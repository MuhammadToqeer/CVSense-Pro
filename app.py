import streamlit as st
from utils.pdf_reader import extract_text_from_pdf
from utils.skill_extractor import analyse_cv_vs_jd
from utils.ats_check import ats_audit
from utils.skill_extractor import _SKILLS_BY_CAT  # just for suggestions mapping
from utils.suggestions import craft_suggestions
from utils.parser_preview import pdf_text_preview
from utils.narrative import recruiter_narrative
from utils.skill_extractor import analyse_cv_vs_jd, _SKILLS_BY_CAT
from utils.suggestions import craft_suggestions
from utils.ats_check import ats_audit


def top_missing_for_target(results: dict, target: float = 90.0, max_items: int = 5):
    score = results.get("score", 0.0)
    if score >= target or not results.get("missing"):
        return []
    return results["missing"][:max_items]



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
            # 1) Skills analysis (ATS-style)
            results = analyse_cv_vs_jd(cv_text, jd_text)

            st.subheader("Match Results (ATS-style)")
            st.write(f"Match Score: {results['score']}%")

            c1, c2, c3 = st.columns(3)
            with c1: st.metric("JD Skills", len(results["jd_skills"]))
            with c2: st.metric("Matched", len(results["matched"]))
            with c3: st.metric("Missing", len(results["missing"]))

            # Category coverage table
            st.subheader("Category Coverage")
            rows = []
            for cat, d in results["category_breakdown"].items():
                pct = round(100.0 * d["matched"] / d["jd_total"], 1) if d["jd_total"] else 0.0
                rows.append(f"- {cat.replace('_',' ')}: {d['matched']}/{d['jd_total']}  ({pct}%)")
            if rows:
                st.write("\n".join(rows))
            else:
                st.write("No JD skills detected in known categories.")

            # Recruiter narrative
            st.subheader("Narrative Summary")
            st.write(recruiter_narrative(results))

            # Target to reach 90%
            target_list = top_missing_for_target(results, target=90.0, max_items=5)
            if target_list:
                st.info("Add evidence for these to reach ~90%:")
                st.write(", ".join(target_list))

            with st.expander("Matched Skills"):
                st.write(", ".join(results["matched"]) or "None")
            with st.expander("Missing Skills (consider adding if you have them)"):
                st.write(", ".join(results["missing"]) or "None")
            with st.expander("Extra Skills in CV (not in JD)"):
                st.write(", ".join(results["extra"]) or "None")
            with st.expander("Detected JD Skills"):
                st.write(", ".join(results["jd_skills"]) or "None")

            # 2) ATS checks (document)
            ats = ats_audit(uploaded_cv)
            st.subheader("ATS Checks")
            cc = st.columns(4)
            cc[0].metric("Pages", ats["pages"])
            cc[1].metric("Tables", ats["tables"])
            cc[2].metric("Images", ats["images"])
            cc[3].metric("Font families", ats["font_families"])
            with st.expander("Warnings"):
                if ats["warnings"]:
                    st.write("\n".join(f"- {w}" for w in ats["warnings"]))
                else:
                    st.write("No major ATS issues detected.")

            # 3) Suggestions (skills + ATS fixes)
            st.subheader("Suggestions")
            suggestions = craft_suggestions(results, _SKILLS_BY_CAT, ats)
            if suggestions:
                st.write("\n".join(f"- {s}" for s in suggestions))
            else:
                st.write("Looks solid. Minor polishing only.")

            # 4) ATS parsing simulation preview
            st.subheader("ATS Parse Preview (Text)")
            st.caption("This is roughly what a basic ATS parser might read from your PDF.")
            preview_txt = pdf_text_preview(uploaded_cv, max_chars=2500)
            with st.expander("Show parsed text"):
                st.write(preview_txt or "No text extracted.")

            # 5) Download report
            report_md = []
            report_md.append(f"# CVSense Pro Report\n")
            report_md.append(f"**Score:** {results['score']}%\n")
            report_md.append("## Category Coverage\n")
            for cat, d in results["category_breakdown"].items():
                pct = round(100.0 * d["matched"] / d["jd_total"], 1) if d["jd_total"] else 0.0
                report_md.append(f"- {cat.replace('_',' ')}: {d['matched']}/{d['jd_total']} ({pct}%)")
            report_md.append("\n## Matched Skills\n" + (", ".join(results["matched"]) or "None"))
            report_md.append("\n## Missing Skills\n" + (", ".join(results["missing"]) or "None"))
            report_md.append("\n## Extra Skills\n" + (", ".join(results["extra"]) or "None"))
            report_md.append("\n## ATS Warnings\n" + ("\n".join(f"- {w}" for w in ats["warnings"]) or "None"))
            report_md.append("\n## Narrative\n" + recruiter_narrative(results))
            md_text = "\n".join(report_md)

            st.download_button(
                label="Download Report (Markdown)",
                data=md_text,
                file_name="cvsense_report.md",
                mime="text/markdown"
            )

