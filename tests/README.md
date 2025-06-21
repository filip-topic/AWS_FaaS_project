# Integration Tests

This directory contains automated integration tests for the review analysis pipeline.

## Test Structure

- `test_integration.py`: Main integration tests for the complete pipeline
- `test_utils.py`: Unit tests for utility functions
- `conftest.py`: Pytest configuration and fixtures

## Test Coverage

### Integration Tests (`test_integration.py`)

1. **`test_preprocessing_lambda_trigger()`**
   - Tests that file upload to S3 triggers preprocessing_lambda
   - Verifies preprocessing output contains cleaned text fields

2. **`test_profanity_detection()`**
   - Tests profanity detection and unpoliteCount updates
   - Verifies review metadata and customer stats are updated correctly

3. **`test_sentiment_analysis()`**
   - Tests sentiment analysis is performed and stored
   - Verifies sentiment values are added to review metadata

4. **`test_customer_banning()`**
   - Tests customer is banned after more than 3 unpolite reviews
   - Verifies ban logic works correctly

5. **`test_full_pipeline_integration()`**
   - Tests the complete pipeline from upload to final state
   - Verifies all stages complete successfully

### Unit Tests (`test_utils.py`)

1. **Text Preprocessing Tests**
   - Tokenization, stopword removal, lemmatization
   - Edge cases (empty text, whitespace)

2. **Sentiment Analysis Tests**
   - Positive, negative, and neutral sentiment detection
   - Edge cases (empty text)

## Running Tests

### Prerequisites

1. LocalStack running: `localstack start`
2. AWS resources created: `python src/infrastructure/setup_localstack_resources.py`
3. Lambda functions deployed and active

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_utils.py -v

# Integration tests only
pytest tests/test_integration.py -v

# Run with detailed output
pytest tests/ -v -s
```

### Test Environment

Tests use LocalStack endpoints and test AWS credentials:
- Endpoint: `http://localhost:4566`
- Region: `us-east-1`
- Credentials: `test`/`test`

## Test Data

Tests create temporary test reviews with:
- Unique customer IDs and review IDs
- Configurable profanity content
- Positive/negative sentiment text

All test data is cleaned up after each test to avoid interference.

## Troubleshooting

1. **Lambda functions not found**: Ensure functions are deployed and active
2. **SSM parameters missing**: Run the setup script first
3. **Tests timing out**: Increase sleep times if processing is slow
4. **LocalStack not responding**: Restart LocalStack and recreate resources 