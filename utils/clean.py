import re
import spacy
from typing import Tuple

_nlp_clean = spacy.load("en_core_web_sm")

# Basic normalisation
_RE_URL   = re.compile(r"https?://\S+|www\.\S+", re.I)
_RE_EMAIL = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", re.I)
_RE_PHONE = re.compile(r"\+?\d[\d\-\s()]{6,}\d")
_RE_YEAR  = re.compile(r"\b(19|20)\d{2}\b")
_RE_NUM   = re.compile(r"\b\d+(\.\d+)?\b")
_RE_JUNK  = re.compile(r"[•·●■▪➤▶►•\t]")

def _drop_non_alpha_tokens(phrase: str) -> bool:
    return all(tok.isalpha() for tok in phrase.split())

def clean_text_for_skills(text: str, is_jd: bool = False) -> str:
    if not text:
        return ""
    t = text
    t = _RE_URL.sub(" ", t)
    t = _RE_EMAIL.sub(" ", t)
    t = _RE_PHONE.sub(" ", t)
    t = _RE_YEAR.sub(" ", t)
    t = _RE_NUM.sub(" ", t)
    t = _RE_JUNK.sub(" ", t)
    t = t.replace("–", "-").replace("—", "-")
    # Optional: focus JD sections
    if is_jd:
        lower = t.lower()
        # crude section slicing if headings exist
        for h in ["requirements", "responsibilities", "what you'll do", "skills", "about you"]:
            if h in lower:
                t = t[lower.index(h):]
                break
    # NER filter: remove ORG/PERSON/GPE etc
    doc = _nlp_clean(t)
    keep = []
    drop_labels = {"ORG","PERSON","GPE","LOC","DATE","TIME","MONEY","QUANTITY","CARDINAL","ORDINAL","EVENT","NORP","LANGUAGE"}
    for sent in doc.sents:
        # drop sentence if mostly named‑entities
        ents = [e for e in sent.ents if e.label_ in drop_labels]
        if len(ents) and len(" ".join(x.text for x in ents)) > 0.5*len(sent.text):
            continue
        keep.append(sent.text)
    t = " ".join(keep)
    # compact spaces
    t = re.sub(r"\s+", " ", t).strip()
    return t

def is_skillish(phrase: str) -> bool:
    # quick gate: alpha only, length 1–4 words, avoid stoplike heads
    phrase = phrase.strip().lower()
    if not phrase or len(phrase) < 2: return False
    if not _drop_non_alpha_tokens(phrase): return False
    n_words = len(phrase.split())
    if n_words > 4: return False
    bad_heads = {"team","year","years","client","company","project","information","value","life","workplace",
                 "role","people","services","activity","knowledge","organisation"}
    if phrase.split()[0] in bad_heads: return False
    return True
