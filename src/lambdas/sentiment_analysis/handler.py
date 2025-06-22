import os
import json
import boto3
import sys

# Set environment for LocalStack
os.environ["STAGE"] = "local"

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.sentiment import analyze_sentiment
from utils.ssm_utils import get_param

# Use LocalStack endpoint for Lambda functions
# When running inside LocalStack Lambda containers, use the internal endpoint
if os.getenv("STAGE") == "local":
    endpoint_url = "http://host.docker.internal:4566"  # Internal LocalStack endpoint
else:
    endpoint_url = None

s3 = boto3.client("s3", endpoint_url=endpoint_url)
ddb = boto3.client("dynamodb", endpoint_url=endpoint_url)

def handler(event, context):
    try:
        checked_bucket = "reviews-checked"
        processed_bucket = "reviews-processed"
        review_table = get_param("/dic2025/a3/table/review_metadata")
        print(f"Processing with checked_bucket={checked_bucket}, processed_bucket={processed_bucket}, review_table={review_table}")
        
        for record in event["Records"]:
            key = record["s3"]["object"]["key"]
            print(f"Processing key: {key}")
            print(f"Reading from bucket: {checked_bucket}")
            try:
                obj = s3.get_object(Bucket=checked_bucket, Key=key)
                review = json.loads(obj["Body"].read())
                print(f"Successfully read review from {checked_bucket}: {review.get('customerId', 'N/A')}, {review.get('reviewId', 'N/A')}")
            except Exception as e:
                print(f"Error reading from {checked_bucket}: {e}")
                raise
            
            # Analyze sentiment
            sentiment_score = analyze_sentiment(review.get("reviewText", ""))
            print(f"Sentiment analysis result: {sentiment_score}")
            
            # Update review metadata with sentiment
            try:
                ddb.update_item(
                    TableName=review_table,
                    Key={
                        "customerId": {"S": review["customerId"]},
                        "reviewId": {"S": review["reviewId"]}
                    },
                    UpdateExpression="SET sentiment = :sentiment",
                    ExpressionAttributeValues={
                        ":sentiment": {"N": str(sentiment_score)}
                    }
                )
                print(f"Successfully updated sentiment for {key}, sentiment={sentiment_score}")
            except ddb.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'ValidationException':
                    print(f"Item does not exist, creating new item for {key}")
                    ddb.put_item(
                        TableName=review_table,
                        Item={
                            "customerId": {"S": review["customerId"]},
                            "reviewId": {"S": review["reviewId"]},
                            "sentiment": {"N": str(sentiment_score)}
                        }
                    )
                    print(f"Created review metadata with sentiment for {key}, sentiment={sentiment_score}")
                else:
                    print(f"Error updating sentiment: {e}")
                    raise
            except Exception as e:
                print(f"Unexpected error updating DynamoDB: {e}")
                raise
            
            # Write to final processed bucket
            print(f"Writing to bucket: {processed_bucket}")
            try:
                s3.put_object(
                    Bucket=processed_bucket,
                    Key=key,
                    Body=json.dumps(review).encode("utf-8"),
                    ContentType="application/json"
                )
                print(f"Successfully wrote to {processed_bucket}: {key}")
            except Exception as e:
                print(f"Error writing to {processed_bucket}: {e}")
                raise
            
            print(f"Successfully processed and stored {key} in processed bucket")
        
        return {"status": "done"}
    except Exception as e:
        print(f"Error in sentiment analysis handler: {str(e)}")
        raise 