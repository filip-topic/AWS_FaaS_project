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
    
    # First, verify Lambda functions exist
    print("Verifying Lambda functions exist...")
    try:
        functions = lambda_client.list_functions()
        function_names = [f['FunctionName'] for f in functions['Functions']]
        print(f"Available functions: {function_names}")
        
        required_functions = ['preprocessing', 'profanity_check', 'sentiment_analysis']
        for func in required_functions:
            if func not in function_names:
                print(f"ERROR: {func} function not found!")
                return
    except Exception as e:
        print(f"Error listing Lambda functions: {e}")
        return
    
    # Get Lambda function ARNs
    preprocessing_arn = f"arn:aws:lambda:{REGION}:000000000000:function:preprocessing"
    profanity_check_arn = f"arn:aws:lambda:{REGION}:000000000000:function:profanity_check"
    sentiment_analysis_arn = f"arn:aws:lambda:{REGION}:000000000000:function:sentiment_analysis"
    
    print(f"Using ARNs:")
    print(f"  preprocessing: {preprocessing_arn}")
    print(f"  profanity_check: {profanity_check_arn}")
    print(f"  sentiment_analysis: {sentiment_analysis_arn}")
    
    # Setup input bucket to trigger preprocessing
    print(f"\nSetting up notifications for {S3_INPUT_BUCKET}...")
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
    print(f"\nSetting up notifications for {S3_PROCESSED_BUCKET}...")
    try:
        s3.put_bucket_notification_configuration(
            Bucket=S3_PROCESSED_BUCKET,
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
                    },
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
        print(f"✓ Setup S3 notifications for {S3_PROCESSED_BUCKET} -> profanity_check, sentiment_analysis")
    except Exception as e:
        print(f"✗ Error setting up notifications for {S3_PROCESSED_BUCKET}: {e}")
        return
    
    # Add Lambda permissions for S3 to invoke functions
    print("\nSetting up Lambda permissions...")
    
    try:
        lambda_client.add_permission(
            FunctionName='preprocessing',
            StatementId='s3-trigger',
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
            StatementId='s3-trigger',
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{S3_PROCESSED_BUCKET}'
        )
        print("✓ Added permission for profanity_check function")
    except lambda_client.exceptions.ResourceConflictException:
        print("✓ Permission already exists for profanity_check function")
    except Exception as e:
        print(f"✗ Error adding permission for profanity_check: {e}")
    
    try:
        lambda_client.add_permission(
            FunctionName='sentiment_analysis',
            StatementId='s3-trigger',
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{S3_PROCESSED_BUCKET}'
        )
        print("✓ Added permission for sentiment_analysis function")
    except lambda_client.exceptions.ResourceConflictException:
        print("✓ Permission already exists for sentiment_analysis function")
    except Exception as e:
        print(f"✗ Error adding permission for sentiment_analysis: {e}")
    
    # Verify the setup
    print("\nVerifying notification setup...")
    try:
        input_notifications = s3.get_bucket_notification_configuration(Bucket=S3_INPUT_BUCKET)
        if 'LambdaFunctionConfigurations' in input_notifications:
            print("✓ Input bucket notifications verified")
        else:
            print("✗ Input bucket notifications not found")
        
        processed_notifications = s3.get_bucket_notification_configuration(Bucket=S3_PROCESSED_BUCKET)
        if 'LambdaFunctionConfigurations' in processed_notifications:
            print("✓ Processed bucket notifications verified")
        else:
            print("✗ Processed bucket notifications not found")
    except Exception as e:
        print(f"✗ Error verifying notifications: {e}")

if __name__ == "__main__":
    setup_s3_notifications() 