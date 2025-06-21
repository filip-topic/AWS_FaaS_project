import pytest
import boto3
import os

@pytest.fixture(scope="session")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture(scope="session")
def localstack_endpoint():
    """LocalStack endpoint URL."""
    return "http://localhost:4566"

@pytest.fixture(scope="session")
def s3_client(localstack_endpoint):
    """S3 client configured for LocalStack."""
    return boto3.client("s3", endpoint_url=localstack_endpoint)

@pytest.fixture(scope="session")
def ddb_client(localstack_endpoint):
    """DynamoDB client configured for LocalStack."""
    return boto3.client("dynamodb", endpoint_url=localstack_endpoint)

@pytest.fixture(scope="session")
def ssm_client(localstack_endpoint):
    """SSM client configured for LocalStack."""
    return boto3.client("ssm", endpoint_url=localstack_endpoint)

@pytest.fixture(scope="session")
def lambda_client(localstack_endpoint):
    """Lambda client configured for LocalStack."""
    return boto3.client("lambda", endpoint_url=localstack_endpoint) 