import re
from pathlib import Path


def test_grype_exceptions_are_exact_and_expiring() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    config = (repository_root / ".grype.yaml").read_text(encoding="utf-8")
    documentation = (repository_root / "docs" / "security-vulnerability-exceptions.md").read_text(
        encoding="utf-8"
    )

    expected_config = """ignore:
  - vulnerability: CVE-2026-11940
    package:
      name: python
      type: binary
  - vulnerability: CVE-2026-11972
    package:
      name: python
      type: binary
  - vulnerability: CVE-2026-15308
    package:
      name: python
      type: binary
"""

    assert config == expected_config
    assert "2026-09-15" in documentation
    assert "stable Python" in documentation
    assert "verify its advisories and rescan" in documentation


def test_api_image_uses_the_audited_python_runtime() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    dockerfile = (repository_root / "apps" / "api" / "Dockerfile").read_text(encoding="utf-8")

    assert dockerfile.startswith("FROM python:3.13.14-alpine3.24")
    assert "UV_PYTHON_DOWNLOADS=never" in dockerfile


def test_web_image_uses_the_audited_node_runtime() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    dockerfile = (repository_root / "apps" / "web" / "Dockerfile").read_text(encoding="utf-8")

    assert dockerfile.count("FROM node:22.23.2-alpine3.24") == 2
    assert "trixie" not in dockerfile


def test_ci_container_scans_use_the_audited_policy_and_scanner() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    workflow = (repository_root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert workflow.count("config: .grype.yaml") == 2
    assert workflow.count("grype-version: 0.116.1") == 2
    assert workflow.count("severity-cutoff: high") == 2
    assert workflow.count("by-cve: true") == 2


def test_ci_preserves_attestation_and_exact_digest_scan_evidence() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    workflow = (repository_root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "driver-opts: network=host" in workflow
    assert '[registry."localhost:5000"]' in workflow
    assert "http = true" in workflow
    assert "registry:2.8.3@sha256:" in workflow
    assert workflow.count("--metadata-file") == 2
    assert workflow.count("--provenance=mode=max") == 2
    assert workflow.count("--sbom=true") == 2
    assert "docker:${{ env.API_CI_IMAGE }}" in workflow
    assert "docker:${{ env.WEB_CI_IMAGE }}" in workflow
    assert "api-provenance.json" in workflow
    assert "api-sbom.spdx.json" in workflow
    assert "web-provenance.json" in workflow
    assert "web-sbom.spdx.json" in workflow
    assert workflow.count("output-format: json") == 2
    assert workflow.count("output-file:") == 2
    assert (
        "ci-container-evidence-${{ github.sha }}-${{ github.run_id }}-${{ github.run_attempt }}"
        in workflow
    )
    assert "terraform -chdir=infra/bootstrap fmt -check" in workflow
    assert "terraform -chdir=infra/bootstrap init -backend=false -input=false" in workflow
    assert "terraform -chdir=infra/bootstrap validate" in workflow


def test_manual_release_uses_wif_and_promotes_the_built_digests() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    workflow = (repository_root / ".github" / "workflows" / "release-images.yml").read_text(
        encoding="utf-8"
    )

    assert "workflow_dispatch:" in workflow
    assert "contents: read\n  id-token: write" in workflow
    assert "credentials_json" not in workflow
    assert "create_credentials_file: false" in workflow
    assert "export_environment_variables: false" in workflow
    assert workflow.count("docker/build-push-action@") == 2
    assert workflow.count("provenance: mode=max") == 2
    assert workflow.count("sbom: true") == 2
    assert workflow.count("${{ github.sha }}-${{ github.run_id }}-${{ github.run_attempt }}") >= 4
    assert "NEXT_PUBLIC_DEMO_MODE=false" in workflow
    assert "registry:${{ steps.release-images.outputs.api_image }}" in workflow
    assert "registry:${{ steps.release-images.outputs.web_image }}" in workflow
    assert "terraform-images.tfvars" in workflow
    assert 'api_image = "%s"' in workflow
    assert 'web_image = "%s"' in workflow
    assert (
        "release-${{ inputs.environment }}-${{ github.sha }}-${{ github.run_id }}-"
        "${{ github.run_attempt }}" in workflow
    )
    assert "Production releases may only be dispatched from the main branch." in workflow

    for variable_name in (
        "ARTIFACT_REPOSITORY",
        "GCP_PROJECT_ID",
        "GCP_REGION",
        "GCP_RELEASE_SERVICE_ACCOUNT",
        "GCP_WORKLOAD_IDENTITY_PROVIDER",
        "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
        "NEXT_PUBLIC_SUPABASE_URL",
    ):
        assert variable_name in workflow


def test_bootstrap_provisions_scoped_keyless_release_identity() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    bootstrap = (repository_root / "infra" / "bootstrap" / "main.tf").read_text(encoding="utf-8")
    outputs = (repository_root / "infra" / "bootstrap" / "outputs.tf").read_text(encoding="utf-8")

    assert '"iamcredentials.googleapis.com"' in bootstrap
    assert '"sts.googleapis.com"' in bootstrap
    assert 'resource "google_iam_workload_identity_pool" "github_release"' in bootstrap
    assert 'resource "google_iam_workload_identity_pool_provider" "github_release"' in bootstrap
    assert '"attribute.repository"' in bootstrap
    assert '"attribute.environment"' in bootstrap
    assert '"attribute.repository_id"' in bootstrap
    assert '"attribute.repository_owner_id"' in bootstrap
    assert '"attribute.workflow_ref"' in bootstrap
    assert "assertion.repository == '${var.github_repository}'" in bootstrap
    assert "assertion.repository_id == '${var.github_repository_id}'" in bootstrap
    assert "assertion.repository_owner_id == '${var.github_repository_owner_id}'" in bootstrap
    release_workflow = "${var.github_repository}/.github/workflows/release-images.yml@"
    assert f"assertion.workflow_ref == '{release_workflow}refs/heads/main'" in bootstrap
    assert f"assertion.workflow_ref.startsWith('{release_workflow}')" in bootstrap
    assert "assertion.environment == 'production'" in bootstrap
    assert "assertion.ref == 'refs/heads/main'" in bootstrap
    assert "assertion.environment == 'staging'" in bootstrap
    assert 'role               = "roles/iam.workloadIdentityUser"' in bootstrap
    assert "/attribute.repository_id/%s" in bootstrap
    assert 'role       = "roles/artifactregistry.writer"' in bootstrap
    assert "roles/owner" not in bootstrap
    assert "roles/editor" not in bootstrap
    assert "immutable_tags = true" in bootstrap
    assert bootstrap.count("prevent_destroy = true") == 2
    assert 'output "artifact_registry_repository_id"' in outputs
    assert 'output "github_workload_identity_provider"' in outputs
    assert 'output "release_service_account"' in outputs


def test_all_workflow_actions_are_pinned_to_full_object_ids() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    workflow_directory = repository_root / ".github" / "workflows"

    for workflow_path in workflow_directory.glob("*.yml"):
        workflow = workflow_path.read_text(encoding="utf-8")
        actions = re.findall(r"^\s*(?:-\s*)?uses:\s*(\S+)", workflow, flags=re.MULTILINE)
        assert actions, f"No actions found in {workflow_path.name}"
        for action in actions:
            if action.startswith("./"):
                continue
            assert "@" in action, f"Unpinned action in {workflow_path.name}: {action}"
            reference = action.rsplit("@", maxsplit=1)[1]
            assert re.fullmatch(r"[0-9a-f]{40}", reference), (
                f"Action is not pinned to a full object ID in {workflow_path.name}: {action}"
            )


def test_local_release_script_is_fail_closed_and_non_authoritative() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    script = (repository_root / "scripts" / "build_and_push.ps1").read_text(encoding="utf-8")
    normalized_script = script.lower()

    assert "non-authoritative" in normalized_script
    assert "throw" in normalized_script
    assert "docker build" not in normalized_script
    assert "docker push" not in normalized_script
    assert "git rev-parse" not in normalized_script


def test_google_auth_credential_files_are_excluded_from_git_and_build_context() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    gitignore = (repository_root / ".gitignore").read_text(encoding="utf-8")
    dockerignore = (repository_root / ".dockerignore").read_text(encoding="utf-8")

    assert "gha-creds-*.json" in gitignore.splitlines()
    assert "gha-creds-*.json" in dockerignore.splitlines()


def test_gitleaks_ignore_contains_only_reviewed_test_fixture_findings() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    ignored_findings = (repository_root / ".gitleaksignore").read_text(encoding="utf-8")

    assert ignored_findings.splitlines() == [
        "08c05b805ec39291ccc7e30df6850e127bd5c583:"
        "apps/api/tests/test_release_internship_scoping.py:generic-api-key:280",
        "08c05b805ec39291ccc7e30df6850e127bd5c583:"
        "apps/api/tests/test_release_internship_scoping.py:generic-api-key:290",
    ]
