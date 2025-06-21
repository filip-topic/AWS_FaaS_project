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

@pytest.fixture(autouse=True)
def _wait_for_lambdas():
    # Wait for lambdas to be available
    awslambda.get_waiter("function_active").wait(FunctionName="preprocessing")
    awslambda.get_waiter("function_active").wait(FunctionName="profanity_check")
    awslambda.get_waiter("function_active").wait(FunctionName="sentiment_analysis")

def get_param(name):
    return ssm.get_parameter(Name=name)["Parameter"]["Value"]

def create_test_review(customer_id="test_customer_1", review_id=None, has_profanity=False):
    """Create a test review with optional profanity."""
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
    
    # Wait for preprocessing to complete
    s3.get_waiter("object_exists").wait(Bucket=processed_bucket, Key=key)
    
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
    review_table = get_param("/dic2025/a3/table/review_metadata")
    stats_table = get_param("/dic2025/a3/table/customer_stats")
    
    customer_id = f"test_customer_{uuid.uuid4()}"
    review = create_test_review(customer_id=customer_id, has_profanity=True)
    key = f"review_{uuid.uuid4()}.json"
    
    # Upload review with profanity
    s3.put_object(
        Bucket=input_bucket,
        Key=key,
        Body=json.dumps(review).encode('utf-8'),
        ContentType="application/json"
    )
    
    # Wait for processing to complete
    time.sleep(5)
    
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

def test_sentiment_analysis():
    """Test sentiment analysis is performed and stored."""
    input_bucket = get_param("/dic2025/a3/bucket/input")
    review_table = get_param("/dic2025/a3/table/review_metadata")
    
    customer_id = f"test_customer_{uuid.uuid4()}"
    review = create_test_review(customer_id=customer_id)
    key = f"review_{uuid.uuid4()}.json"
    
    # Upload positive review
    s3.put_object(
        Bucket=input_bucket,
        Key=key,
        Body=json.dumps(review).encode('utf-8'),
        ContentType="application/json"
    )
    
    # Wait for processing
    time.sleep(5)
    
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

def test_customer_banning():
    """Test customer is banned after more than 3 unpolite reviews."""
    input_bucket = get_param("/dic2025/a3/bucket/input")
    stats_table = get_param("/dic2025/a3/table/customer_stats")
    
    customer_id = f"test_customer_{uuid.uuid4()}"
    
    # Upload 4 unpolite reviews
    for i in range(4):
        review = create_test_review(
            customer_id=customer_id,
            review_id=f"review_{i}",
            has_profanity=True
        )
        key = f"review_{uuid.uuid4()}.json"
        
        s3.put_object(
            Bucket=input_bucket,
            Key=key,
            Body=json.dumps(review).encode('utf-8'),
            ContentType="application/json"
        )
        
        # Wait between uploads
        time.sleep(3)
    
    # Wait for final processing
    time.sleep(5)
    
    # Check customer is banned
    stats_response = ddb.get_item(
        TableName=stats_table,
        Key={"customerId": {"S": customer_id}}
    )
    
    assert "Item" in stats_response
    assert int(stats_response["Item"]["unpoliteCount"]["N"]) == 4
    assert stats_response["Item"]["banned"]["BOOL"] == True

def test_full_pipeline_integration():
    """Test the complete pipeline from upload to final state."""
    input_bucket = get_param("/dic2025/a3/bucket/input")
    processed_bucket = get_param("/dic2025/a3/bucket/processed")
    review_table = get_param("/dic2025/a3/table/review_metadata")
    stats_table = get_param("/dic2025/a3/table/customer_stats")
    
    customer_id = f"test_customer_{uuid.uuid4()}"
    review = create_test_review(customer_id=customer_id, has_profanity=True)
    key = f"review_{uuid.uuid4()}.json"
    
    # Upload review
    s3.put_object(
        Bucket=input_bucket,
        Key=key,
        Body=json.dumps(review).encode('utf-8'),
        ContentType="application/json"
    )
    
    # Wait for complete processing
    time.sleep(10)
    
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