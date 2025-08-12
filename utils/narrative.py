# utils/narrative.py
from typing import Dict, List

def _top_csv(items: List[str], k: int = 6) -> str:
    return ", ".join(items[:k]) if items else "—"

def recruiter_narrative(results: Dict) -> str:
    """
    Build a short, recruiter‑friendly narrative using the extracted signals.
    """
    score = results.get("score", 0)
    matched = results.get("matched", [])
    missing = results.get("missing", [])
    jd_skills = results.get("jd_skills", [])
    cat = results.get("category_breakdown", {})

    # Find strongest and weakest categories by coverage %
    best_cat = None
    best_pct = -1.0
    weak_cat = None
    weak_pct = 999.0
    for c, d in cat.items():
        pct = (100.0 * d["matched"] / d["jd_total"]) if d["jd_total"] else 0.0
        if pct > best_pct:
            best_pct, best_cat = pct, c
        if pct < weak_pct:
            weak_pct, weak_cat = pct, c

    lines = []
    lines.append(f"This CV aligns at {score:.0f}% with the role requirements.")
    if best_cat is not None:
        lines.append(f"Strong coverage in {best_cat.replace('_',' ')} ({best_pct:.0f}%).")
    if weak_cat is not None and weak_pct < 90:
        lines.append(f"Lower coverage in {weak_cat.replace('_',' ')} ({weak_pct:.0f}%).")

    if matched:
        lines.append(f"Key strengths: {_top_csv(matched, 6)}.")
    if missing:
        lines.append(f"To improve fit, add evidence for: {_top_csv(missing, 5)}.")

    if len(jd_skills) >= 25 and score >= 85:
        lines.append("Overall, this profile is well‑suited; minor additions can push it above 90%.")
    elif score < 70:
        lines.append("Significant gaps remain; focus on core tools and platform coverage mentioned in the JD.")
    return " ".join(lines)
