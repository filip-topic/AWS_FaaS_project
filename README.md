# Review Analysis Pipeline - Assignment 3

A serverless application using AWS Lambda functions, S3, and DynamoDB to analyze customer reviews for sentiment, profanity detection, and customer moderation.

## 🏗️ Architecture Overview

The application consists of three Lambda functions in a processing pipeline:

1. **Preprocessing Lambda** - Tokenizes, removes stopwords, and lemmatizes review text
2. **Profanity Check Lambda** - Detects bad words and tracks unpolite review counts
3. **Sentiment Analysis Lambda** - Analyzes sentiment and implements customer banning logic

### Data Flow:
```
S3 Upload → Preprocessing → Profanity Check → Sentiment Analysis → Customer Banning
```

## 📁 Project Structure

```
assignment_3/
├── src/
│   ├── lambdas/
│   │   ├── preprocessing/          # Text preprocessing Lambda
│   │   ├── profanity_check/        # Profanity detection Lambda
│   │   └── sentiment_analysis/     # Sentiment analysis Lambda
│   ├── infrastructure/
│   │   └── setup_localstack_resources.py  # AWS resource setup
│   └── utils/
│       ├── ssm_utils.py            # SSM parameter utilities
│       ├── text_preprocessing.py   # Text preprocessing utilities
│       ├── sentiment.py            # Sentiment analysis utilities
│       └── review_analyzer.py      # Review analysis script
├── tests/
│   ├── test_integration.py         # Integration tests
│   ├── test_utils.py               # Unit tests
│   └── conftest.py                 # Pytest configuration
├── data/
│   └── reviews_devset.json         # Review dataset
├── requirements.txt                 # Python dependencies
├── run_analysis.py                  # Review analysis runner
└── show_results.py                  # Results display script
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start LocalStack
```bash
localstack start
```

### 3. Setup AWS Resources
```bash
python src/infrastructure/setup_localstack_resources.py
```

### 4. Run Review Analysis
```bash
python run_analysis.py
```

### 5. View Results
```bash
python show_results.py
```

## 🔧 Infrastructure Setup

### `src/infrastructure/setup_localstack_resources.py`

This script creates and configures all AWS resources needed for the review analysis pipeline in LocalStack:

#### **Resources Created:**

**S3 Buckets:**
- `reviews-input` - Receives new review uploads
- `reviews-processed` - Stores preprocessed reviews

**DynamoDB Tables:**
- `review-metadata` - Stores review analysis results (PK: customerId, SK: reviewId)
- `customer-stats` - Tracks customer profanity counts and ban status (PK: customerId)

**SSM Parameters:**
- `/dic2025/a3/bucket/input` - Input bucket name
- `/dic2025/a3/bucket/processed` - Processed bucket name  
- `/dic2025/a3/table/review_metadata` - Review metadata table name
- `/dic2025/a3/table/customer_stats` - Customer stats table name

#### **Features:**
- ✅ **Idempotent**: Can be run multiple times safely
- ✅ **Reset Capability**: Deletes and recreates resources
- ✅ **LocalStack Compatible**: Uses LocalStack endpoints
- ✅ **Parameter Store Integration**: Stores all resource names in SSM

#### **Usage:**
```bash
# Run once to setup resources
python src/infrastructure/setup_localstack_resources.py

# Run again to reset/resetup resources
python src/infrastructure/setup_localstack_resources.py
```

## 📊 Review Analysis

### `run_analysis.py` & `src/utils/review_analyzer.py`

Analyzes the `reviews_devset.json` file and provides:

- **Sentiment Distribution**: Positive/Neutral/Negative review counts
- **Profanity Detection**: Reviews containing bad words
- **Customer Moderation**: Banned customers (>3 profane reviews)
- **Detailed Statistics**: Complete analysis with percentages

### Sample Output:
```
📊 SENTIMENT ANALYSIS:
   Total Reviews: 78,829
   Positive Reviews: 59,899 (76.0%)
   Neutral Reviews: 15,272 (19.4%)
   Negative Reviews: 3,658 (4.6%)

🚫 PROFANITY ANALYSIS:
   Profane Reviews: 5,705 (7.2%)

👥 CUSTOMER ANALYSIS:
   Banned Customers: 5
```

## 🧪 Testing

### Run Integration Tests
```bash
pytest tests/ -v
```

### Run Unit Tests
```bash
pytest tests/test_utils.py -v
```

### Test Coverage:
- ✅ Lambda function triggers
- ✅ Preprocessing pipeline
- ✅ Profanity detection
- ✅ Sentiment analysis
- ✅ Customer banning logic
- ✅ Utility functions

## 🔍 Key Features

- **Serverless Architecture**: AWS Lambda + S3 + DynamoDB
- **Text Processing**: NLTK-based tokenization, stopword removal, lemmatization
- **Sentiment Analysis**: TextBlob-based polarity scoring
- **Profanity Detection**: Custom word list with preprocessing
- **Customer Moderation**: Automatic banning after 3+ profane reviews
- **Parameter Store**: SSM for resource name management
- **LocalStack Support**: Full local development environment
- **Comprehensive Testing**: Integration and unit tests

## 📝 Requirements Met

✅ **3+ Lambda Functions**: preprocessing, profanity_check, sentiment_analysis  
✅ **S3 Triggers**: File upload triggers preprocessing  
✅ **DynamoDB Events**: Review updates trigger sentiment analysis  
✅ **SSM Integration**: All resource names from Parameter Store  
✅ **Integration Tests**: Automated pipeline verification  
✅ **Review Fields**: summary, reviewText, overall analysis  
✅ **Customer Banning**: >3 unpolite reviews = banned  

## 🛠️ Development

### Adding New Lambda Functions:
1. Create handler in `src/lambdas/[function_name]/`
2. Use utilities from `src/utils/`
3. Add SSM parameters in setup script
4. Create integration tests

### Modifying Profanity Detection:
Update `PROFANITY_WORDS` set in `src/utils/review_analyzer.py`

### Changing Sentiment Analysis:
Modify `analyze_sentiment()` in `src/utils/sentiment.py`