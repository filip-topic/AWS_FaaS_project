import os
import json
import boto3
import sys

# Set environment for LocalStack
os.environ["STAGE"] = "local"

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.profanity import check_profanity
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
        stats_table = get_param("/dic2025/a3/table/customer_stats")
        
        print(f"Processing with processed_bucket={processed_bucket}, review_table={review_table}, stats_table={stats_table}")
        
        for record in event["Records"]:
            key = record["s3"]["object"]["key"]
            print(f"Processing key: {key}")
            
            try:
                obj = s3.get_object(Bucket=processed_bucket, Key=key)
                review = json.loads(obj["Body"].read())
                
                print(f"Review data: customerId={review['customerId']}, reviewId={review['reviewId']}")
                print(f"Review text: '{review.get('reviewText', '')}'")
                
                # Check if this review has already been processed
                try:
                    existing_review = ddb.get_item(
                        TableName=review_table,
                        Key={
                            "customerId": {"S": review["customerId"]},
                            "reviewId": {"S": review["reviewId"]}
                        }
                    )
                    
                    if "Item" in existing_review:
                        # Only skip if 'isUnpolite' is already set
                        if "isUnpolite" in existing_review["Item"]:
                            print(f"Review {review['reviewId']} already processed for profanity, skipping")
                            continue
                        else:
                            print(f"Review {review['reviewId']} exists but not checked for profanity, updating")
                except Exception as e:
                    print(f"Error checking existing review: {e}")
                
                # Check for profanity in review text
                has_profanity = check_profanity(review.get("reviewText", ""))
                print(f"Profanity check result: {has_profanity}")
                
                # Store in review metadata table
                try:
                    ddb.put_item(
                        TableName=review_table,
                        Item={
                            "customerId": {"S": review["customerId"]},
                            "reviewId": {"S": review["reviewId"]},
                            "isUnpolite": {"BOOL": has_profanity}
                        }
                    )
                    print(f"Stored review metadata: isUnpolite={has_profanity}")
                except Exception as e:
                    print(f"Error storing review metadata: {e}")
                    raise
                
                # Update customer stats only if there's profanity
                if has_profanity:
                    customer_id = review["customerId"]
                    print(f"Updating stats for customer: {customer_id}")
                    
                    # Get current stats
                    try:
                        response = ddb.get_item(
                            TableName=stats_table,
                            Key={"customerId": {"S": customer_id}}
                        )
                        
                        if "Item" in response:
                            current_count = int(response["Item"]["unpoliteCount"]["N"])
                            is_banned = response["Item"]["banned"]["BOOL"]
                            print(f"Current stats: count={current_count}, banned={is_banned}")
                        else:
                            current_count = 0
                            is_banned = False
                            print(f"No existing stats, starting with count=0")
                            
                    except Exception as e:
                        print(f"Error getting customer stats: {e}")
                        current_count = 0
                        is_banned = False
                    
                    # Update count and check for banning
                    new_count = current_count + 1
                    should_ban = new_count > 3
                    
                    try:
                        ddb.put_item(
                            TableName=stats_table,
                            Item={
                                "customerId": {"S": customer_id},
                                "unpoliteCount": {"N": str(new_count)},
                                "banned": {"BOOL": should_ban}
                            }
                        )
                        print(f"Updated customer stats: count={new_count}, banned={should_ban}")
                    except Exception as e:
                        print(f"Error updating customer stats: {e}")
                        raise
                else:
                    print(f"No profanity detected, skipping stats update")
                
                print(f"Successfully processed profanity check for {key}, has_profanity={has_profanity}")
                
            except Exception as e:
                print(f"Error processing record {key}: {e}")
                raise
            
        return {"status": "done"}
    except Exception as e:
        print(f"Error in profanity check handler: {str(e)}")
        raise