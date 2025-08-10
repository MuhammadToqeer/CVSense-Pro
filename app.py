import streamlit as st
from utils.pdf_reader import extract_text_from_pdf
from utils.matcher import compare_keywords

# Page config
st.set_page_config(page_title="CVSense Pro", layout="centered")

# Title and intro
st.title("CVSense Pro")
st.subheader("AI-powered Resume & Job Description Matcher")
st.info("App is up and running. More features coming soon...")

# CV Upload
uploaded_cv = st.file_uploader("Upload your CV (PDF)", type=["pdf"])

# JD Upload + Text Input
st.write("Upload the Job Description (PDF or TXT) or paste it below:")

jd_input_mode = st.radio(
    "How would you like to provide the Job Description?",
    ("Upload File", "Paste Text")
)

uploaded_jd = None
jd_text_input = ""

if jd_input_mode == "Upload File":
    uploaded_jd = st.file_uploader("Upload JD (PDF/TXT)", type=["pdf", "txt"])
else:
    jd_text_input = st.text_area("Paste Job Description Here", height=200)


# Extract CV Text
cv_text = ""
if uploaded_cv:
    try:
        cv_text = extract_text_from_pdf(uploaded_cv)
    except Exception as e:
        st.error(f"Error reading CV: {e}")

# Extract JD Text
jd_text = ""
if uploaded_jd:
    try:
        if uploaded_jd.name.endswith(".pdf"):
            jd_text = extract_text_from_pdf(uploaded_jd)
        else:
            jd_text = uploaded_jd.read().decode("utf-8")
    except Exception as e:
        st.error(f"Error reading JD: {e}")
elif jd_text_input:
    jd_text = jd_text_input

# Analyse button
if uploaded_cv and (uploaded_jd or jd_text_input):
    if st.button("Analyse Compatibility"):
        st.success("Files ready for processing")
        st.subheader("Preview Extracted Content")

        with st.expander("CV Text"):
            st.write(cv_text[:1000] + "..." if len(cv_text) > 1000 else cv_text)

        with st.expander("Job Description Text"):
            st.write(jd_text[:1000] + "..." if len(jd_text) > 1000 else jd_text)

        # --- Matching logic and results ---
        if cv_text.strip() and jd_text.strip():
            results = compare_keywords(cv_text, jd_text)

            st.subheader("Match Results")
            st.write(f"Match Score: {results['score']}%")

            with st.expander("Matched Keywords"):
                st.write(", ".join(sorted(results['matched'])) if results['matched'] else "None")

            with st.expander("Missing Keywords from CV"):
                st.write(", ".join(sorted(results['missing'])) if results['missing'] else "None")
        else:
            st.warning("Please upload both CV and JD before analysis.")

