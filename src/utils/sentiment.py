import re
from .text_preprocessing import (
    lemmatize,            
    _expand as _expand_c  
)

# ----------------------------------------------------------------------
# 1.  Opinion lexicons (store **lemmas** – never inflected forms)
# ----------------------------------------------------------------------
POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "wonderful", "fantastic", "awesome",
    "love", "like", "enjoy", "perfect", "best", "outstanding", "superb", "brilliant",
    "nice", "beautiful", "delicious", "comfortable", "easy", "fast", "quick",
    "helpful", "friendly", "clean", "fresh", "modern", "quality", "value"
}

NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "horrible", "worst",  # "worst" lemmatises to "bad" but kept for safety
    "hate", "disgust", "useless", "garbage", "trash", "crap", "shit",
    "damn", "hell", "fuck", "ass", "bitch",
    "stupid", "idiot", "moron", "dumb",
    "suck", "poor", "cheap", "slow", "difficult", "hard", "pain", "broken",
    "old", "dirty", "ugly", "expensive", "waste", "disappoint", "frustrate"
}

# Tokens that *flip* polarity of any sentiment word they precede (within a 3-token window)
NEGATION_WORDS = {
    "not", "never", "no", "none", "neither", "nor", "cannot",
}

# Tokens that scale the magnitude of the sentiment (kept in raw form, **not** lemmatised)
INTENSIFIERS = {
    "very": 1.5, "really": 1.3, "extremely": 2.0, "quite": 1.2,
    "absolutely": 2.0, "totally": 2.0, "utterly": 2.0,
    "barely": 0.5, "hardly": 0.5, "slightly": 0.5, "somewhat": 0.75,
}

SENTENCE_PUNCT = {".", "!", "?", ";", ":"}

# ----------------------------------------------------------------------
# 2.  Tokeniser (fast, deliberately simple)
# ----------------------------------------------------------------------
_token_re = re.compile(r"[a-zA-Z']+|[.!?;:]")

def _tokenise(text: str):
    """Return a list of raw tokens, keeping sentence punctuation."""
    return _token_re.findall(text.lower())

# ----------------------------------------------------------------------
# 3.  Main analyser
# ----------------------------------------------------------------------
def analyze_sentiment(text: str) -> float:
    """
    Return sentiment polarity in the range [-1 … 1].

    >>> analyze_sentiment("I really don't like this product.")
    -1.0
    """
    if not text:
        return 0.0

    # Step 1: normalise contractions so "can't" → "can not"
    text = _expand_c(text.lower())

    # Step 2: raw tokens + lemmata
    tokens = _tokenise(text)

    # Running totals
    score = 0.0
    seen = 0          # number of sentiment-bearing words (for normalisation)

    for idx, tok in enumerate(tokens):
        # Skip punctuation
        if not tok.isalpha():
            continue

        lemma = lemmatize(tok)

        # Skip if token is not an opinion word
        if lemma not in POSITIVE_WORDS and lemma not in NEGATIVE_WORDS:
            continue

        # ---- Determine base polarity (+1 or −1) ----
        polarity = 1 if lemma in POSITIVE_WORDS else -1

        # ---- Look back up to three tokens for negation & intensifiers ----
        modifier = 1.0
        negated = False

        back_idx = idx - 1
        hops = 0
        while back_idx >= 0 and hops < 3:
            prev = tokens[back_idx]
            if prev in SENTENCE_PUNCT:
                break  # crossed a sentence boundary

            if prev in INTENSIFIERS:
                modifier *= INTENSIFIERS[prev]

            if prev in NEGATION_WORDS:
                negated = True

            back_idx -= 1
            hops += 1

        if negated:
            polarity *= -1

        # Apply modifier
        polarity *= modifier

        score += polarity
        seen  += abs(modifier)   

    if seen == 0:
        return 0.0

    # --- Normalise to [-1, +1] ---
    norm = score / seen
    return max(-1.0, min(1.0, norm))

if __name__ == "__main__":
    print(analyze_sentiment("I love this product!"))


