#!/usr/bin/env python3
import boto3
import json
import uuid

# LocalStack configuration
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"

def test_single_lambda():
    """Test a single Lambda invocation and see the logs."""
    
    lambda_client = boto3.client(
        "lambda",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    print("=== Testing Single Lambda Invocation ===")
    
    # Create test data with new test run ID format
    test_run_id = f"test_run_{uuid.uuid4()}"
    customer_id = f"{test_run_id}_customer_{uuid.uuid4()}"
    review_id = f"review_{uuid.uuid4()}"
    key = f"review_{uuid.uuid4()}.json"
    
    review = {
        "customerId": customer_id,
        "reviewId": review_id,
        "summary": "This is a great product!",
        "reviewText": "I really love this product. It works perfectly. This is a bad word test.",
        "overall": 5
    }
    
    print(f"Test data:")
    print(f"  Test run ID: {test_run_id}")
    print(f"  Customer ID: {customer_id}")
    print(f"  Review ID: {review_id}")
    print(f"  S3 Key: {key}")
    print(f"  Review text: '{review['reviewText']}'")
    
    # Upload test file to processed bucket (since profanity check reads from processed bucket)
    s3.put_object(
        Bucket="reviews-processed",
        Key=key,
        Body=json.dumps(review).encode('utf-8'),
        ContentType="application/json"
    )
    print("✓ Uploaded test file to processed bucket")
    
    # Test profanity check function
    print(f"\nTesting profanity check function...")
    s3_event = {
        "Records": [
            {
                "s3": {
                    "object": {
                        "key": key
                    }
                }
            }
        ]
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='profanity_check',
            Payload=json.dumps(s3_event),
            LogType='Tail'  # Get logs
        )
        
        print(f"✓ Invocation successful (status: {response['StatusCode']})")
        
        # Check the response payload
        if 'Payload' in response:
            payload = response['Payload'].read()
            print(f"Response payload: {payload}")
            
            # Check if there was an error
            if response.get('FunctionError'):
                print(f"✗ Function error: {response['FunctionError']}")
        
        # Check logs if available
        if 'LogResult' in response:
            import base64
            logs = base64.b64decode(response['LogResult']).decode('utf-8')
            print(f"Lambda logs:\n{logs}")
            
    except Exception as e:
        print(f"✗ Invocation failed: {e}")
    
    # Check if review metadata was created
    print(f"\nChecking review metadata...")
    ddb = boto3.client(
        "dynamodb",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    try:
        review_response = ddb.get_item(
            TableName="review-metadata",
            Key={
                "customerId": {"S": customer_id},
                "reviewId": {"S": review_id}
            }
        )
        if "Item" in review_response:
            print(f"✓ Review metadata found: {review_response['Item']}")
        else:
            print(f"✗ No review metadata found")
    except Exception as e:
        print(f"✗ Error checking review metadata: {e}")
    
    # Check if customer stats were created
    print(f"\nChecking customer stats...")
    try:
        stats_response = ddb.get_item(
            TableName="customer-stats",
            Key={"customerId": {"S": customer_id}}
        )
        if "Item" in stats_response:
            print(f"✓ Customer stats found: {stats_response['Item']}")
        else:
            print(f"✗ No customer stats found")
    except Exception as e:
        print(f"✗ Error checking customer stats: {e}")
    
    # Cleanup
    try:
        s3.delete_object(Bucket="reviews-processed", Key=key)
        print("\n✓ Cleaned up test files")
    except:
        pass

if __name__ == "__main__":
    test_single_lambda() 