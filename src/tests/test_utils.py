import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.text_preprocessing import preprocess
from utils.sentiment import analyze_sentiment

def test_text_preprocessing():
    """Test text preprocessing functionality."""
    text = "This is a great product! I really love it."
    result = preprocess(text)
    
    # Should return a list of tokens
    assert isinstance(result, list)
    
    # Should remove stopwords
    assert "is" not in result
    assert "a" not in result
    
    # Should lemmatize
    assert "great" in result
    assert "love" in result
    
    # Should be lowercase
    assert all(word.islower() for word in result)

def test_sentiment_analysis():
    """Test sentiment analysis functionality."""
    # Test positive sentiment
    positive_text = "This is a great product! I love it."
    positive_sentiment = analyze_sentiment(positive_text)
    assert positive_sentiment > 0
    
    # Test negative sentiment
    negative_text = "This is terrible. I hate it."
    negative_sentiment = analyze_sentiment(negative_text)
    assert negative_sentiment < 0
    
    # Test neutral sentiment
    neutral_text = "This is a product."
    neutral_sentiment = analyze_sentiment(neutral_text)
    assert abs(neutral_sentiment) < 0.1

def test_preprocessing_empty_text():
    """Test preprocessing with empty text."""
    result = preprocess("")
    assert result == []
    
    result = preprocess("   ")
    assert result == []

def test_sentiment_empty_text():
    """Test sentiment analysis with empty text."""
    result = analyze_sentiment("")
    assert result == 0.0 