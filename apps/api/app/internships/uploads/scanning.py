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


def _magic_matches(content: bytes, declared_content_type: str, filename: str) -> bool:
    suffix = PurePosixPath(filename).suffix.casefold()
    signatures: dict[str, tuple[bytes, ...]] = {
        ".pdf": (b"%PDF-",),
        ".png": (b"\x89PNG\r\n\x1a\n",),
        ".jpg": (b"\xff\xd8\xff",),
        ".jpeg": (b"\xff\xd8\xff",),
        ".webp": (b"RIFF",),
        ".zip": (b"PK\x03\x04", b"PK\x05\x06"),
        ".ipynb": (b"{",),
        ".json": (b"{", b"["),
        ".md": (),
        ".txt": (),
    }
    expected = signatures.get(suffix)
    if expected is None:
        return False
    if expected and not any(content.startswith(signature) for signature in expected):
        return False
    if declared_content_type == "application/pdf" and not content.startswith(b"%PDF-"):
        return False
    if declared_content_type in {
        "application/zip",
        "application/x-zip-compressed",
    } and not content.startswith(b"PK"):
        return False
    return True


class DemoScanner:
    """Deterministic scanner for explicit local, test, and demo environments."""

    def scan(self, content: bytes, *, declared_content_type: str, filename: str) -> ScanResult:
        if b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in content:
            return ScanResult("REJECTED", "Malware fixture detected")
        if not _magic_matches(content, declared_content_type, filename):
            return ScanResult("REJECTED", "Declared type does not match file signature")
        if filename.casefold().endswith(".zip"):
            try:
                with ZipFile(BytesIO(content)) as archive:
                    members = archive.infolist()
                    if len(members) > 200:
                        return ScanResult("REJECTED", "Archive contains too many entries")
                    if any(".." in PurePosixPath(member.filename).parts for member in members):
                        return ScanResult("REJECTED", "Archive contains a path traversal entry")
                    expanded_size = sum(member.file_size for member in members)
                    if expanded_size > 500 * 1024 * 1024:
                        return ScanResult("REJECTED", "Archive expansion exceeds the scan limit")
            except BadZipFile:
                return ScanResult("REJECTED", "Invalid ZIP archive")
        return ScanResult("CLEAN", "Accepted by the explicit demo scan policy")


class ClamAVScanner:
    """Adapter boundary for a deployed ClamAV worker.

    The callable is injected by the worker process so the API does not need a
    ClamAV client dependency or a network socket in its request path.
    """

    def __init__(self, scan_bytes: Callable[[bytes], tuple[bool, str]]) -> None:
        self._scan_bytes = scan_bytes

    def scan(self, content: bytes, *, declared_content_type: str, filename: str) -> ScanResult:
        del declared_content_type, filename
        clean, message = self._scan_bytes(content)
        return ScanResult("CLEAN" if clean else "REJECTED", message)


class DisabledProductionScanner:
    def scan(self, content: bytes, *, declared_content_type: str, filename: str) -> ScanResult:
        del content, declared_content_type, filename
        return ScanResult(
            "QUARANTINED", "Production scanner is unavailable; upload remains quarantined"
        )
