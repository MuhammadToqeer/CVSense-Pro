import json
import os
import re
from typing import Dict, List, Set, Tuple
from rapidfuzz import fuzz

# --------- load skills bank ---------
_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
_BANK_PATH = os.path.join(_REPO_ROOT, "data", "skills_bank.json")

with open(_BANK_PATH, "r", encoding="utf-8") as f:
    _BANK = json.load(f)

_SKILLS_BY_CAT: Dict[str, Set[str]] = {
    cat: {s.lower() for s in skills} for cat, skills in _BANK["skills"].items()
}
_ALL_SKILLS: Set[str] = set().union(*_SKILLS_BY_CAT.values())
_SYNONYMS: Dict[str, str] = {k.lower(): v.lower() for k, v in _BANK.get("synonyms", {}).items()}

# Category weights (tune freely)
_CAT_WEIGHTS: Dict[str, float] = {
    "programming_languages": 1.5,
    "data_frame_and_compute": 1.2,
    "ml_core": 1.8,
    "time_series": 1.6,
    "recommenders": 1.4,
    "deep_learning": 1.8,
    "nlp": 1.6,
    "computer_vision": 1.6,
    "genai_llms": 1.8,
    "mlops": 2.0,
    "data_engineering_core": 2.0,
    "cloud_azure": 2.0,
    "cloud_aws": 1.5,
    "cloud_gcp": 1.5,
    "databases_warehousing_bi": 1.4,
    "data_quality_governance": 1.3,
    "testing_ci_cd_devops": 1.3,
    "metrics_eval": 1.2,
    "security_governance_ops": 1.1,
    "tools_editors": 1.0,
}

# --------- helpers ---------
_WORD_BOUNDARY = r"(?<![A-Za-z0-9]){phrase}(?![A-Za-z0-9])"

def _normalise_text(t: str) -> str:
    if not t:
        return ""
    t = t.lower()
    t = re.sub(r"https?://\S+|www\.\S+", " ", t)
    t = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " ", t)
    t = re.sub(r"\+?\d[\d\-\s()]{6,}\d", " ", t)   # phones
    t = re.sub(r"\b(19|20)\d{2}\b", " ", t)        # years
    t = re.sub(r"[^a-z0-9\-\+\./ ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _canon(term: str) -> str:
    t = term.strip().lower()
    return _SYNONYMS.get(t, t)

# Pre-compile regex patterns for exact phrase hits (skills + synonym keys)
_PATTERNS: List[Tuple[str, re.Pattern]] = []
_seen_for_patterns: Set[str] = set()

def _add_pattern(phrase: str):
    ph = phrase.lower().strip()
    if ph and ph not in _seen_for_patterns:
        patt = re.compile(_WORD_BOUNDARY.format(phrase=re.escape(ph)))
        _PATTERNS.append((ph, patt))
        _seen_for_patterns.add(ph)

for ph in _ALL_SKILLS:
    _add_pattern(ph)
for syn_key in _SYNONYMS.keys():
    _add_pattern(syn_key)

# --------- core extraction ---------
def _exact_phrase_hits(text_norm: str) -> Set[str]:
    hits: Set[str] = set()
    for ph, patt in _PATTERNS:
        if patt.search(text_norm):
            hits.add(_canon(ph))
    return hits

def _fuzzy_boost(text_norm: str, missing: Set[str], threshold: int = 92) -> Set[str]:
    """Very light fuzzy: try to rescue near-misses (e.g., 'ml flow' -> 'mlflow')."""
    if not missing:
        return set()
    # Build simple n-grams up to trigrams from text_norm
    tokens = [t for t in text_norm.split() if t]
    grams: Set[str] = set()
    for n in (1, 2, 3):
        for i in range(len(tokens) - n + 1):
            grams.add(" ".join(tokens[i:i+n]))
    rescued = set()
    for skill in list(missing):
        for g in grams:
            if fuzz.token_set_ratio(skill, g) >= threshold:
                rescued.add(skill)
                break
    return rescued

def extract_skills(text: str) -> Set[str]:
    """
    Returns canonical set of skills found in the text
    (synonyms mapped to canonical terms).
    """
    t = _normalise_text(text)
    if not t:
        return set()
    exact = _exact_phrase_hits(t)
    # Try to rescue common near-misses
    still_missing = (_ALL_SKILLS - exact)
    rescued = _fuzzy_boost(t, still_missing, threshold=92)
    return exact.union(rescued)

def analyse_cv_vs_jd(cv_text: str, jd_text: str) -> Dict:
    cv = extract_skills(cv_text)
    jd = extract_skills(jd_text)

    matched = jd & cv
    missing = jd - cv
    extra   = cv - jd

    # weighted score by JD skill importance per category
    def weight(skill: str) -> float:
        for cat, skills in _SKILLS_BY_CAT.items():
            if skill in skills:
                return _CAT_WEIGHTS.get(cat, 1.0)
        return 1.0

    denom = sum(weight(s) for s in jd) or 1.0
    num   = sum(weight(s) for s in matched)
    score = round(100.0 * num / denom, 2)

    # category breakdown (optional)
    breakdown: Dict[str, Dict[str, int]] = {}
    for cat, skills in _SKILLS_BY_CAT.items():
        j = len(jd & skills)
        m = len(matched & skills)
        if j > 0:
            breakdown[cat] = {"jd_total": j, "matched": m}

    return {
        "score": score,
        "matched": sorted(matched),
        "missing": sorted(missing),
        "extra": sorted(extra),
        "jd_skills": sorted(jd),
        "cv_skills": sorted(cv),
        "category_breakdown": breakdown
    }
