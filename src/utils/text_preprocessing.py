import os
import re


# 1. Stop-words
STOPWORDS = set()

# Try multiple possible paths for stopwords.txt
possible_paths = [
    # Development path (from src/utils/)
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "stopwords.txt"),
    # Lambda path (if data is included in the package)
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "stopwords.txt"),
    # Direct path (if data is in the same directory as utils)
    os.path.join(os.path.dirname(__file__), "..", "data", "stopwords.txt"),
]

stopwords_loaded = False
for stopwords_path in possible_paths:
    try:
        with open(stopwords_path, encoding="utf-8") as fh:
            STOPWORDS |= {w.strip().lower() for w in fh if w.strip()}
        print(f"[INFO] Successfully loaded stopwords from: {stopwords_path}")
        stopwords_loaded = True
        break
    except Exception as exc:
        continue

if not stopwords_loaded:
    print(f"[WARN] Could not load stopwords from any of the attempted paths: {possible_paths}")
    # Fallback: use a minimal set of common stopwords
    STOPWORDS = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "her", "its", "our", "their", "mine", "yours", "hers", "ours", "theirs"}


# 2. Contractions
CONTRACTIONS = {
    "aren't": "are not", "can't": "can not", "couldn't": "could not",
    "didn't": "did not", "doesn't": "does not", "don't": "do not",
    "hadn't": "had not", "hasn't": "has not", "haven't": "have not",
    "he's": "he is", "i'm": "i am", "isn't": "is not", "it's": "it is",
    "let's": "let us", "mightn't": "might not", "mustn't": "must not",
    "shan't": "shall not", "she's": "she is", "shouldn't": "should not",
    "that's": "that is", "there's": "there is", "they're": "they are",
    "wasn't": "was not", "we're": "we are", "weren't": "were not",
    "what's": "what is", "who's": "who is", "won't": "will not",
    "wouldn't": "would not", "you'd": "you would", "you're": "you are",
    "you've": "you have",
}
_CONTRACTION_RE = re.compile(r"\b(" + "|".join(map(re.escape, CONTRACTIONS)) + r")\b")

def _expand(text: str) -> str:
    """Expand contracted forms in *text*."""
    return _CONTRACTION_RE.sub(lambda m: CONTRACTIONS[m.group(0)], text)



# 3. Irregular lemmas  (forms → lemma)
IRREGULARS = {
    # --- verbs
    "am": "be", "is": "be", "are": "be", "was": "be", "were": "be",
    "been": "be", "being": "be",
    "has": "have", "had": "have", "having": "have",
    "does": "do", "did": "do", "done": "do", "doing": "do",
    "goes": "go", "went": "go", "gone": "go",
    "makes": "make", "made": "make",
    "says": "say", "said": "say",
    "gets": "get", "got": "get", "gotten": "get",
    "knows": "know", "knew": "know", "known": "know",
    "thinks": "think", "thought": "think",
    "takes": "take", "took": "take", "taken": "take",
    "sees": "see", "saw": "see", "seen": "see",
    "comes": "come", "came": "come",
    "puts": "put", "put": "put",
    "runs": "run", "ran": "run",
    "sends": "send", "sent": "send",
    "says": "say", "said": "say",
    # modal / auxiliary
    "can't": "can", "cannot": "can", "could": "can",
    "won't": "will", "would": "will",
    "shan't": "shall", "should": "shall",
    "might": "may",
    # --- nouns     
    "children": "child", "men": "man", "women": "woman",
    "people": "person", "mice": "mouse", "geese": "goose",
    "feet": "foot", "teeth": "tooth", "data": "datum",
    # --- adjectives
    "better": "good", "best": "good",
    "worse": "bad", "worst": "bad",
}

# You can grow this list as you meet more edge-cases in your data.



# 4. Simple rule-based lemmatiser

_consonants = set("bcdfghjklmnpqrstvwxyz")

def _undouble(word: str) -> str:
    """Drop a final doubled consonant (running → run)."""
    if len(word) >= 4 and word[-1] == word[-2] and word[-1] in _consonants:
        return word[:-1]
    return word

def _lemmatize_regular(word: str) -> str:
    """Suffix-stripping rules (nouns, verbs, adjectives, adverbs)."""
    w = word

    # --- verbs ---
    if w.endswith("ing") and len(w) > 5:
        w = _undouble(w[:-3])
    elif w.endswith("ed") and len(w) > 4:
        w = _undouble(w[:-2])
        # studied → study
        if w.endswith("i"):
            w = w[:-1] + "y"

    # --- nouns plural ---
    elif w.endswith("ies") and len(w) > 4:             # parties → party
        w = w[:-3] + "y"
    elif w.endswith("ves") and len(w) > 4:             # wolves → wolf
        w = w[:-3] + "f"
    elif w.endswith("ses") and len(w) > 4:             # classes → class
        w = w[:-2]
    elif w.endswith("s") and len(w) > 3 and w[-2] != "s":
        w = w[:-1]

    # --- adjectives / adverbs ---
    if w.endswith("ly") and len(w) > 4:                # quickly → quick
        w = w[:-2]
    elif w.endswith("er") and len(w) > 4:              # smaller → small
        w = w[:-2]
    elif w.endswith("est") and len(w) > 5:             # smallest → small
        w = w[:-3]

    return w

def lemmatize(word: str) -> str:
    """Return the lemma of *word*."""
    # 1. irregulars (fast path)
    if word in IRREGULARS:
        return IRREGULARS[word]

    # 2. regular suffix stripping
    return _lemmatize_regular(word)



# 5. Preprocess pipeline

_token_re = re.compile(r"\b[a-zA-Z]+\b")

def preprocess(text: str):
    """
    1. lowercase
    2. expand contractions ("don't" → "do not")
    3. tokenize         (alpha tokens only)
    4. lemmatise
    5. remove stop-words & tokens shorter than 3 chars
    Returns a list of lemmata.
    """
    if not text:
        return []

    # lower + expand
    text = _expand(text.lower())

    # tokenize
    tokens = _token_re.findall(text)

    # lemmatise + filter
    out = []
    for tok in tokens:
        lemma = lemmatize(tok)
        if len(lemma) >= 3 and lemma not in STOPWORDS:
            out.append(lemma)

    return out


