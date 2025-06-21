import os
import json
import boto3
from utils.ssm_utils import get_param
from utils.sentiment import analyze_sentiment

endpoint_url = "http://localhost:4566" if os.getenv("STAGE") == "local" else None
s3 = boto3.client("s3", endpoint_url=endpoint_url)
ddb = boto3.client("dynamodb", endpoint_url=endpoint_url)
processed_bucket = get_param("/dic2025/a3/bucket/processed")
review_table = get_param("/dic2025/a3/table/review_metadata")
stats_table = get_param("/dic2025/a3/table/customer_stats")


def handler(event, context):

    for record in event["Records"]:
        key = record["s3"]["object"]["key"]
        obj = s3.get_object(Bucket=processed_bucket, Key=key)
        review = json.loads(obj["Body"].read())
        sentiment = analyze_sentiment(review.get("reviewText", ""))
        # Update review-metadata with sentiment
        ddb.update_item(
            TableName=review_table,
            Key={
                "customerId": {"S": review["customerId"]},
                "reviewId": {"S": review["reviewId"]}
            },
            UpdateExpression="SET sentiment = :s",
            ExpressionAttributeValues={":s": {"N": str(sentiment)}}
        )
        # Check and ban user if needed
        stats = ddb.get_item(
            TableName=stats_table,
            Key={"customerId": {"S": review["customerId"]}}
        )
        unpolite_count = int(stats["Item"].get("unpoliteCount", {"N": "0"})["N"])
        if unpolite_count > 3:
            ddb.update_item(
                TableName=stats_table,
                Key={"customerId": {"S": review["customerId"]}},
                UpdateExpression="SET banned = :b",
                ExpressionAttributeValues={":b": {"BOOL": True}}
            )
    return {"status": "done"} 