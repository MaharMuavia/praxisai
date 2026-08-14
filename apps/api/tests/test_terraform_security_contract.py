from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
TERRAFORM_ROOT = REPOSITORY_ROOT / "infra" / "terraform"


def _terraform_block(source: str, declaration: str) -> str:
    start = source.index(declaration)
    opening_brace = source.index("{", start)
    depth = 0
    for index in range(opening_brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"Unterminated Terraform block: {declaration}")


def test_runtime_secrets_are_pinned_and_retained_for_rotation() -> None:
    main = (TERRAFORM_ROOT / "main.tf").read_text(encoding="utf-8")
    variables = (TERRAFORM_ROOT / "variables.tf").read_text(encoding="utf-8")

    assert 'version = "latest"' not in main
    for variable_name in (
        "database_url_secret_version",
        "supabase_url_secret_version",
        "supabase_service_role_key_secret_version",
        "session_secret_version",
        "session_secret_fallback_version",
    ):
        assert f'variable "{variable_name}"' in variables
        assert f"version = var.{variable_name}" in main

    assert 'name = "SESSION_SECRET_FALLBACK"' in main
    for secret_name in (
        "database_url",
        "database_migration_url",
        "supabase_url",
        "supabase_service_role_key",
        "session_secret",
    ):
        secret = _terraform_block(
            main,
            f'resource "google_secret_manager_secret" "{secret_name}"',
        )
        assert "prevent_destroy = true" in secret


def test_artifact_bucket_is_protected_from_destroy() -> None:
    main = (TERRAFORM_ROOT / "main.tf").read_text(encoding="utf-8")
    artifact_bucket = _terraform_block(
        main,
        'resource "google_storage_bucket" "artifacts"',
    )

    assert "prevent_destroy = true" in artifact_bucket


def test_worker_network_contract_is_private_and_environment_scoped() -> None:
    main = (TERRAFORM_ROOT / "main.tf").read_text(encoding="utf-8")
    variables = (TERRAFORM_ROOT / "variables.tf").read_text(encoding="utf-8")

    assert 'egress = "PRIVATE_RANGES_ONLY"' in main
    assert 'tags       = ["${local.prefix}-worker"]' in main
    assert 'cidrhost("${var.clamav_host}/32", 0) == var.clamav_host' in variables
    for private_range in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"):
        assert f'cidrcontains("{private_range}", var.clamav_host)' in variables


def test_alerts_are_scoped_to_the_deployed_project_and_region() -> None:
    main = (TERRAFORM_ROOT / "main.tf").read_text(encoding="utf-8")
    alert_filters = [
        line.strip()
        for line in main.splitlines()
        if "filter" in line and "run.googleapis.com/" in line
    ]

    assert len(alert_filters) == 4
    for alert_filter in alert_filters:
        assert 'resource.labels.project_id = \\"${var.project_id}\\"' in alert_filter
        assert 'resource.labels.location = \\"${var.region}\\"' in alert_filter


def test_removed_managed_services_are_not_provisioned() -> None:
    terraform = "\n".join(
        path.read_text(encoding="utf-8") for path in TERRAFORM_ROOT.glob("*.tf")
    ).casefold()

    assert "cloudtasks.googleapis.com" not in terraform
    assert "google_cloud_tasks" not in terraform
    assert "bigquery.googleapis.com" not in terraform
    assert "google_bigquery" not in terraform
