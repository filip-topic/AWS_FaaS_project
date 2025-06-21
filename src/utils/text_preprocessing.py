import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.data.path.append("/tmp")
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', download_dir="/tmp")
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', download_dir="/tmp")
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', download_dir="/tmp")

lemmatizer = WordNetLemmatizer()
stops = set(stopwords.words("english"))

def preprocess(text):
    """Preprocess text: tokenize, remove stopwords, lemmatize."""
    if not text:
        return []
    
    try:
        # Use simple word tokenization to avoid punkt_tab issues
        tokens = text.split()
        # Filter for alphabetic words and convert to lowercase
        tokens = [word.lower() for word in tokens if word.isalpha()]
        # Remove stopwords and lemmatize
        return [lemmatizer.lemmatize(w) for w in tokens if w not in stops]
    except Exception as e:
        print(f"Warning: Error preprocessing text: {e}")
        return [] 