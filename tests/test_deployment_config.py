"""Deployment configuration checks for the supported Bedrock inference profile."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_ID = "apac.amazon.nova-lite-v1:0"
REGIONS = (
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-northeast-3",
    "ap-south-1",
    "ap-southeast-1",
    "ap-southeast-2",
)


def test_bedrock_deployment_defaults_match_supported_profile():
    template = (ROOT / "infrastructure" / "template.yaml").read_text(encoding="utf-8")
    powershell = (ROOT / "scripts" / "deploy.ps1").read_text(encoding="utf-8")
    shell = (ROOT / "scripts" / "deploy.sh").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert f"Default: {PROFILE_ID}" in template
    assert f'"{PROFILE_ID}"' in powershell
    assert f"BEDROCK_MODEL_ID:-{PROFILE_ID}" in shell
    assert PROFILE_ID in readme
    assert "amazon.nova-lite-v1:0" not in powershell.replace(PROFILE_ID, "")
    assert "BEDROCK_MODEL_ID:-amazon.nova-lite-v1:0" not in shell



def test_lambda_dependencies_match_local_project_dependencies():
    local_requirements = (ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8").splitlines()
    lambda_requirements = (ROOT / "backend" / "lambda" / "requirements.txt").read_text(encoding="utf-8").splitlines()

    assert local_requirements == lambda_requirements
    assert "boto3>=1.40,<2" in lambda_requirements

def test_bedrock_iam_allows_profile_and_its_apac_model_regions():
    template = (ROOT / "infrastructure" / "template.yaml").read_text(encoding="utf-8")

    assert "inference-profile/${BedrockModelId}" in template
    assert "bedrock:InferenceProfileArn" in template
    assert "AllowedValues:" in template
    for region in REGIONS:
        expected = f"bedrock:{region}::foundation-model/amazon.nova-lite-v1:0"
        assert expected in template
