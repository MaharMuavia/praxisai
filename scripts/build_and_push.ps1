# PowerShell script to build, tag with Git SHA, push to Artifact Registry, and output image digests

param(
    [string]$ProjectId = "<PROJECT_ID>",
    [string]$Region = "<REGION>",
    [string]$Repository = "praxisai-staging-praxisai",
    [string]$Env = "staging"
)

$ErrorActionPreference = "Stop"

Write-Host "Checking Git commit SHA..." -ForegroundColor Cyan
$gitSha = (git rev-parse --short HEAD).Trim()
if (-not $gitSha) {
    $gitSha = "latest"
}

$arHost = "$Region-docker.pkg.dev"
$apiImageName = "$arHost/$ProjectId/$Repository/api:$gitSha"
$webImageName = "$arHost/$ProjectId/$Repository/web:$gitSha"

Write-Host "Building API image: $apiImageName" -ForegroundColor Cyan
docker build -t $apiImageName -f apps/api/Dockerfile apps/api

Write-Host "Building Web image: $webImageName" -ForegroundColor Cyan
docker build -t $webImageName -f apps/web/Dockerfile apps/web

Write-Host "Pushing API image..." -ForegroundColor Cyan
docker push $apiImageName

Write-Host "Pushing Web image..." -ForegroundColor Cyan
docker push $webImageName

Write-Host "Inspecting Image Digests..." -ForegroundColor Cyan
$apiDigest = (docker inspect --format='{{index .RepoDigests 0}}' $apiImageName)
$webDigest = (docker inspect --format='{{index .RepoDigests 0}}' $webImageName)

Write-Host "=== Image Digest Summary ===" -ForegroundColor Green
Write-Host "API Digest: $apiDigest"
Write-Host "Web Digest: $webDigest"

Write-Host "`nTo use immutable digests in Terraform (tfvars):" -ForegroundColor Yellow
Write-Host "api_image = `"$apiDigest`""
Write-Host "web_image = `"$webDigest`""
