param(
    [string]$StackName = "ruralshield-ai",
    [string]$Region = $(if ($env:AWS_REGION) { $env:AWS_REGION } else { "ap-south-1" }),
    [string]$BedrockModelId = $(if ($env:BEDROCK_MODEL_ID) { $env:BEDROCK_MODEL_ID } else { "amazon.nova-lite-v1:0" }),
    [string]$CognitoDomainPrefix = $(if ($env:COGNITO_DOMAIN_PREFIX) { $env:COGNITO_DOMAIN_PREFIX } else { "ruralshield-demo" })
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) { throw "AWS CLI is required" }
if (-not (Get-Command sam -ErrorAction SilentlyContinue)) { throw "AWS SAM CLI is required" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python is required" }

sam build -t infrastructure/template.yaml
sam deploy --stack-name $StackName --region $Region --resolve-s3 --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides "AllowedOrigin=http://localhost:8080" "BedrockModelId=$BedrockModelId" "CognitoDomainPrefix=$CognitoDomainPrefix"

function Get-StackOutput([string]$Key) {
    return aws cloudformation describe-stacks --stack-name $StackName --region $Region --query "Stacks[0].Outputs[?OutputKey=='$Key'].OutputValue | [0]" --output text
}

$ApiUrl = Get-StackOutput "ApiUrl"
$FrontendBucket = Get-StackOutput "FrontendBucketName"
$FrontendUrl = Get-StackOutput "FrontendUrl"
$DistributionId = Get-StackOutput "FrontendDistributionId"
$CognitoClientId = Get-StackOutput "CognitoUserPoolClientId"
$CognitoDomain = Get-StackOutput "CognitoDomain"

sam deploy --stack-name $StackName --region $Region --resolve-s3 --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides "AllowedOrigin=$FrontendUrl" "BedrockModelId=$BedrockModelId" "CognitoDomainPrefix=$CognitoDomainPrefix"

$DeployDir = Join-Path ([System.IO.Path]::GetTempPath()) ("ruralshield-" + [guid]::NewGuid())
try {
    New-Item -ItemType Directory -Path $DeployDir | Out-Null
    $ConfigObject = [ordered]@{
        apiUrl = $ApiUrl
        cognitoDomain = $CognitoDomain
        cognitoClientId = $CognitoClientId
        frontendUrl = $FrontendUrl
    }
    $ConfigJson = $ConfigObject | ConvertTo-Json -Compress
    $Config = "window.RURALSHIELD_CONFIG = $ConfigJson;`n"
    Set-Content -Path (Join-Path $DeployDir "runtime-config.js") -Value $Config -Encoding utf8NoBOM
    aws s3 cp (Join-Path $DeployDir "runtime-config.js") "s3://$FrontendBucket/runtime-config.js" --region $Region
    $FrontendFiles = Get-ChildItem -Path "frontend\*" -File | Where-Object { $_.Name -ne "runtime-config.js" }
    foreach ($File in $FrontendFiles) {
        aws s3 cp $File.FullName "s3://$FrontendBucket/$($File.Name)" --region $Region
    }
    aws cloudfront create-invalidation --distribution-id $DistributionId --paths "/*" | Out-Null
}
finally {
    if (Test-Path $DeployDir) { Remove-Item $DeployDir -Recurse -Force }
}

Write-Host ""
Write-Host "RuralShield AI deployed."
Write-Host "API: $ApiUrl"
Write-Host "Frontend (HTTPS): $FrontendUrl"
Write-Host "Cognito: $CognitoDomain"
