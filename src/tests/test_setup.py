#!/usr/bin/env python3
import boto3
import json

# LocalStack configuration
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"

BUCKETS = [
    "reviews-input",
    "reviews-preprocessed",
    "reviews-checked",
    "reviews-processed"
]

def test_setup():
    """Test that all components are properly configured."""
    
    # Initialize clients
    lambda_client = boto3.client(
        "lambda",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    s3_client = boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    ssm_client = boto3.client(
        "ssm",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    print("=== Testing Setup ===")
    
    # 1. Check Lambda functions exist
    print("\n1. Checking Lambda functions...")
    try:
        functions = lambda_client.list_functions()
        function_names = [f['FunctionName'] for f in functions['Functions']]
        print(f"Found functions: {function_names}")
        
        required_functions = ['preprocessing', 'profanity_check', 'sentiment_analysis']
        for func in required_functions:
            if func in function_names:
                print(f"✓ {func} function exists")
            else:
                print(f"✗ {func} function missing")
    except Exception as e:
        print(f"Error checking Lambda functions: {e}")
    
    # 2. Check S3 buckets exist
    print("\n2. Checking S3 buckets...")
    try:
        buckets = s3_client.list_buckets()
        bucket_names = [b['Name'] for b in buckets['Buckets']]
        print(f"Found buckets: {bucket_names}")
        
        for bucket in BUCKETS:
            if bucket in bucket_names:
                print(f"✓ {bucket} bucket exists")
            else:
                print(f"✗ {bucket} bucket missing")
    except Exception as e:
        print(f"Error checking S3 buckets: {e}")
    
    # 3. Check S3 notifications
    print("\n3. Checking S3 notifications...")
    for bucket in BUCKETS[:-1]:  # Only check notifications for input, preprocessed, checked
        try:
            notifications = s3_client.get_bucket_notification_configuration(Bucket=bucket)
            if 'LambdaFunctionConfigurations' in notifications:
                print(f"✓ {bucket} has Lambda notifications:")
                for config in notifications['LambdaFunctionConfigurations']:
                    print(f"  - {config['LambdaFunctionArn']}")
            else:
                print(f"✗ {bucket} missing Lambda notifications")
        except Exception as e:
            print(f"Error checking notifications for {bucket}: {e}")
    
    # 4. Check SSM parameters
    print("\n4. Checking SSM parameters...")
    try:
        required_params = [
            "/dic2025/a3/bucket/input",
            "/dic2025/a3/bucket/processed",
            "/dic2025/a3/table/review_metadata",
            "/dic2025/a3/table/customer_stats"
        ]
        
        for param in required_params:
            try:
                response = ssm_client.get_parameter(Name=param)
                print(f"✓ {param} = {response['Parameter']['Value']}")
            except Exception as e:
                print(f"✗ {param} missing: {e}")
    except Exception as e:
        print(f"Error checking SSM parameters: {e}")
    
    # 5. Test Lambda function invocation
    print("\n5. Testing Lambda function invocation...")
    try:
        # Test preprocessing function
        test_event = {
            "Records": [
                {
                    "s3": {
                        "object": {
                            "key": "test.json"
                        }
                    }
                }
            ]
        }
        
        response = lambda_client.invoke(
            FunctionName='preprocessing',
            Payload=json.dumps(test_event)
        )
        print(f"✓ Preprocessing function invoked (status: {response['StatusCode']})")
    except Exception as e:
        print(f"✗ Error invoking preprocessing function: {e}")

if __name__ == "__main__":
    test_setup() 