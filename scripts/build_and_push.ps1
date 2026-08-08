# PowerShell script to build, tag with Git SHA, push to Artifact Registry, and output image digests

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,
    [string]$Region = "us-central1",
    [string]$Repository = "",
    [ValidateSet("staging", "production")]
    [string]$Env = "staging",
    [Parameter(Mandatory = $true)]
    [string]$FirebaseApiKey,
    [Parameter(Mandatory = $true)]
    [string]$FirebaseAuthDomain,
    [Parameter(Mandatory = $true)]
    [string]$FirebaseProjectId,
    [Parameter(Mandatory = $true)]
    [string]$FirebaseStorageBucket,
    [Parameter(Mandatory = $true)]
    [string]$FirebaseMessagingSenderId,
    [Parameter(Mandatory = $true)]
    [string]$FirebaseAppId
)

$ErrorActionPreference = "Stop"

Write-Host "Checking Git commit SHA..." -ForegroundColor Cyan
$gitSha = (git rev-parse --short HEAD).Trim()
if (-not $gitSha) {
    $gitSha = "latest"
}

if (-not $Repository) {
    $Repository = "praxisai-$Env-praxisai"
}

$arHost = "$Region-docker.pkg.dev"
$apiImageName = "$arHost/$ProjectId/$Repository/api:$gitSha"
$webImageName = "$arHost/$ProjectId/$Repository/web:$gitSha"

Write-Host "Building API image: $apiImageName" -ForegroundColor Cyan
docker build -t $apiImageName -f apps/api/Dockerfile apps/api

Write-Host "Building Web image: $webImageName" -ForegroundColor Cyan
docker build -t $webImageName -f apps/web/Dockerfile `
    --build-arg "NEXT_PUBLIC_FIREBASE_API_KEY=$FirebaseApiKey" `
    --build-arg "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=$FirebaseAuthDomain" `
    --build-arg "NEXT_PUBLIC_FIREBASE_PROJECT_ID=$FirebaseProjectId" `
    --build-arg "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=$FirebaseStorageBucket" `
    --build-arg "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=$FirebaseMessagingSenderId" `
    --build-arg "NEXT_PUBLIC_FIREBASE_APP_ID=$FirebaseAppId" `
    --build-arg "NEXT_PUBLIC_APP_ENV=$Env" `
    --build-arg "NEXT_PUBLIC_DEMO_MODE=false" .

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
