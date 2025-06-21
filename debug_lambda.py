#!/usr/bin/env python3
import boto3
import json
import uuid

# LocalStack configuration
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"

def debug_lambda():
    """Debug Lambda function execution."""
    
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
    
    print("=== Debugging Lambda Functions ===")
    
    # Create test data
    customer_id = f"test_customer_{uuid.uuid4()}"
    review_id = f"review_{uuid.uuid4()}"
    key = f"review_{uuid.uuid4()}.json"
    
    review = {
        "customerId": customer_id,
        "reviewId": review_id,
        "summary": "This is a great product!",
        "reviewText": "I really love this product. It works perfectly.",
        "overall": 5
    }
    
    print(f"Test data:")
    print(f"  Customer ID: {customer_id}")
    print(f"  Review ID: {review_id}")
    print(f"  S3 Key: {key}")
    
    # Upload test file
    s3.put_object(
        Bucket="reviews-input",
        Key=key,
        Body=json.dumps(review).encode('utf-8'),
        ContentType="application/json"
    )
    print("✓ Uploaded test file to input bucket")
    
    # Test preprocessing function
    print(f"\n1. Testing preprocessing function...")
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
            FunctionName='preprocessing',
            Payload=json.dumps(s3_event)
        )
        
        print(f"✓ Invocation successful (status: {response['StatusCode']})")
        
        # Check the response payload
        if 'Payload' in response:
            payload = response['Payload'].read()
            print(f"Response payload: {payload}")
            
            # Check if there was an error
            if response.get('FunctionError'):
                print(f"✗ Function error: {response['FunctionError']}")
        
        # Check if file was created in processed bucket
        try:
            s3.head_object(Bucket="reviews-processed", Key=key)
            print("✓ File created in processed bucket")
        except:
            print("✗ File not created in processed bucket")
            
    except Exception as e:
        print(f"✗ Invocation failed: {e}")
    
    # Test profanity check function
    print(f"\n2. Testing profanity check function...")
    try:
        response = lambda_client.invoke(
            FunctionName='profanity_check',
            Payload=json.dumps(s3_event)
        )
        
        print(f"✓ Invocation successful (status: {response['StatusCode']})")
        
        if 'Payload' in response:
            payload = response['Payload'].read()
            print(f"Response payload: {payload}")
            
        if response.get('FunctionError'):
            print(f"✗ Function error: {response['FunctionError']}")
            
    except Exception as e:
        print(f"✗ Invocation failed: {e}")
    
    # Test sentiment analysis function
    print(f"\n3. Testing sentiment analysis function...")
    try:
        response = lambda_client.invoke(
            FunctionName='sentiment_analysis',
            Payload=json.dumps(s3_event)
        )
        
        print(f"✓ Invocation successful (status: {response['StatusCode']})")
        
        if 'Payload' in response:
            payload = response['Payload'].read()
            print(f"Response payload: {payload}")
            
        if response.get('FunctionError'):
            print(f"✗ Function error: {response['FunctionError']}")
            
    except Exception as e:
        print(f"✗ Invocation failed: {e}")
    
    # Check DynamoDB
    print(f"\n4. Checking DynamoDB...")
    ddb = boto3.client(
        "dynamodb",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    try:
        response = ddb.get_item(
            TableName="review-metadata",
            Key={
                "customerId": {"S": customer_id},
                "reviewId": {"S": review_id}
            }
        )
        
        if "Item" in response:
            print("✓ Review metadata found in DynamoDB")
            print(f"  Item: {response['Item']}")
        else:
            print("✗ Review metadata not found in DynamoDB")
            
    except Exception as e:
        print(f"✗ Error checking DynamoDB: {e}")
    
    # Cleanup
    try:
        s3.delete_object(Bucket="reviews-input", Key=key)
        s3.delete_object(Bucket="reviews-processed", Key=key)
        print("\n✓ Cleaned up test files")
    except:
        pass

if __name__ == "__main__":
    debug_lambda() 