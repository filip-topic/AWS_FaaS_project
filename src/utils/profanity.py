BAD_WORDS = {
    "bad", "terrible", "awful", "horrible", "worst", "hate", "disgusting",
    "useless", "garbage", "trash", "crap", "shit", "damn", "hell", "fuck",
    "ass", "bitch", "stupid", "idiot", "moron", "dumb", "suck", "sucks"
}

def contains_bad_words(tokens):
    return any(w in BAD_WORDS for w in tokens) 