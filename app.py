import streamlit as st
from utils.pdf_reader import extract_text_from_pdf
from utils.matcher import compare_keywords
from utils.keywords import extract_keyphrases
from utils.semantic import semantic_cover
from utils.skill_extractor import analyse_cv_vs_jd
from utils.ats_check import ats_audit
from utils.skill_extractor import _SKILLS_BY_CAT  # just for suggestions mapping
from utils.suggestions import craft_suggestions




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

        # --- Semantic keyphrase matching (dynamic, domain-agnostic) ---
        if cv_text.strip() and jd_text.strip():
            results = analyse_cv_vs_jd(cv_text, jd_text)

            st.subheader("Match Results (ATS-style)")
            st.write(f"Match Score: {results['score']}%")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("JD Skills", len(results["jd_skills"]))
            with col2:
                st.metric("Matched", len(results["matched"]))
            with col3:
                st.metric("Missing", len(results["missing"]))

            with st.expander("Matched Skills"):
                st.write(", ".join(results["matched"]) or "None")

            with st.expander("Missing Skills (consider adding if you have them)"):
                st.write(", ".join(results["missing"]) or "None")

            with st.expander("Extra Skills in CV (not in JD)"):
                st.write(", ".join(results["extra"]) or "None")

            with st.expander("Detected JD Skills"):
                st.write(", ".join(results["jd_skills"]) or "None")

            with st.expander("Category Coverage"):
                rows = []
                for cat, d in results["category_breakdown"].items():
                    rows.append(f"{cat}: {d['matched']}/{d['jd_total']}")
                st.write("\n".join(rows) if rows else "No JD skills detected")
        else:
            st.warning("Please upload both CV and JD before analysis.")

                # ATS audit of the uploaded CV PDF
        ats = ats_audit(uploaded_cv)

        st.subheader("ATS Checks")
        cols = st.columns(4)
        cols[0].metric("Pages", ats["pages"])
        cols[1].metric("Tables", ats["tables"])
        cols[2].metric("Images", ats["images"])
        cols[3].metric("Font families", ats["font_families"])

        with st.expander("Warnings"):
            if ats["warnings"]:
                st.write("\n".join(f"- {w}" for w in ats["warnings"]))
            else:
                st.write("No major ATS issues detected.")

        # Actionable suggestions
        st.subheader("Suggestions")
        suggestions = craft_suggestions(results, _SKILLS_BY_CAT, ats)
        if suggestions:
            st.write("\n".join(f"- {s}" for s in suggestions))
        else:
            st.write("Looks solid. Minor polishing only.")

        # Export a simple Markdown report
        report_md = []
        report_md.append(f"# CVSense Pro Report\n")
        report_md.append(f"**Score:** {results['score']}%\n")
        report_md.append("## Matched Skills\n" + ", ".join(results["matched"]) + "\n")
        report_md.append("## Missing Skills\n" + (", ".join(results["missing"]) or "None") + "\n")
        report_md.append("## Extra Skills\n" + (", ".join(results["extra"]) or "None") + "\n")
        report_md.append("## ATS Warnings\n" + ("\n".join(f"- {w}" for w in ats["warnings"]) or "None") + "\n")
        report_md.append("## Suggestions\n" + ("\n".join(f"- {s}" for s in suggestions) or "None") + "\n")
        md_text = "\n".join(report_md)

        st.download_button(
            label="Download Report (Markdown)",
            data=md_text,
            file_name="cvsense_report.md",
            mime="text/markdown"
        )

