import os
import boto3

# Use LocalStack endpoint for Lambda functions
# When running inside LocalStack Lambda containers, use the internal endpoint
if os.getenv("STAGE") == "local":
    endpoint_url = "http://host.docker.internal:4566"  # Internal LocalStack endpoint
else:
    endpoint_url = None

ssm = boto3.client("ssm", endpoint_url=endpoint_url)

def get_param(name):
    """Fetch a parameter value from SSM Parameter Store."""
    try:
        return ssm.get_parameter(Name=name)["Parameter"]["Value"]
    except Exception as e:
        print(f"Error getting SSM parameter {name}: {e}")
        # Return default values for testing
        if "input" in name:
            return "reviews-input"
        elif "processed" in name:
            return "reviews-processed"
        elif "review_metadata" in name:
            return "review-metadata"
        elif "customer_stats" in name:
            return "customer-stats"
        else:
            raise e 