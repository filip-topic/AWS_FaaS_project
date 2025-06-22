#!/bin/bash
set -e

echo "=== Setting up LocalStack infrastructure ==="
python src/infrastructure/setup_localstack_resources.py

echo "=== Building Lambda packages with dependencies ==="
python src/infrastructure/build_lambda_packages.py

echo "=== Deploying Lambda functions ==="
python src/infrastructure/deploy_lambdas_python.py

echo "=== Waiting for Lambda functions to be ready ==="
sleep 10

echo "=== Setting up S3 notifications ==="
python src/infrastructure/setup_s3_notifications.py

echo "=== Waiting for notifications to be configured ==="
sleep 5

echo "=== Testing setup ==="
python src/tests/test_setup.py

echo "=== Running manual test ==="
python src/tests/manual_test.py

echo "=== Running unit tests ==="
python -m pytest src/tests/test_utils.py -v

echo "=== Running integration tests ==="
python -m pytest src/tests/test_integration.py -v

echo "=== Setup and testing complete ===" 