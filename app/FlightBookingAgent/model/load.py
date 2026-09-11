from strands.models.bedrock import BedrockModel

# Claude Sonnet 4.6 - Application inference profile for
model_arn="arn:aws:bedrock:us-east-1:742752463290:application-inference-profile/wtv4phtvp7i1"

def load_model() -> BedrockModel:
    """Get Bedrock model client using IAM credentials."""
    return BedrockModel(model_id=model_arn)
