#!/usr/bin/env python3
"""
Show Review Analysis Results

This script displays the key findings from the review analysis.
"""

import json
import os

def show_results():
    """Display the analysis results."""
    results_file = "data/analysis_results.json"
    
    if not os.path.exists(results_file):
        print("❌ Analysis results not found. Run 'python run_analysis.py' first.")
        return
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    summary = data['summary']
    banned_customers = data['banned_customers']
    
    print("=" * 60)
    print("📊 REVIEW ANALYSIS SUMMARY")
    print("=" * 60)
    
    # Sentiment breakdown
    print(f"\n🎭 SENTIMENT DISTRIBUTION:")
    total = summary['total_reviews']
    positive = summary['sentiment_counts']['positive']
    neutral = summary['sentiment_counts']['neutral']
    negative = summary['sentiment_counts']['negative']
    
    print(f"   📈 Positive: {positive:,} ({(positive/total*100):.1f}%)")
    print(f"   ➖ Neutral:  {neutral:,} ({(neutral/total*100):.1f}%)")
    print(f"   📉 Negative: {negative:,} ({(negative/total*100):.1f}%)")
    
    # Profanity analysis
    profane = summary['profane_reviews']
    print(f"\n🚫 PROFANITY ANALYSIS:")
    print(f"   Profane Reviews: {profane:,} ({(profane/total*100):.1f}%)")
    
    # Customer analysis
    print(f"\n👥 CUSTOMER ANALYSIS:")
    print(f"   Banned Customers: {len(banned_customers)}")
    
    if banned_customers:
        print(f"\n🚨 BANNED CUSTOMER LIST:")
        for i, customer_id in enumerate(banned_customers, 1):
            print(f"   {i}. {customer_id}")
    
    # Key insights
    print(f"\n💡 KEY INSIGHTS:")
    print(f"   • {(positive/total*100):.1f}% of reviews are positive")
    print(f"   • {(profane/total*100):.1f}% of reviews contain profanity")
    print(f"   • {len(banned_customers)} customers have been banned")
    
    if len(banned_customers) > 0:
        print(f"   • Ban rate: {(len(banned_customers)/total*100):.3f}% of customers")

if __name__ == "__main__":
    show_results() 