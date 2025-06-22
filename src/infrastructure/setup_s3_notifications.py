import boto3
import json

# LocalStack endpoints
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"  # Default region for LocalStack

# Dummy credentials for LocalStack
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"

# Resource names
S3_INPUT_BUCKET = "reviews-input"
S3_PREPROCESSED_BUCKET = "reviews-preprocessed"
S3_CHECKED_BUCKET = "reviews-checked"
S3_PROCESSED_BUCKET = "reviews-processed"

def setup_s3_notifications():
    """Setup S3 event notifications to trigger Lambda functions."""
    
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
    
    # Ensure all buckets exist
    for bucket in [S3_INPUT_BUCKET, S3_PREPROCESSED_BUCKET, S3_CHECKED_BUCKET, S3_PROCESSED_BUCKET]:
        try:
            s3.head_bucket(Bucket=bucket)
            print(f"✓ Bucket exists: {bucket}")
        except Exception:
            s3.create_bucket(Bucket=bucket)
            print(f"✓ Created bucket: {bucket}")
    
    # Get Lambda function ARNs
    preprocessing_arn = f"arn:aws:lambda:{REGION}:000000000000:function:preprocessing"
    profanity_check_arn = f"arn:aws:lambda:{REGION}:000000000000:function:profanity_check"
    sentiment_analysis_arn = f"arn:aws:lambda:{REGION}:000000000000:function:sentiment_analysis"
    
    print(f"Using ARNs:")
    print(f"  preprocessing: {preprocessing_arn}")
    print(f"  profanity_check: {profanity_check_arn}")
    print(f"  sentiment_analysis: {sentiment_analysis_arn}")
    
    # Setup input bucket to trigger preprocessing
    print(f"\nSetting up notifications for {S3_INPUT_BUCKET} -> preprocessing...")
    try:
        s3.put_bucket_notification_configuration(
            Bucket=S3_INPUT_BUCKET,
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': preprocessing_arn,
                        'Events': ['s3:ObjectCreated:*'],
                        'Filter': {
                            'Key': {
                                'FilterRules': [
                                    {
                                        'Name': 'suffix',
                                        'Value': '.json'
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        )
        print(f"✓ Setup S3 notifications for {S3_INPUT_BUCKET} -> preprocessing")
    except Exception as e:
        print(f"✗ Error setting up notifications for {S3_INPUT_BUCKET}: {e}")
        return
    
    # Setup processed bucket to trigger profanity_check and sentiment_analysis
    print(f"\nSetting up notifications for {S3_PREPROCESSED_BUCKET} -> profanity_check...")
    try:
        s3.put_bucket_notification_configuration(
            Bucket=S3_PREPROCESSED_BUCKET,
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': profanity_check_arn,
                        'Events': ['s3:ObjectCreated:*'],
                        'Filter': {
                            'Key': {
                                'FilterRules': [
                                    {
                                        'Name': 'suffix',
                                        'Value': '.json'
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        )
        print(f"✓ Setup S3 notifications for {S3_PREPROCESSED_BUCKET} -> profanity_check")
    except Exception as e:
        print(f"✗ Error setting up notifications for {S3_PREPROCESSED_BUCKET}: {e}")
        return
    
    print(f"\nSetting up notifications for {S3_CHECKED_BUCKET} -> sentiment_analysis...")
    try:
        s3.put_bucket_notification_configuration(
            Bucket=S3_CHECKED_BUCKET,
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': sentiment_analysis_arn,
                        'Events': ['s3:ObjectCreated:*'],
                        'Filter': {
                            'Key': {
                                'FilterRules': [
                                    {
                                        'Name': 'suffix',
                                        'Value': '.json'
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        )
        print(f"✓ Setup S3 notifications for {S3_CHECKED_BUCKET} -> sentiment_analysis")
    except Exception as e:
        print(f"✗ Error setting up notifications for {S3_CHECKED_BUCKET}: {e}")
        return
    
    # Add Lambda permissions for S3 to invoke functions
    print("\nSetting up Lambda permissions...")
    
    try:
        lambda_client.add_permission(
            FunctionName='preprocessing',
            StatementId='s3-trigger-input',
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{S3_INPUT_BUCKET}'
        )
        print("✓ Added permission for preprocessing function")
    except lambda_client.exceptions.ResourceConflictException:
        print("✓ Permission already exists for preprocessing function")
    except Exception as e:
        print(f"✗ Error adding permission for preprocessing: {e}")
    
    try:
        lambda_client.add_permission(
            FunctionName='profanity_check',
            StatementId='s3-trigger-preprocessed',
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{S3_PREPROCESSED_BUCKET}'
        )
        print("✓ Added permission for profanity_check function")
    except lambda_client.exceptions.ResourceConflictException:
        print("✓ Permission already exists for profanity_check function")
    except Exception as e:
        print(f"✗ Error adding permission for profanity_check: {e}")
    
    try:
        lambda_client.add_permission(
            FunctionName='sentiment_analysis',
            StatementId='s3-trigger-checked',
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{S3_CHECKED_BUCKET}'
        )
        print("✓ Added permission for sentiment_analysis function")
    except lambda_client.exceptions.ResourceConflictException:
        print("✓ Permission already exists for sentiment_analysis function")
    except Exception as e:
        print(f"✗ Error adding permission for sentiment_analysis: {e}")
    
    # Verify the setup
    print("\nVerifying notification setup...")
    for bucket in [S3_INPUT_BUCKET, S3_PREPROCESSED_BUCKET, S3_CHECKED_BUCKET]:
        try:
            notifications = s3.get_bucket_notification_configuration(Bucket=bucket)
            if 'LambdaFunctionConfigurations' in notifications:
                print(f"✓ {bucket} notifications verified")
            else:
                print(f"✗ {bucket} notifications not found")
        except Exception as e:
            print(f"✗ Error verifying notifications for {bucket}: {e}")

if __name__ == "__main__":
    setup_s3_notifications() 