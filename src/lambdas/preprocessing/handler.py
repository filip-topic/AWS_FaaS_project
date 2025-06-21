import os
import json
import boto3
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.text_preprocessing import preprocess
from utils.ssm_utils import get_param

endpoint_url = "http://localhost:4566" if os.getenv("STAGE") == "local" else None
s3 = boto3.client("s3", endpoint_url=endpoint_url)

def handler(event, context):
    input_bucket = get_param("/dic2025/a3/bucket/input")
    output_bucket = get_param("/dic2025/a3/bucket/processed")
    for record in event["Records"]:
        key = record["s3"]["object"]["key"]
        obj = s3.get_object(Bucket=input_bucket, Key=key)
        review = json.loads(obj["Body"].read())
        for field in ["summary", "reviewText"]:
            if field in review:
                review[f"{field}_clean"] = preprocess(review[field])
        # Store cleaned review in processed bucket
        s3.put_object(
            Bucket=output_bucket,
            Key=key,
            Body=json.dumps(review).encode("utf-8"),
            ContentType="application/json"
        )
    return {"status": "done"}