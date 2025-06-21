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
        processed_bucket = get_param("/dic2025/a3/bucket/processed")
        review_table = get_param("/dic2025/a3/table/review_metadata")
        
        print(f"Processing with processed_bucket={processed_bucket}, review_table={review_table}")
        
        for record in event["Records"]:
            key = record["s3"]["object"]["key"]
            print(f"Processing key: {key}")
            
            obj = s3.get_object(Bucket=processed_bucket, Key=key)
            review = json.loads(obj["Body"].read())
            
            # Analyze sentiment
            sentiment_score = analyze_sentiment(review.get("reviewText", ""))
            
            # Update review metadata with sentiment
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
            
            print(f"Successfully processed sentiment analysis for {key}, sentiment={sentiment_score}")
            
        return {"status": "done"}
    except Exception as e:
        print(f"Error in sentiment analysis handler: {str(e)}")
        raise 