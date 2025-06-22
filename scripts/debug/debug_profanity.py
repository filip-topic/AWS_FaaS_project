#!/usr/bin/env python3
import json
import boto3
import uuid
from datetime import datetime

# LocalStack configuration
lambda_client = boto3.client(
    'lambda', 
    endpoint_url='http://localhost:4566', 
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)
s3_client = boto3.client(
    's3', 
    endpoint_url='http://localhost:4566', 
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

def test_profanity_check():
    """Test the profanity check Lambda with detailed logging."""
    
    # Create test data
    test_run_id = f"test_run_{uuid.uuid4()}"
    customer_id = f"{test_run_id}_customer_{uuid.uuid4()}"
    review_id = f"review_{uuid.uuid4()}"
    s3_key = f"review_{uuid.uuid4()}.json"
    
    # Test review with profanity
    review_data = {
        "customerId": customer_id,
        "reviewId": review_id,
        "summary": "This is a great product!",
        "reviewText": "I really love this product. It works perfectly. This is a bad word test.",
        "overall": 5,
        "summary_clean": ["great", "product"],
        "reviewText_clean": ["real", "love", "product", "work", "perfect", "bad", "word", "test"]
    }
    
    print(f"=== Testing Profanity Check Lambda ===")
    print(f"Test run ID: {test_run_id}")
    print(f"Customer ID: {customer_id}")
    print(f"Review ID: {review_id}")
    print(f"S3 Key: {s3_key}")
    print(f"Review text: '{review_data['reviewText']}'")
    print(f"Cleaned text: {review_data['reviewText_clean']}")
    
    # Upload test file to processed bucket
    try:
        s3_client.put_object(
            Bucket='reviews-processed',
            Key=s3_key,
            Body=json.dumps(review_data)
        )
        print(f"✓ Uploaded test file to processed bucket")
    except Exception as e:
        print(f"✗ Error uploading file: {e}")
        return
    
    # Invoke profanity check Lambda
    try:
        event = {
            "Records": [
                {
                    "s3": {
                        "object": {
                            "key": s3_key
                        }
                    }
                }
            ]
        }
        
        print(f"\nInvoking profanity check Lambda...")
        response = lambda_client.invoke(
            FunctionName='profanity_check',
            Payload=json.dumps(event),
            LogType='Tail'
        )
        
        print(f"✓ Lambda invocation successful")
        print(f"Status code: {response['StatusCode']}")
        
        # Get response payload
        payload = response['Payload'].read()
        print(f"Response payload: {payload}")
        
        # Get logs if available
        if 'LogResult' in response:
            import base64
            logs = base64.b64decode(response['LogResult']).decode('utf-8')
            print(f"\nLambda logs:")
            print(logs)
        
    except Exception as e:
        print(f"✗ Error invoking Lambda: {e}")
        return
    
    # Check if review metadata was created
    try:
        ddb_client = boto3.client(
            'dynamodb', 
            endpoint_url='http://localhost:4566', 
            region_name='us-east-1',
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
        
        review_response = ddb_client.get_item(
            TableName='review-metadata',
            Key={
                "customerId": {"S": customer_id},
                "reviewId": {"S": review_id}
            }
        )
        
        if "Item" in review_response:
            print(f"\n✓ Review metadata created:")
            print(f"  {review_response['Item']}")
        else:
            print(f"\n✗ No review metadata found")
            
    except Exception as e:
        print(f"✗ Error checking review metadata: {e}")
    
    # Check if customer stats were created
    try:
        stats_response = ddb_client.get_item(
            TableName='customer-stats',
            Key={
                "customerId": {"S": customer_id}
            }
        )
        
        if "Item" in stats_response:
            print(f"\n✓ Customer stats created:")
            print(f"  {stats_response['Item']}")
        else:
            print(f"\n✗ No customer stats found")
            
    except Exception as e:
        print(f"✗ Error checking customer stats: {e}")
    
    # Cleanup
    try:
        s3_client.delete_object(Bucket='reviews-processed', Key=s3_key)
        print(f"\n✓ Cleaned up test file")
    except Exception as e:
        print(f"✗ Error cleaning up: {e}")

if __name__ == "__main__":
    test_profanity_check() 