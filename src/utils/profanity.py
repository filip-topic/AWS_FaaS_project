BAD_WORDS = {
    "bad", "terrible", "awful", "horrible", "worst", "hate", "disgusting",
    "useless", "garbage", "trash", "crap", "shit", "damn", "hell", "fuck",
    "ass", "bitch", "stupid", "idiot", "moron", "dumb", "suck", "sucks"
}

def contains_bad_words(tokens):
    return any(w in BAD_WORDS for w in tokens)

def check_profanity(text):
    """Check if text contains profanity."""
    if not text:
        return False
    
    text_lower = text.lower()
    words = text_lower.split()
    return any(word in BAD_WORDS for word in words) 