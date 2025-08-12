from typing import List, Tuple, Dict, Set
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import streamlit as st
from sentence_transformers import SentenceTransformer

@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")
_embedder = load_embedder()


def _embed(texts: List[str]) -> np.ndarray:
    return _embedder.encode(texts, normalize_embeddings=True)

def semantic_cover(
    jd_keyphrases: List[Tuple[str, float]],
    cv_keyphrases: List[Tuple[str, float]],
    threshold: float = 0.70
) -> Dict:
    """
    jd_keyphrases: [(phrase, weight)], weight in [0,1] (importance from JD)
    cv_keyphrases: [(phrase, weight)] (weights unused here)
    threshold: cosine similarity to count a JD phrase as covered by CV

    Returns:
      {
        "matched": [(jd_phrase, best_cv_phrase, sim)],
        "missing": [jd_phrase],
        "score": 0..100 (weighted by JD importance)
      }
    """
    if not jd_keyphrases:
        return {"matched": [], "missing": [], "score": 0.0}

    jd_phrases = [p for p, w in jd_keyphrases]
    jd_weights = np.array([w for p, w in jd_keyphrases], dtype=float)
    cv_phrases = [p for p, w in cv_keyphrases] if cv_keyphrases else []

    if not cv_phrases:
        return {"matched": [], "missing": jd_phrases, "score": 0.0}

    E_jd = _embed(jd_phrases)
    E_cv = _embed(cv_phrases)

    S = cosine_similarity(E_jd, E_cv)  # shape: [len(jd), len(cv)]
    best_sim = S.max(axis=1)
    best_idx = S.argmax(axis=1)

    matched = []
    missing = []
    covered = np.zeros_like(jd_weights)

    for i, sim in enumerate(best_sim):
        if sim >= threshold:
            matched.append((jd_phrases[i], cv_phrases[best_idx[i]], float(sim)))
            covered[i] = jd_weights[i]
        else:
            missing.append(jd_phrases[i])

    # weighted coverage score (by JD importance)
    denom = jd_weights.sum()
    score = float(100.0 * covered.sum() / denom) if denom > 0 else 0.0

    return {
        "matched": matched,
        "missing": missing,
        "score": round(score, 2)
    }
