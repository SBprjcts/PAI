from sklearn.feature_extraction.text import HashingVectorizer

def build_vectorizer() -> HashingVectorizer:
     """Create a stateless text vectorizer that works for streaming/online learning."""
     return HashingVectorizer(
        n_features = 2**20,  # Large feature space to reduce collisions
        alternate_sign=False, # Keeps the output non-negative for better interpretability
        ngram_range=(1, 2), # Uses unigrams and bigrams for better context capture
        norm="l2" # Normalizes the output to unit length for consistent scaling
     )
