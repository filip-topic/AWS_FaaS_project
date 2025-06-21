#!/usr/bin/env python3
import boto3
import subprocess
import os

# LocalStack configuration
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"

def deploy_lambdas():
    """Deploy Lambda functions using boto3."""
    
    lambda_client = boto3.client(
        "lambda",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    lambda_configs = [
        {
            "name": "preprocessing",
            "zip_file": "src/lambdas/preprocessing/lambda.zip"
        },
        {
            "name": "profanity_check", 
            "zip_file": "src/lambdas/profanity_check/lambda.zip"
        },
        {
            "name": "sentiment_analysis",
            "zip_file": "src/lambdas/sentiment_analysis/lambda.zip"
        }
    ]
    
    print("=== Deploying Lambda Functions ===")
    
    for config in lambda_configs:
        name = config["name"]
        zip_file = config["zip_file"]
        
        print(f"Deploying {name}...")
        
        # Delete existing function if it exists
        try:
            lambda_client.delete_function(FunctionName=name)
            print(f"  ✓ Deleted existing function: {name}")
        except:
            pass
        
        # Read zip file
        with open(zip_file, 'rb') as f:
            zip_content = f.read()
        
        # Create function
        try:
            response = lambda_client.create_function(
                FunctionName=name,
                Runtime='python3.11',
                Handler='handler.handler',
                Role='arn:aws:iam::000000000000:role/lambda-role',
                Code={'ZipFile': zip_content},
                Timeout=30,
                Environment={
                    'Variables': {
                        'STAGE': 'local'
                    }
                }
            )
            print(f"  ✓ Created function: {name}")
        except Exception as e:
            print(f"  ✗ Error creating function {name}: {e}")
    
    print("=== Lambda deployment complete ===")

if __name__ == "__main__":
    deploy_lambdas() 