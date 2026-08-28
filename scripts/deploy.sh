#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${1:-ruralshield-ai}"
REGION="${AWS_REGION:-ap-south-1}"
BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-amazon.nova-lite-v1:0}"

command -v aws >/dev/null || { echo "AWS CLI is required" >&2; exit 1; }
command -v sam >/dev/null || { echo "AWS SAM CLI is required" >&2; exit 1; }

sam build -t infrastructure/template.yaml
sam deploy --stack-name "$STACK_NAME" --region "$REGION" --resolve-s3 --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides AllowedOrigin=http://localhost:8080 BedrockModelId="$BEDROCK_MODEL_ID"

stack_output() {
  aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue | [0]" --output text
}

API_URL="$(stack_output ApiUrl)"
FRONTEND_BUCKET="$(stack_output FrontendBucketName)"
FRONTEND_URL="$(stack_output FrontendUrl)"
DISTRIBUTION_ID="$(stack_output FrontendDistributionId)"

# Tighten API CORS to the HTTPS CloudFront origin after its generated domain is known.
sam deploy --stack-name "$STACK_NAME" --region "$REGION" --resolve-s3 --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides AllowedOrigin="$FRONTEND_URL" BedrockModelId="$BEDROCK_MODEL_ID"

DEPLOY_DIR="$(mktemp -d)"
trap 'rm -rf "$DEPLOY_DIR"' EXIT
cp -R frontend/. "$DEPLOY_DIR/"
python - "$API_URL" "$DEPLOY_DIR/runtime-config.js" <<'PY'
import json
import pathlib
import sys
api_url, output = sys.argv[1:]
pathlib.Path(output).write_text("window.RURALSHIELD_API_URL = " + json.dumps(api_url) + ";\n", encoding="utf-8")
PY

aws s3 sync "$DEPLOY_DIR/" "s3://$FRONTEND_BUCKET/" --delete --region "$REGION"
aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths '/*' >/dev/null

printf '\nRuralShield AI deployed.\nAPI: %s\nFrontend (HTTPS): %s\n' "$API_URL" "$FRONTEND_URL"
