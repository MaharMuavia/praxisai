# NON-AUTHORITATIVE: local release publication is intentionally disabled.

[CmdletBinding()]
param(
    [string]$ProjectId,
    [string]$Region = "us-central1",
    [string]$Repository,
    [ValidateSet("staging", "production")]
    [string]$Env = "staging",
    [string]$SupabaseUrl,
    [string]$SupabasePublishableKey
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

throw @"
This script is non-authoritative and cannot build or push release images.
Run the pinned "Release container images" GitHub Actions workflow instead. It uses
Google Workload Identity Federation, builds each image once, publishes SBOM and
provenance attestations, scans the exact registry digests, and emits reviewed
Terraform image values. Local Docker credentials and local worktrees are not an
approved release source.
"@
