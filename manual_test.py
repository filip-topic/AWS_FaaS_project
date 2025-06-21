#!/usr/bin/env python3
import boto3
import json
import time
import uuid

# LocalStack configuration
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"

def manual_test():
    """Manually test the complete pipeline."""
    
    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    lambda_client = boto3.client(
        "lambda",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    ddb = boto3.client(
        "dynamodb",
        endpoint_url=ENDPOINT_URL,
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    print("=== Manual Pipeline Test ===")
    
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
    
    # Step 1: Upload to input bucket
    print(f"\n1. Uploading to input bucket...")
    s3.put_object(
        Bucket="reviews-input",
        Key=key,
        Body=json.dumps(review).encode('utf-8'),
        ContentType="application/json"
    )
    print("✓ Uploaded to input bucket")
    
    # Step 2: Wait and check if preprocessing was triggered
    print(f"\n2. Waiting for preprocessing (10 seconds)...")
    time.sleep(10)
    
    try:
        # Check if file exists in processed bucket
        s3.head_object(Bucket="reviews-processed", Key=key)
        print("✓ File found in processed bucket - preprocessing worked!")
        
        # Get the processed file
        obj = s3.get_object(Bucket="reviews-processed", Key=key)
        processed_review = json.loads(obj["Body"].read())
        print(f"✓ Processed review has {len(processed_review)} fields")
        if "summary_clean" in processed_review:
            print(f"✓ summary_clean field found: {processed_review['summary_clean'][:3]}...")
        if "reviewText_clean" in processed_review:
            print(f"✓ reviewText_clean field found: {processed_review['reviewText_clean'][:3]}...")
            
    except Exception as e:
        print(f"✗ File not found in processed bucket: {e}")
        print("This means S3 event notifications are not working in LocalStack")
        
        # Try manual invocation instead
        print(f"\n3. Trying manual Lambda invocation...")
        try:
            event = {
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
            
            response = lambda_client.invoke(
                FunctionName='preprocessing',
                Payload=json.dumps(event)
            )
            print(f"✓ Manual invocation successful (status: {response['StatusCode']})")
            
            # Check if file was created
            time.sleep(2)
            try:
                s3.head_object(Bucket="reviews-processed", Key=key)
                print("✓ File now exists in processed bucket after manual invocation!")
            except:
                print("✗ File still not found after manual invocation")
                
        except Exception as e2:
            print(f"✗ Manual invocation failed: {e2}")
    
    # Step 3: Check DynamoDB entries
    print(f"\n4. Checking DynamoDB entries...")
    try:
        # Check review metadata
        response = ddb.get_item(
            TableName="review-metadata",
            Key={
                "customerId": {"S": customer_id},
                "reviewId": {"S": review_id}
            }
        )
        
        if "Item" in response:
            print("✓ Review metadata found in DynamoDB")
            item = response["Item"]
            if "isUnpolite" in item:
                print(f"  - isUnpolite: {item['isUnpolite']['BOOL']}")
            if "sentiment" in item:
                print(f"  - sentiment: {item['sentiment']['N']}")
        else:
            print("✗ Review metadata not found in DynamoDB")
            
        # Check customer stats
        response = ddb.get_item(
            TableName="customer-stats",
            Key={"customerId": {"S": customer_id}}
        )
        
        if "Item" in response:
            print("✓ Customer stats found in DynamoDB")
            item = response["Item"]
            if "unpoliteCount" in item:
                print(f"  - unpoliteCount: {item['unpoliteCount']['N']}")
            if "banned" in item:
                print(f"  - banned: {item['banned']['BOOL']}")
        else:
            print("✗ Customer stats not found in DynamoDB")
            
    except Exception as e:
        print(f"✗ Error checking DynamoDB: {e}")
    
    # Cleanup
    print(f"\n5. Cleaning up...")
    try:
        s3.delete_object(Bucket="reviews-input", Key=key)
        s3.delete_object(Bucket="reviews-processed", Key=key)
        print("✓ Cleaned up test files")
    except:
        pass

if __name__ == "__main__":
    manual_test() 