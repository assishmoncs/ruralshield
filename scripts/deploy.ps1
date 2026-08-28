param(
    [string]$StackName = "ruralshield-ai",
    [string]$Region = $(if ($env:AWS_REGION) { $env:AWS_REGION } else { "ap-south-1" }),
    [string]$BedrockModelId = $(if ($env:BEDROCK_MODEL_ID) { $env:BEDROCK_MODEL_ID } else { "amazon.nova-lite-v1:0" })
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) { throw "AWS CLI is required" }
if (-not (Get-Command sam -ErrorAction SilentlyContinue)) { throw "AWS SAM CLI is required" }

sam build -t infrastructure/template.yaml
sam deploy --stack-name $StackName --region $Region --resolve-s3 --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides "AllowedOrigin=http://localhost:8080" "BedrockModelId=$BedrockModelId"

function Get-StackOutput([string]$Key) {
    return aws cloudformation describe-stacks --stack-name $StackName --region $Region --query "Stacks[0].Outputs[?OutputKey=='$Key'].OutputValue | [0]" --output text
}

$ApiUrl = Get-StackOutput "ApiUrl"
$FrontendBucket = Get-StackOutput "FrontendBucketName"
$FrontendUrl = Get-StackOutput "FrontendUrl"
$DistributionId = Get-StackOutput "FrontendDistributionId"

sam deploy --stack-name $StackName --region $Region --resolve-s3 --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides "AllowedOrigin=$FrontendUrl" "BedrockModelId=$BedrockModelId"

$DeployDir = Join-Path ([System.IO.Path]::GetTempPath()) ("ruralshield-" + [guid]::NewGuid())
try {
    New-Item -ItemType Directory -Path $DeployDir | Out-Null
    Copy-Item -Path "frontend\*" -Destination $DeployDir -Recurse
    $Config = "window.RURALSHIELD_API_URL = " + ($ApiUrl | ConvertTo-Json -Compress) + ";`n"
    Set-Content -Path (Join-Path $DeployDir "runtime-config.js") -Value $Config -Encoding utf8NoBOM
    aws s3 sync "$DeployDir\" "s3://$FrontendBucket/" --delete --region $Region
    aws cloudfront create-invalidation --distribution-id $DistributionId --paths "/*" | Out-Null
}
finally {
    if (Test-Path $DeployDir) { Remove-Item $DeployDir -Recurse -Force }
}

Write-Host ""
Write-Host "RuralShield AI deployed."
Write-Host "API: $ApiUrl"
Write-Host "Frontend (HTTPS): $FrontendUrl"
