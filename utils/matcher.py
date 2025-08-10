import spacy

# Load NLP model
nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    doc = nlp(text.lower())
    keywords = set()

    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop and token.is_alpha:
            keywords.add(token.lemma_)
    
    return keywords

def compare_keywords(cv_text, jd_text):
    cv_keywords = extract_keywords(cv_text)
    jd_keywords = extract_keywords(jd_text)

    matched = cv_keywords.intersection(jd_keywords)
    missing = jd_keywords - cv_keywords

    match_score = round((len(matched) / len(jd_keywords)) * 100, 2) if jd_keywords else 0

    return {
        "cv_keywords": cv_keywords,
        "jd_keywords": jd_keywords,
        "matched": matched,
        "missing": missing,
        "score": match_score
    }
