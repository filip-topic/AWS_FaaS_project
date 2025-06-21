# Integration Test Fixes

## Issues Identified

### 1. **Missing S3 Event Triggers**
- **Problem**: Lambda functions were deployed but not connected to S3 buckets via event notifications
- **Impact**: Tests failed because uploading files to S3 didn't trigger the Lambda functions
- **Fix**: Added `setup_s3_notifications()` function in `setup_localstack_resources.py` to configure S3 event notifications

### 2. **Missing Environment Variable**
- **Problem**: Lambda functions check for `os.getenv("STAGE") == "local"` but this wasn't set
- **Impact**: Lambda functions couldn't connect to LocalStack endpoints
- **Fix**: 
  - Added `os.environ["STAGE"] = "local"` to all Lambda handlers
  - Updated `deploy_lambdas.sh` to set environment variable during deployment

### 3. **Missing Lambda Permissions**
- **Problem**: S3 couldn't invoke Lambda functions due to missing permissions
- **Impact**: Event notifications failed silently
- **Fix**: Added Lambda permissions in `setup_s3_notifications()` function

### 4. **Error Handling Issues**
- **Problem**: Sentiment analysis handler tried to access `stats["Item"]` without checking if it exists
- **Impact**: Lambda function would crash when customer doesn't exist in stats table
- **Fix**: Added proper error handling and null checks in all Lambda handlers

## Files Modified

### 1. `src/lambdas/preprocessing/handler.py`
- Added environment variable setting
- Added try-catch error handling

### 2. `src/lambdas/profanity_check/handler.py`
- Added environment variable setting
- Added try-catch error handling

### 3. `src/lambdas/sentiment_analysis/handler.py`
- Added environment variable setting
- Added try-catch error handling
- Fixed stats lookup to handle missing customers

### 4. `src/infrastructure/setup_localstack_resources.py`
- Added `setup_s3_notifications()` function
- Added Lambda client initialization
- Added S3 event notification configuration
- Added Lambda permissions setup

### 5. `deploy_lambdas.sh`
- Added `--environment Variables='{STAGE=local}'` parameter

### 6. `setup_and_test.sh` (new file)
- Created comprehensive setup script that runs everything in correct order

## How to Run

1. **Make sure LocalStack is running**:
   ```bash
   localstack start
   ```

2. **Run the complete setup and test**:
   ```bash
   chmod +x setup_and_test.sh
   ./setup_and_test.sh
   ```

3. **Or run steps individually**:
   ```bash
   # Setup infrastructure
   python src/infrastructure/setup_localstack_resources.py
   
   # Deploy Lambda functions
   ./deploy_lambdas.sh
   
   # Wait for functions to be ready
   sleep 10
   
   # Run tests
   python -m pytest tests/test_integration.py -v
   ```

## Expected Test Flow

1. **test_preprocessing_lambda_trigger**: Upload file to input bucket → triggers preprocessing → file appears in processed bucket
2. **test_profanity_detection**: Upload file with profanity → triggers preprocessing → triggers profanity check → updates DynamoDB
3. **test_sentiment_analysis**: Upload file → triggers preprocessing → triggers sentiment analysis → updates DynamoDB
4. **test_customer_banning**: Upload multiple profane reviews → customer gets banned after 4th review
5. **test_full_pipeline_integration**: Tests complete end-to-end pipeline

## Troubleshooting

If tests still fail:

1. **Check LocalStack is running**: `curl http://localhost:4566/health`
2. **Check Lambda functions are deployed**: `awslocal lambda list-functions`
3. **Check S3 notifications**: `awslocal s3api get-bucket-notification-configuration --bucket reviews-input`
4. **Check Lambda logs**: `awslocal logs describe-log-groups`

## Dependencies

Make sure all required packages are installed:
```bash
pip install -r requirements.txt
``` 