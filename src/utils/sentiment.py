# Simple sentiment analysis using keyword matching
POSITIVE_WORDS = {
    'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
    'love', 'like', 'enjoy', 'perfect', 'best', 'outstanding', 'superb', 'brilliant',
    'nice', 'beautiful', 'delicious', 'comfortable', 'easy', 'fast', 'quick',
    'helpful', 'friendly', 'clean', 'fresh', 'new', 'modern', 'quality', 'value'
}

NEGATIVE_WORDS = {
    'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'disgusting',
    'useless', 'garbage', 'trash', 'crap', 'shit', 'damn', 'hell', 'fuck',
    'ass', 'bitch', 'stupid', 'idiot', 'moron', 'dumb', 'suck', 'sucks',
    'poor', 'cheap', 'slow', 'difficult', 'hard', 'painful', 'broken', 'old',
    'dirty', 'ugly', 'expensive', 'waste', 'disappointing', 'frustrating'
}

def analyze_sentiment(text):
    """Return sentiment polarity: >0 positive, <0 negative, 0 neutral."""
    if not text:
        return 0.0
    
    text_lower = text.lower()
    words = text_lower.split()
    
    positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
    negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)
    
    # Calculate sentiment score
    total_words = len(words)
    if total_words == 0:
        return 0.0
    
    # Normalize by text length and return score between -1 and 1
    sentiment = (positive_count - negative_count) / max(total_words, 1)
    
    # Clamp to [-1, 1] range
    return max(-1.0, min(1.0, sentiment)) 