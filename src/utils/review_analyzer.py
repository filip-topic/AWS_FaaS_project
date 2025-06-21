import json
import sys
import os
from collections import defaultdict, Counter

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.text_preprocessing import preprocess
from utils.profanity import contains_bad_words
from utils.sentiment import analyze_sentiment

def load_reviews(file_path):
    """Load reviews from JSONL file."""
    reviews = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                reviews.append(json.loads(line))
    return reviews

def classify_sentiment(polarity):
    """Classify sentiment based on polarity score."""
    if polarity > 0.1:
        return 'positive'
    elif polarity < -0.1:
        return 'negative'
    else:
        return 'neutral'

def analyze_reviews(reviews):
    """Analyze all reviews and return statistics."""
    stats = {
        'total_reviews': len(reviews),
        'sentiment_counts': Counter(),
        'profane_reviews': 0,
        'customer_profanity_count': defaultdict(int),
        'banned_customers': set(),
        'review_details': []
    }
    
    for review in reviews:
        reviewer_id = review.get('reviewerID', 'unknown')
        review_text = review.get('reviewText', '')
        summary = review.get('summary', '')
        overall = review.get('overall', 0)
        
        # Analyze sentiment
        sentiment_polarity = analyze_sentiment(review_text)
        sentiment_class = classify_sentiment(sentiment_polarity)
        stats['sentiment_counts'][sentiment_class] += 1
        
        # Check for profanity (tokenize before checking)
        tokens_review = preprocess(review_text.lower())
        tokens_summary = preprocess(summary.lower())
        is_profane = contains_bad_words(tokens_review) or contains_bad_words(tokens_summary)
        if is_profane:
            stats['profane_reviews'] += 1
            stats['customer_profanity_count'][reviewer_id] += 1
        
        # Check if customer should be banned (>3 profane reviews)
        if stats['customer_profanity_count'][reviewer_id] > 3:
            stats['banned_customers'].add(reviewer_id)
        
        # Store review details for potential further analysis
        stats['review_details'].append({
            'reviewerID': reviewer_id,
            'sentiment': sentiment_class,
            'polarity': sentiment_polarity,
            'is_profane': is_profane,
            'overall': overall
        })
    
    return stats

def print_analysis(stats):
    """Print formatted analysis results."""
    print("=" * 60)
    print("REVIEW ANALYSIS REPORT")
    print("=" * 60)
    
    # Sentiment analysis
    print(f"\n📊 SENTIMENT ANALYSIS:")
    print(f"   Total Reviews: {stats['total_reviews']}")
    print(f"   Positive Reviews: {stats['sentiment_counts']['positive']}")
    print(f"   Neutral Reviews: {stats['sentiment_counts']['neutral']}")
    print(f"   Negative Reviews: {stats['sentiment_counts']['negative']}")
    
    # Profanity analysis
    print(f"\n🚫 PROFANITY ANALYSIS:")
    print(f"   Profane Reviews: {stats['profane_reviews']}")
    print(f"   Percentage: {(stats['profane_reviews'] / stats['total_reviews'] * 100):.2f}%")
    
    # Customer analysis
    print(f"\n👥 CUSTOMER ANALYSIS:")
    print(f"   Customers with Profane Reviews: {len(stats['customer_profanity_count'])}")
    print(f"   Banned Customers: {len(stats['banned_customers'])}")
    
    if stats['banned_customers']:
        print(f"\n🚨 BANNED CUSTOMERS:")
        for customer_id in sorted(stats['banned_customers']):
            profanity_count = stats['customer_profanity_count'][customer_id]
            print(f"   - {customer_id} ({profanity_count} profane reviews)")
    
    # Top profane customers
    if stats['customer_profanity_count']:
        print(f"\n📈 TOP CUSTOMERS BY PROFANE REVIEWS:")
        top_customers = sorted(stats['customer_profanity_count'].items(), 
                             key=lambda x: x[1], reverse=True)[:5]
        for customer_id, count in top_customers:
            status = "BANNED" if customer_id in stats['banned_customers'] else "Active"
            print(f"   - {customer_id}: {count} profane reviews ({status})")

def main():
    """Main function to run the analysis."""
    file_path = "data/reviews_devset.json"
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found!")
        sys.exit(1)
    
    print("Loading reviews...")
    reviews = load_reviews(file_path)
    print(f"Loaded {len(reviews)} reviews")
    
    print("Analyzing reviews...")
    stats = analyze_reviews(reviews)
    
    print_analysis(stats)
    
    # Save detailed results to file
    output_file = "data/analysis_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_reviews': stats['total_reviews'],
                'sentiment_counts': dict(stats['sentiment_counts']),
                'profane_reviews': stats['profane_reviews'],
                'banned_customers_count': len(stats['banned_customers'])
            },
            'banned_customers': list(stats['banned_customers']),
            'customer_profanity_counts': dict(stats['customer_profanity_count'])
        }, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main() 