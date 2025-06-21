import os
import json
import boto3
import sys

# Set environment for LocalStack
os.environ["STAGE"] = "local"

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.text_preprocessing import preprocess
from utils.ssm_utils import get_param

# Use LocalStack endpoint for Lambda functions
# When running inside LocalStack Lambda containers, use the internal endpoint
if os.getenv("STAGE") == "local":
    endpoint_url = "http://host.docker.internal:4566"  # Internal LocalStack endpoint
else:
    endpoint_url = None

s3 = boto3.client("s3", endpoint_url=endpoint_url)

def handler(event, context):
    try:
        input_bucket = get_param("/dic2025/a3/bucket/input")
        output_bucket = get_param("/dic2025/a3/bucket/processed")
        
        print(f"Processing with input_bucket={input_bucket}, output_bucket={output_bucket}")
        
        for record in event["Records"]:
            key = record["s3"]["object"]["key"]
            print(f"Processing key: {key}")
            
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
            print(f"Successfully processed and stored {key}")
            
        return {"status": "done"}
    except Exception as e:
        print(f"Error in preprocessing handler: {str(e)}")
        raise