import os
import boto3

endpoint_url = "http://localhost:4566" if os.getenv("STAGE") == "local" else None
ssm = boto3.client("ssm", endpoint_url=endpoint_url)

def get_param(name):
    """Fetch a parameter value from SSM Parameter Store."""
    return ssm.get_parameter(Name=name)["Parameter"]["Value"] 