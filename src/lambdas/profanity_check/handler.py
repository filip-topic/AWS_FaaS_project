import os
import json
import boto3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.profanity import contains_bad_words
from utils.ssm_utils import get_param

endpoint_url = "http://localhost:4566" if os.getenv("STAGE") == "local" else None
s3 = boto3.client("s3", endpoint_url=endpoint_url)
ssm = boto3.client("ssm", endpoint_url=endpoint_url)
ddb = boto3.client("dynamodb", endpoint_url=endpoint_url)


def handler(event, context):
    processed_bucket = get_param("/dic2025/a3/bucket/processed")
    review_table = get_param("/dic2025/a3/table/review_metadata")
    stats_table = get_param("/dic2025/a3/table/customer_stats")
    for record in event["Records"]:
        key = record["s3"]["object"]["key"]
        obj = s3.get_object(Bucket=processed_bucket, Key=key)
        review = json.loads(obj["Body"].read())
        is_unpolite = (
            contains_bad_words(review.get("summary_clean", [])) or
            contains_bad_words(review.get("reviewText_clean", []))
        )
        # Update review-metadata
        ddb.put_item(
            TableName=review_table,
            Item={
                "customerId": {"S": review["customerId"]},
                "reviewId": {"S": review["reviewId"]},
                "isUnpolite": {"BOOL": is_unpolite},
                # ... add other fields as needed
            }
        )
        # Increment unpoliteCount if needed
        if is_unpolite:
            ddb.update_item(
                TableName=stats_table,
                Key={"customerId": {"S": review["customerId"]}},
                UpdateExpression="ADD unpoliteCount :inc",
                ExpressionAttributeValues={":inc": {"N": "1"}},
                ReturnValues="UPDATED_NEW"
            )
    return {"status": "done"}