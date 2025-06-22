#!/usr/bin/env python3
import boto3
import json
import uuid

ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"

def debug_sentiment_lambda():
    """Debug the sentiment analysis Lambda function."""
    
    s3 = boto3.client("s3", endpoint_url=ENDPOINT_URL, region_name=REGION,
                      aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    lambda_client = boto3.client("lambda", endpoint_url=ENDPOINT_URL, region_name=REGION,
                                 aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    
    print("=== Debugging Sentiment Analysis Lambda ===")
    
    # Create a test file in reviews-checked
    test_key = f"debug_test_{uuid.uuid4()}.json"
    test_review = {
        "customerId": "debug_customer",
        "reviewId": "debug_review",
        "summary": "Test summary",
        "reviewText": "I love this product!",
        "overall": 5
    }
    
    print(f"1. Creating test file in reviews-checked: {test_key}")
    try:
        s3.put_object(
            Bucket="reviews-checked",
            Key=test_key,
            Body=json.dumps(test_review).encode('utf-8'),
            ContentType="application/json"
        )
        print("✓ Test file created in reviews-checked")
    except Exception as e:
        print(f"✗ Error creating test file: {e}")
        return
    
    # Invoke sentiment analysis Lambda
    print(f"2. Invoking sentiment_analysis Lambda...")
    event = {
        "Records": [
            {
                "s3": {
                    "object": {
                        "key": test_key
                    }
                }
            }
        ]
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName="sentiment_analysis",
            Payload=json.dumps(event)
        )
        print(f"✓ Lambda invoked (status: {response['StatusCode']})")
        
        # Check response payload
        if 'Payload' in response:
            payload = json.loads(response['Payload'].read())
            print(f"Lambda response: {payload}")
            
            if 'errorMessage' in payload:
                print(f"✗ Lambda error: {payload['errorMessage']}")
                return
    except Exception as e:
        print(f"✗ Error invoking Lambda: {e}")
        return
    
    # Check if file was created in reviews-processed
    print(f"3. Checking if file exists in reviews-processed...")
    try:
        s3.head_object(Bucket="reviews-processed", Key=test_key)
        print("✓ File found in reviews-processed")
        
        # Read the file to verify content
        obj = s3.get_object(Bucket="reviews-processed", Key=test_key)
        content = json.loads(obj["Body"].read())
        print(f"✓ File content verified: {len(content)} fields")
        
    except Exception as e:
        print(f"✗ File not found in reviews-processed: {e}")
    
    # Cleanup
    print(f"4. Cleaning up...")
    try:
        s3.delete_object(Bucket="reviews-checked", Key=test_key)
        s3.delete_object(Bucket="reviews-processed", Key=test_key)
        print("✓ Cleaned up test files")
    except:
        pass

if __name__ == "__main__":
    debug_sentiment_lambda() 