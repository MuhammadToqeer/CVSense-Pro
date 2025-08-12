# utils/suggestions.py
from typing import Dict, List

TEMPLATES = {
    "data_engineering_core": "Add a bullet under Experience showing {skill} used to build/maintain data pipelines, including orchestration and monitoring.",
    "mlops": "Mention {skill} for experiment tracking/model registry and how it integrated with CI/CD.",
    "cloud_azure": "Include {skill} in a project bullet (ingestion, processing, storage, security).",
    "deep_learning": "Add a quantified achievement using {skill} (e.g., trained CNN improving F1 by X%).",
    "nlp": "Show a use case with {skill} (NER, text classification, RAG) and outcome.",
    "genai_llms": "Add a line about {skill} for LLM apps (prompting, tools, serving).",
    "databases_warehousing_bi": "Include {skill} for reporting/analytics with a performance or cost outcome.",
    "testing_ci_cd_devops": "Note CI/CD with {skill} for model/data pipeline deployments."
}

# Map a skill to a rough category name string from extractor
def _find_cat(skill: str, skills_by_cat: Dict[str, set]) -> str:
    for cat, skills in skills_by_cat.items():
        if skill in skills:
            return cat
    return "general"

def craft_suggestions(results: Dict, skills_by_cat: Dict[str, set], ats_report: Dict) -> List[str]:
    sug: List[str] = []

    # 1) Missing skills -> targeted bullets
    for s in results.get("missing", [])[:10]:  # cap to keep concise
        cat = _find_cat(s, skills_by_cat)
        tmpl = TEMPLATES.get(cat, "Add {skill} with a concrete project/result bullet.")
        sug.append(tmpl.format(skill=s))

    # 2) ATS warnings -> fixes
    for w in ats_report.get("warnings", []):
        if "multi‑column" in w.lower():
            sug.append("Switch to a single-column layout; ATS parsers read top-to-bottom.")
        if "font" in w.lower():
            sug.append("Reduce to 1–2 fonts; use common families (Arial/Calibri).")
        if "tables" in w.lower():
            sug.append("Replace tables with simple bullet points and plain text.")
        if "images" in w.lower():
            sug.append("Remove icons/images; ensure all content is text.")
        if "longer than 2 pages" in w.lower():
            sug.append("Trim to 1–2 pages focusing on recent, relevant work.")
        if "contact info" in w.lower():
            sug.append("Place email and phone in the header in plain text.")
        if "missing key sections" in w.lower():
            sug.append("Ensure Summary, Skills, Experience, Education sections exist as headings.")

    # 3) Reach 90%: if score < 90, suggest adding top missing skills
    score = results.get("score", 0)
    if score < 90 and results.get("missing"):
        top3 = ", ".join(results["missing"][:3])
        sug.append(f"To reach 90%+, add evidence for: {top3}.")

    # de-duplicate, keep order
    seen = set()
    final = []
    for s in sug:
        if s not in seen:
            final.append(s)
            seen.add(s)
    return final
