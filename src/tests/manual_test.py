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

BUCKET_INPUT = "reviews-input"
BUCKET_PREPROCESSED = "reviews-preprocessed"
BUCKET_CHECKED = "reviews-checked"
BUCKET_PROCESSED = "reviews-processed"

LAMBDA_PREPROCESSING = "preprocessing"
LAMBDA_PROFANITY = "profanity_check"
LAMBDA_SENTIMENT = "sentiment_analysis"

REVIEW_TABLE = "review-metadata"
STATS_TABLE = "customer-stats"

def wait_for_file(s3, bucket, key, timeout=20):
    for _ in range(timeout):
        try:
            s3.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            time.sleep(1)
    return False

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
    
    print("=== Manual Pipeline Test (Chained) ===")
    
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
        Bucket=BUCKET_INPUT,
        Key=key,
        Body=json.dumps(review).encode('utf-8'),
        ContentType="application/json"
    )
    print("✓ Uploaded to input bucket")
    
    # Step 2: Wait and check if preprocessing was triggered
    print(f"\n2. Waiting for preprocessing output in {BUCKET_PREPROCESSED} (20s)...")
    if wait_for_file(s3, BUCKET_PREPROCESSED, key):
        print(f"✓ File found in {BUCKET_PREPROCESSED}")
    else:
        print(f"✗ File not found in {BUCKET_PREPROCESSED}. Trying manual Lambda invocation...")
        event = {"Records": [{"s3": {"object": {"key": key}}}]}
        resp = lambda_client.invoke(FunctionName=LAMBDA_PREPROCESSING, Payload=json.dumps(event))
        print(f"✓ Manual invocation preprocessing (status: {resp['StatusCode']})")
        if wait_for_file(s3, BUCKET_PREPROCESSED, key):
            print(f"✓ File now exists in {BUCKET_PREPROCESSED} after manual invocation!")
        else:
            print(f"✗ File still not found after manual invocation. Aborting.")
            return
    
    # Step 3: Wait and check if profanity check was triggered
    print(f"\n3. Waiting for profanity check output in {BUCKET_CHECKED} (20s)...")
    if wait_for_file(s3, BUCKET_CHECKED, key):
        print(f"✓ File found in {BUCKET_CHECKED}")
    else:
        print(f"✗ File not found in {BUCKET_CHECKED}. Trying manual Lambda invocation...")
        event = {"Records": [{"s3": {"object": {"key": key}}}]}
        resp = lambda_client.invoke(FunctionName=LAMBDA_PROFANITY, Payload=json.dumps(event))
        print(f"✓ Manual invocation profanity_check (status: {resp['StatusCode']})")
        if wait_for_file(s3, BUCKET_CHECKED, key):
            print(f"✓ File now exists in {BUCKET_CHECKED} after manual invocation!")
        else:
            print(f"✗ File still not found after manual invocation. Aborting.")
            return
    
    # Step 4: Wait and check if sentiment analysis was triggered
    print(f"\n4. Waiting for sentiment analysis output in {BUCKET_PROCESSED} (20s)...")
    if wait_for_file(s3, BUCKET_PROCESSED, key):
        print(f"✓ File found in {BUCKET_PROCESSED}")
    else:
        print(f"✗ File not found in {BUCKET_PROCESSED}. Trying manual Lambda invocation...")
        # First, verify the input file exists
        if wait_for_file(s3, BUCKET_CHECKED, key):
            print(f"✓ Input file exists in {BUCKET_CHECKED}")
        else:
            print(f"✗ Input file missing in {BUCKET_CHECKED}. Cannot proceed.")
            return
        event = {"Records": [{"s3": {"object": {"key": key}}}]}
        try:
            resp = lambda_client.invoke(FunctionName=LAMBDA_SENTIMENT, Payload=json.dumps(event))
            print(f"✓ Manual invocation sentiment_analysis (status: {resp['StatusCode']})")
            # Check the response payload for any errors
            if 'Payload' in resp:
                payload = json.loads(resp['Payload'].read())
                print(f"Lambda response: {payload}")
        except Exception as e:
            print(f"✗ Error invoking sentiment_analysis: {e}")
            return
        if wait_for_file(s3, BUCKET_PROCESSED, key):
            print(f"✓ File now exists in {BUCKET_PROCESSED} after manual invocation!")
        else:
            print(f"✗ File still not found after manual invocation. Aborting.")
            return
    
    # Step 5: Check DynamoDB entries
    print(f"\n5. Checking DynamoDB entries...")
    try:
        # Check review metadata
        response = ddb.get_item(
            TableName=REVIEW_TABLE,
            Key={"customerId": {"S": customer_id}, "reviewId": {"S": review_id}}
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
            TableName=STATS_TABLE,
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
    print(f"\n6. Cleaning up...")
    try:
        s3.delete_object(Bucket=BUCKET_INPUT, Key=key)
        s3.delete_object(Bucket=BUCKET_PREPROCESSED, Key=key)
        s3.delete_object(Bucket=BUCKET_CHECKED, Key=key)
        s3.delete_object(Bucket=BUCKET_PROCESSED, Key=key)
        print("✓ Cleaned up test files")
    except:
        pass

if __name__ == "__main__":
    manual_test() 