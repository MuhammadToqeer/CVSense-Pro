from keybert import KeyBERT
from typing import List, Tuple
from utils.clean import clean_text_for_skills, is_skillish

_kw_model = KeyBERT(model="all-MiniLM-L6-v2")

def extract_keyphrases(text: str, top_n: int = 30, is_jd: bool = False) -> List[Tuple[str, float]]:
    if not text or not text.strip():
        return []
    text = clean_text_for_skills(text, is_jd=is_jd)
    if not text:
        return []
    raw = _kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1,3),
        stop_words="english",
        use_mmr=True, diversity=0.6,
        top_n=top_n*2  # over-generate then filter
    )
    seen, cleaned = set(), []
    for p, s in raw:
        ph = " ".join(p.lower().split())
        if ph in seen: 
            continue
        if is_skillish(ph):
            cleaned.append((ph, float(s)))
            seen.add(ph)
        if len(cleaned) >= top_n:
            break
    return cleaned
