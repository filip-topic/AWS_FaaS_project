import re

# Simple stopwords list (most common English stopwords)
STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 
    'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'will', 'with',
    'i', 'you', 'your', 'we', 'they', 'them', 'this', 'these', 'those', 'but', 'or',
    'if', 'then', 'else', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each',
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
    'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now'
}

def preprocess(text):
    """Preprocess text: tokenize, remove stopwords, lemmatize (simplified)."""
    if not text:
        return []
    
    try:
        # Convert to lowercase and split into words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # Remove stopwords and short words
        filtered_words = [word for word in words if word not in STOPWORDS and len(word) > 2]
        
        # Simple lemmatization (remove common suffixes)
        lemmatized = []
        for word in filtered_words:
            # Remove common suffixes
            if word.endswith('ing'):
                word = word[:-3]
            elif word.endswith('ed'):
                word = word[:-2]
            elif word.endswith('s'):
                word = word[:-1]
            elif word.endswith('ly'):
                word = word[:-2]
            
            if len(word) > 2:  # Keep only words with meaningful length
                lemmatized.append(word)
        
        return lemmatized
    except Exception as e:
        print(f"Warning: Error preprocessing text: {e}")
        return [] 