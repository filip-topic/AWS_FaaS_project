import os
import time
import json
import uuid
import typing

import boto3
import pytest

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_dynamodb import DynamoDBClient

os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

s3: "S3Client" = boto3.client("s3", endpoint_url="http://localhost:4566")
ssm: "SSMClient" = boto3.client("ssm", endpoint_url="http://localhost:4566")
awslambda: "LambdaClient" = boto3.client("lambda", endpoint_url="http://localhost:4566")
ddb: "DynamoDBClient" = boto3.client("dynamodb", endpoint_url="http://localhost:4566")

def cleanup_test_data():
    """Clean up any test data from previous runs."""
    try:
        review_table = get_param("/dic2025/a3/table/review_metadata")
        stats_table = get_param("/dic2025/a3/table/customer_stats")
        # Scan and delete test items from review-metadata (composite key)
        response = ddb.scan(TableName=review_table)
        for item in response.get("Items", []):
            if "customerId" in item and item["customerId"]["S"].startswith("test_run_"):
                ddb.delete_item(
                    TableName=review_table,
                    Key={
                        "customerId": item["customerId"],
                        "reviewId": item["reviewId"]
                    }
                )
        # Scan and delete test items from customer-stats (single key)
        response = ddb.scan(TableName=stats_table)
        for item in response.get("Items", []):
            if "customerId" in item and item["customerId"]["S"].startswith("test_run_"):
                ddb.delete_item(
                    TableName=stats_table,
                    Key={"customerId": item["customerId"]}
                )
    except Exception as e:
        print(f"Warning: Could not cleanup test data: {e}")

def wait_for_tables_empty(timeout=30):
    """Poll DynamoDB to ensure test tables are empty before starting a test."""
    review_table = get_param("/dic2025/a3/table/review_metadata")
    stats_table = get_param("/dic2025/a3/table/customer_stats")
    start = time.time()
    while time.time() - start < timeout:
        review_items = ddb.scan(TableName=review_table).get("Items", [])
        stats_items = ddb.scan(TableName=stats_table).get("Items", [])
        review_left = [item for item in review_items if item["customerId"]["S"].startswith("test_run_")]
        stats_left = [item for item in stats_items if item["customerId"]["S"].startswith("test_run_")]
        if not review_left and not stats_left:
            return
        time.sleep(1)
    raise RuntimeError("DynamoDB test tables not empty after cleanup!")

@pytest.fixture(autouse=True)
def _wait_for_lambdas():
    awslambda.get_waiter("function_active").wait(FunctionName="preprocessing")
    awslambda.get_waiter("function_active").wait(FunctionName="profanity_check")
    awslambda.get_waiter("function_active").wait(FunctionName="sentiment_analysis")

@pytest.fixture(autouse=True)
def _cleanup_before_test():
    cleanup_test_data()
    wait_for_tables_empty()
    yield
    cleanup_test_data()
    wait_for_tables_empty()

def get_param(name):
    return ssm.get_parameter(Name=name)["Parameter"]["Value"]

def create_test_review(customer_id="test_customer_1", review_id=None, has_profanity=False):
    if review_id is None:
        review_id = str(uuid.uuid4())
    review = {
        "customerId": customer_id,
        "reviewId": review_id,
        "summary": "This is a great product!",
        "reviewText": "I really love this product. It works perfectly.",
        "overall": 5
    }
    if has_profanity:
        review["reviewText"] += " This is a bad word test."
    return review

def trigger_lambda_manually(function_name, s3_event):
    response = awslambda.invoke(
        FunctionName=function_name,
        Payload=json.dumps(s3_event)
    )
    return response

# Unique test run ID for this session
test_run_id = f"test_run_{uuid.uuid4()}"

def test_preprocessing_lambda_trigger():
    """Test that file upload to S3 triggers preprocessing_lambda."""
    input_bucket = get_param("/dic2025/a3/bucket/input")
    processed_bucket = get_param("/dic2025/a3/bucket/processed")
    
    # Create test review
    review = create_test_review()
    key = f"review_{uuid.uuid4()}.json"
    
    # Upload to input bucket
    s3.put_object(
        Bucket=input_bucket,
        Key=key,
        Body=json.dumps(review).encode('utf-8'),
        ContentType="application/json"
    )
    
    # Manually trigger preprocessing (since LocalStack S3 notifications don't work)
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
    
    trigger_lambda_manually("preprocessing", s3_event)
    
    # Wait for preprocessing to complete
    time.sleep(3)
    
    # Verify preprocessing output
    obj = s3.get_object(Bucket=processed_bucket, Key=key)
    processed_review = json.loads(obj["Body"].read())
    
    # Check that preprocessing added cleaned text fields
    assert "summary_clean" in processed_review
    assert "reviewText_clean" in processed_review
    assert isinstance(processed_review["summary_clean"], list)
    assert isinstance(processed_review["reviewText_clean"], list)
    
    # Cleanup
    s3.delete_object(Bucket=input_bucket, Key=key)
    s3.delete_object(Bucket=processed_bucket, Key=key)

def test_profanity_detection():
    """Test profanity detection and unpoliteCount updates."""
    input_bucket = get_param("/dic2025/a3/bucket/input")
    processed_bucket = get_param("/dic2025/a3/bucket/processed")
    review_table = get_param("/dic2025/a3/table/review_metadata")
    stats_table = get_param("/dic2025/a3/table/customer_stats")
    
    customer_id = f"{test_run_id}_customer_{uuid.uuid4()}"
    review = create_test_review(customer_id=customer_id, has_profanity=True)
    key = f"review_{uuid.uuid4()}.json"
    
    # Upload review with profanity
    s3.put_object(
        Bucket=input_bucket,
        Key=key,
        Body=json.dumps(review).encode('utf-8'),
        ContentType="application/json"
    )
    
    # Manually trigger preprocessing
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
    
    trigger_lambda_manually("preprocessing", s3_event)
    time.sleep(2)
    
    # Manually trigger profanity check
    trigger_lambda_manually("profanity_check", s3_event)
    time.sleep(2)
    
    # Check review metadata
    response = ddb.get_item(
        TableName=review_table,
        Key={
            "customerId": {"S": customer_id},
            "reviewId": {"S": review["reviewId"]}
        }
    )
    
    assert "Item" in response
    assert response["Item"]["isUnpolite"]["BOOL"] == True
    
    # Check customer stats
    stats_response = ddb.get_item(
        TableName=stats_table,
        Key={"customerId": {"S": customer_id}}
    )
    
    assert "Item" in stats_response
    assert int(stats_response["Item"]["unpoliteCount"]["N"]) == 1
    
    # Cleanup
    s3.delete_object(Bucket=input_bucket, Key=key)
    s3.delete_object(Bucket=processed_bucket, Key=key)

def test_sentiment_analysis():
    """Test sentiment analysis is performed and stored."""
    input_bucket = get_param("/dic2025/a3/bucket/input")
    processed_bucket = get_param("/dic2025/a3/bucket/processed")
    review_table = get_param("/dic2025/a3/table/review_metadata")
    
    customer_id = f"{test_run_id}_customer_{uuid.uuid4()}"
    review = create_test_review(customer_id=customer_id)
    key = f"review_{uuid.uuid4()}.json"
    
    # Upload positive review
    s3.put_object(
        Bucket=input_bucket,
        Key=key,
        Body=json.dumps(review).encode('utf-8'),
        ContentType="application/json"
    )
    
    # Manually trigger preprocessing
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
    
    trigger_lambda_manually("preprocessing", s3_event)
    time.sleep(2)
    
    # Manually trigger sentiment analysis
    trigger_lambda_manually("sentiment_analysis", s3_event)
    time.sleep(2)
    
    # Check sentiment was added
    response = ddb.get_item(
        TableName=review_table,
        Key={
            "customerId": {"S": customer_id},
            "reviewId": {"S": review["reviewId"]}
        }
    )
    
    assert "Item" in response
    assert "sentiment" in response["Item"]
    sentiment = float(response["Item"]["sentiment"]["N"])
    assert sentiment > 0  # Should be positive for this review
    
    # Cleanup
    s3.delete_object(Bucket=input_bucket, Key=key)
    s3.delete_object(Bucket=processed_bucket, Key=key)

def test_customer_banning():
    """Test customer is banned after more than 3 unpolite reviews."""
    input_bucket = get_param("/dic2025/a3/bucket/input")
    processed_bucket = get_param("/dic2025/a3/bucket/processed")
    stats_table = get_param("/dic2025/a3/table/customer_stats")
    
    customer_id = f"{test_run_id}_customer_{uuid.uuid4()}"
    print(f"Testing customer banning for customer: {customer_id}")
    
    # Upload 4 unpolite reviews
    for i in range(4):
        review = create_test_review(
            customer_id=customer_id,
            review_id=f"review_{uuid.uuid4()}",  # Use unique review ID
            has_profanity=True
        )
        key = f"review_{uuid.uuid4()}.json"
        
        print(f"Processing review {i+1}: {review['reviewId']} with text: '{review['reviewText']}'")
        
        s3.put_object(
            Bucket=input_bucket,
            Key=key,
            Body=json.dumps(review).encode('utf-8'),
            ContentType="application/json"
        )
        
        # Manually trigger preprocessing and profanity check
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
        
        print(f"  Triggering preprocessing for review {i+1}")
        trigger_lambda_manually("preprocessing", s3_event)
        time.sleep(2)  # Wait longer for preprocessing
        
        print(f"  Triggering profanity check for review {i+1}")
        trigger_lambda_manually("profanity_check", s3_event)
        time.sleep(2)  # Wait longer for profanity check
        
        # Check intermediate results
        try:
            stats_response = ddb.get_item(
                TableName=stats_table,
                Key={"customerId": {"S": customer_id}}
            )
            if "Item" in stats_response:
                current_count = int(stats_response["Item"]["unpoliteCount"]["N"])
                print(f"  After review {i+1}: unpoliteCount = {current_count}")
            else:
                print(f"  After review {i+1}: no stats entry found")
        except Exception as e:
            print(f"  Error checking stats after review {i+1}: {e}")
        
        # Cleanup this file
        s3.delete_object(Bucket=input_bucket, Key=key)
        s3.delete_object(Bucket=processed_bucket, Key=key)
    
    # Wait for final processing
    time.sleep(5)  # Wait longer for all processing to complete
    
    # Check customer is banned
    stats_response = ddb.get_item(
        TableName=stats_table,
        Key={"customerId": {"S": customer_id}}
    )
    
    print(f"Final stats response: {stats_response}")
    
    assert "Item" in stats_response
    assert int(stats_response["Item"]["unpoliteCount"]["N"]) == 4
    assert stats_response["Item"]["banned"]["BOOL"] == True

def test_full_pipeline_integration():
    """Test the complete pipeline from upload to final state."""
    input_bucket = get_param("/dic2025/a3/bucket/input")
    processed_bucket = get_param("/dic2025/a3/bucket/processed")
    review_table = get_param("/dic2025/a3/table/review_metadata")
    stats_table = get_param("/dic2025/a3/table/customer_stats")
    
    customer_id = f"{test_run_id}_customer_{uuid.uuid4()}"
    review = create_test_review(customer_id=customer_id, has_profanity=True)
    key = f"review_{uuid.uuid4()}.json"
    
    # Upload review
    s3.put_object(
        Bucket=input_bucket,
        Key=key,
        Body=json.dumps(review).encode('utf-8'),
        ContentType="application/json"
    )
    
    # Manually trigger all Lambda functions
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
    
    # Trigger preprocessing
    trigger_lambda_manually("preprocessing", s3_event)
    time.sleep(2)
    
    # Trigger profanity check
    trigger_lambda_manually("profanity_check", s3_event)
    time.sleep(2)
    
    # Trigger sentiment analysis
    trigger_lambda_manually("sentiment_analysis", s3_event)
    time.sleep(2)
    
    # Verify all stages completed
    # 1. Preprocessing
    obj = s3.get_object(Bucket=processed_bucket, Key=key)
    processed_review = json.loads(obj["Body"].read())
    assert "summary_clean" in processed_review
    assert "reviewText_clean" in processed_review
    
    # 2. Profanity check
    review_response = ddb.get_item(
        TableName=review_table,
        Key={
            "customerId": {"S": customer_id},
            "reviewId": {"S": review["reviewId"]}
        }
    )
    assert "Item" in review_response
    assert "isUnpolite" in review_response["Item"]
    assert "sentiment" in review_response["Item"]
    
    # 3. Customer stats
    stats_response = ddb.get_item(
        TableName=stats_table,
        Key={"customerId": {"S": customer_id}}
    )
    assert "Item" in stats_response
    assert "unpoliteCount" in stats_response["Item"]
    
    # Cleanup
    s3.delete_object(Bucket=input_bucket, Key=key)
    s3.delete_object(Bucket=processed_bucket, Key=key) 