import json
import socket
import struct
from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from typing import Protocol
from zipfile import BadZipFile, ZipFile


@dataclass(frozen=True)
class ScanResult:
    state: str
    message: str


class UploadScanner(Protocol):
    def scan(self, content: bytes, *, declared_content_type: str, filename: str) -> ScanResult: ...


CONTENT_TYPES_BY_SUFFIX: dict[str, frozenset[str]] = {
    ".pdf": frozenset({"application/pdf"}),
    ".png": frozenset({"image/png"}),
    ".jpg": frozenset({"image/jpeg"}),
    ".jpeg": frozenset({"image/jpeg"}),
    ".webp": frozenset({"image/webp"}),
    ".zip": frozenset({"application/zip", "application/x-zip-compressed"}),
    ".ipynb": frozenset({"application/json"}),
    ".json": frozenset({"application/json"}),
    ".md": frozenset({"text/markdown", "text/plain"}),
    ".txt": frozenset({"text/plain"}),
}


def content_type_matches_filename(declared_content_type: str, filename: str) -> bool:
    suffix = PurePosixPath(filename).suffix.casefold()
    normalized_type = declared_content_type.partition(";")[0].strip().casefold()
    return normalized_type in CONTENT_TYPES_BY_SUFFIX.get(suffix, frozenset())


def _magic_matches(content: bytes, declared_content_type: str, filename: str) -> bool:
    suffix = PurePosixPath(filename).suffix.casefold()
    if not content_type_matches_filename(declared_content_type, filename):
        return False
    signatures: dict[str, tuple[bytes, ...]] = {
        ".pdf": (b"%PDF-",),
        ".png": (b"\x89PNG\r\n\x1a\n",),
        ".jpg": (b"\xff\xd8\xff",),
        ".jpeg": (b"\xff\xd8\xff",),
        ".webp": (),
        ".zip": (b"PK\x03\x04", b"PK\x05\x06"),
        ".ipynb": (b"{",),
        ".json": (b"{", b"["),
        ".md": (),
        ".txt": (),
    }
    expected = signatures.get(suffix)
    if expected is None:
        return False
    if suffix == ".webp" and not (
        len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    ):
        return False
    if expected and not any(content.startswith(signature) for signature in expected):
        return False
    return True


def deterministic_upload_scan(
    content: bytes, *, declared_content_type: str, filename: str
) -> ScanResult:
    """Apply provider-independent content and archive safety checks."""
    if not _magic_matches(content, declared_content_type, filename):
        return ScanResult("REJECTED", "Declared type does not match file signature")
    suffix = PurePosixPath(filename).suffix.casefold()
    if suffix in {".txt", ".md"}:
        try:
            content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ScanResult("REJECTED", "Text artifact is not valid UTF-8")
        if b"\x00" in content:
            return ScanResult("REJECTED", "Text artifact contains binary null bytes")
    if suffix in {".json", ".ipynb"}:
        try:
            json.loads(content.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return ScanResult("REJECTED", "JSON artifact is malformed")
    if filename.casefold().endswith(".zip"):
        try:
            with ZipFile(BytesIO(content)) as archive:
                members = archive.infolist()
                if len(members) > 200:
                    return ScanResult("REJECTED", "Archive contains too many entries")
                for member in members:
                    member_path = PurePosixPath(member.filename.replace("\\", "/"))
                    unix_mode = member.external_attr >> 16
                    if (
                        member_path.is_absolute()
                        or ".." in member_path.parts
                        or (member_path.parts and member_path.parts[0].endswith(":"))
                    ):
                        return ScanResult("REJECTED", "Archive contains a path traversal entry")
                    if unix_mode & 0o170000 == 0o120000:
                        return ScanResult("REJECTED", "Archive contains a symbolic link")
                    if member.flag_bits & 0x1:
                        return ScanResult("REJECTED", "Encrypted archives are not accepted")
                expanded_size = sum(member.file_size for member in members)
                if expanded_size > 500 * 1024 * 1024:
                    return ScanResult("REJECTED", "Archive expansion exceeds the scan limit")
        except BadZipFile:
            return ScanResult("REJECTED", "Invalid ZIP archive")
    return ScanResult("CLEAN", "Passed deterministic upload safety checks")


class DemoScanner:
    """Deterministic scanner for explicit local, test, and demo environments."""

    def scan(self, content: bytes, *, declared_content_type: str, filename: str) -> ScanResult:
        if b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in content:
            return ScanResult("REJECTED", "Malware fixture detected")
        deterministic = deterministic_upload_scan(
            content,
            declared_content_type=declared_content_type,
            filename=filename,
        )
        if deterministic.state != "CLEAN":
            return deterministic
        return ScanResult("CLEAN", "Accepted by the explicit demo scan policy")


class ClamAVScanner:
    """Adapter boundary for a deployed ClamAV worker.

    The callable is injected by the worker process so the API does not need a
    ClamAV client dependency or a network socket in its request path.
    """

    def __init__(self, scan_bytes: Callable[[bytes], tuple[bool, str]]) -> None:
        self._scan_bytes = scan_bytes

    def scan(self, content: bytes, *, declared_content_type: str, filename: str) -> ScanResult:
        deterministic = deterministic_upload_scan(
            content,
            declared_content_type=declared_content_type,
            filename=filename,
        )
        if deterministic.state != "CLEAN":
            return deterministic
        clean, message = self._scan_bytes(content)
        return ScanResult("CLEAN" if clean else "REJECTED", message)


def scan_with_clamav(
    content: bytes,
    *,
    host: str,
    port: int,
    timeout_seconds: float,
) -> tuple[bool, str]:
    """Scan bytes through ClamAV's bounded INSTREAM protocol."""
    with socket.create_connection((host, port), timeout=timeout_seconds) as connection:
        connection.settimeout(timeout_seconds)
        connection.sendall(b"zINSTREAM\0")
        for offset in range(0, len(content), 1024 * 1024):
            chunk = content[offset : offset + 1024 * 1024]
            connection.sendall(struct.pack(">I", len(chunk)))
            connection.sendall(chunk)
        connection.sendall(struct.pack(">I", 0))
        response = connection.recv(4096).decode("utf-8", errors="replace").strip()
    if response.endswith("FOUND") or "FOUND" in response:
        return False, response
    if not response.endswith("OK"):
        raise RuntimeError(f"ClamAV returned an unexpected response: {response[:300]}")
    return True, response


class DisabledProductionScanner:
    def scan(self, content: bytes, *, declared_content_type: str, filename: str) -> ScanResult:
        del content, declared_content_type, filename
        return ScanResult(
            "QUARANTINED", "Production scanner is unavailable; upload remains quarantined"
        )
