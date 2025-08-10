from keybert import KeyBERT
from typing import List, Tuple

_kw_model = KeyBERT(model="all-MiniLM-L6-v2")  # compact, fast

def extract_keyphrases(text: str, top_n: int = 25) -> List[Tuple[str, float]]:
    """
    Returns list of (phrase, weight) sorted by weight desc.
    Phrases are lower-cased; weights in [0,1].
    """
    if not text or not text.strip():
        return []
    # KeyBERT returns (phrase, score)
    # Use unigrams, bigrams, trigrams to capture domain phrasing
    candidates = _kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),
        stop_words="english",
        use_mmr=True,       # diversity
        diversity=0.6,
        top_n=top_n
    )
    # normalise phrases
    cleaned = []
    seen = set()
    for p, s in candidates:
        ph = " ".join(p.lower().split())
        if ph and ph not in seen:
            cleaned.append((ph, float(s)))
            seen.add(ph)
    return cleaned
