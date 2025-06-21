#!/bin/bash
set -e

# Directory paths
LAMBDA_DIRS=(
  "src/lambdas/preprocessing"
  "src/lambdas/profanity_check"
  "src/lambdas/sentiment_analysis"
)
LAMBDA_NAMES=(
  "preprocessing"
  "profanity_check"
  "sentiment_analysis"
)

ROLE_ARN="arn:aws:iam::000000000000:role/lambda-role"
RUNTIME="python3.11"

# Deploy each lambda
for i in ${!LAMBDA_DIRS[@]}; do
  DIR=${LAMBDA_DIRS[$i]}
  NAME=${LAMBDA_NAMES[$i]}
  ZIP_FILE="$DIR/lambda.zip"

  echo "Zipping $NAME..."
  (cd "$DIR" && zip -r lambda.zip . > /dev/null)

  echo "Deleting existing function (if any): $NAME"
  awslocal lambda delete-function --function-name "$NAME" 2>/dev/null || true

  echo "Creating function: $NAME"
  awslocal lambda create-function \
    --function-name "$NAME" \
    --runtime $RUNTIME \
    --handler handler.handler \
    --role $ROLE_ARN \
    --zip-file fileb://$ZIP_FILE \
    --timeout 30

done

echo "All Lambda functions deployed to LocalStack!" 