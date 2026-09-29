import os
import json
from datetime import datetime, date
import pandas as pd
import streamlit as st
from classifier import classify_incident, generate_summary
from db import (
    init_db, insert_case, fetch_cases, fetch_case,
    update_case_status, seed_demo_cases
)

st.set_page_config(
    page_title="Cybercrime Incident Classification Portal",
    page_icon="🛡️",
    layout="wide",
)

init_db()

# ---------- Styling ----------
st.markdown("""
<style>
.main-title {
    font-size: 2.1rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}
.subtitle {
    color: #5b6470;
    margin-bottom: 1rem;
}
.badge {
    display: inline-block;
    padding: 0.2rem 0.55rem;
    border-radius: 0.8rem;
    font-size: 0.8rem;
    font-weight: 600;
    background: #eef2ff;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛡️ Cybercrime Incident Classification & Reporting Portal</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">College project demo: classify complaints, generate summaries, store cases, and visualize category statistics.</div>',
    unsafe_allow_html=True
)

st.info(
    "Demo/academic use only. Do not enter real passwords, banking details, identity numbers, or other sensitive personal information."
)

with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Choose a module",
        ["Report Incident", "Dashboard", "Case Tracker", "About Project"],
        index=0
    )
    st.divider()
    api_status = bool(os.getenv("OPENAI_API_KEY"))
    st.write("AI API:", "✅ Configured" if api_status else "⚪ Not configured")
    st.caption("Without an API key, the app uses a local keyword-based fallback classifier and summary generator.")

# ---------- Report Incident ----------
if page == "Report Incident":
    st.subheader("📋 Report a Cybercrime Incident")

    with st.form("incident_form"):
        col1, col2 = st.columns(2)
        with col1:
            reporter_name = st.text_input("Reporter name", placeholder="Demo User")
            contact = st.text_input("Contact (optional)", placeholder="email@example.com")
            incident_date = st.date_input("Incident date", value=date.today())
        with col2:
            severity = st.selectbox("Initial severity", ["Low", "Medium", "High", "Critical"])
            status = st.selectbox("Case status", ["New", "Under Review", "Investigating", "Closed"])

        description = st.text_area(
            "Incident description",
            height=180,
            placeholder=(
                "Example: I received a message claiming to be from my bank. "
                "It asked me to click a link and enter my login details..."
            ),
        )

        submitted = st.form_submit_button("🔎 Classify & Save Incident", use_container_width=True)

    if submitted:
        if not description.strip():
            st.error("Please enter an incident description.")
        else:
            with st.spinner("Classifying incident and preparing summary..."):
                result = classify_incident(description)
                summary = generate_summary(description, result["category"])

            case_id = insert_case({
                "reporter_name": reporter_name.strip() or "Anonymous",
                "contact": contact.strip(),
                "incident_date": incident_date.isoformat(),
                "description": description.strip(),
                "category": result["category"],
                "confidence": float(result["confidence"]),
                "severity": severity,
                "summary": summary,
                "status": status,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

            st.success(f"Incident saved successfully. Case ID: {case_id}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Category", result["category"])
            c2.metric("Confidence", f'{result["confidence"]:.0%}')
            c3.metric("Severity", severity)

            st.write("### AI Incident Summary")
            st.write(summary)

            with st.expander("Classification details"):
                st.write("Reason:", result.get("reason", ""))
                st.write("AI mode:", result.get("mode", "fallback"))

# ---------- Dashboard ----------
elif page == "Dashboard":
    st.subheader("📊 Category Statistics Dashboard")

    df = fetch_cases()

    if df.empty:
        st.warning("No cases yet. Add a demo case from the Report Incident page or load demo data below.")
        if st.button("Load Demo Data"):
            seed_demo_cases()
            st.rerun()
    else:
        total = len(df)
        open_cases = int((df["status"] != "Closed").sum())
        high_risk = int(df["severity"].isin(["High", "Critical"]).sum())

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Cases", total)
        c2.metric("Open Cases", open_cases)
        c3.metric("High/Critical", high_risk)

        st.write("### Cases by Cybercrime Category")
        category_counts = df["category"].value_counts().rename("Cases").to_frame()
        st.bar_chart(category_counts)

        st.write("### Status Distribution")
        status_counts = df["status"].value_counts().rename("Cases").to_frame()
        st.bar_chart(status_counts)

        st.write("### Recent Cases")
        recent = df.sort_values("created_at", ascending=False).head(10).copy()
        st.dataframe(
            recent[
                ["case_id", "created_at", "category", "severity", "status", "confidence"]
            ],
            hide_index=True,
            width="stretch",
        )

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Cases as CSV",
            data=csv,
            file_name="cybercrime_cases.csv",
            mime="text/csv",
        )

# ---------- Case Tracker ----------
elif page == "Case Tracker":
    st.subheader("🗂️ Case Tracker")
    df = fetch_cases()

    if df.empty:
        st.warning("No cases available.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            categories = ["All"] + sorted(df["category"].dropna().unique().tolist())
            selected_category = st.selectbox("Filter by category", categories)
        with col2:
            statuses = ["All"] + sorted(df["status"].dropna().unique().tolist())
            selected_status = st.selectbox("Filter by status", statuses)

        filtered = df.copy()
        if selected_category != "All":
            filtered = filtered[filtered["category"] == selected_category]
        if selected_status != "All":
            filtered = filtered[filtered["status"] == selected_status]

        st.dataframe(
            filtered[
                ["case_id", "created_at", "category", "severity", "status", "confidence"]
            ],
            hide_index=True,
            width="stretch",
        )

        if not filtered.empty:
            chosen_id = st.selectbox("Open case", filtered["case_id"].tolist())
            case = fetch_case(chosen_id)

            st.write("### Case Details")
            a, b = st.columns(2)
            with a:
                st.write(f"**Case ID:** {case['case_id']}")
                st.write(f"**Reporter:** {case['reporter_name']}")
                st.write(f"**Incident date:** {case['incident_date']}")
                st.write(f"**Category:** {case['category']}")
                st.write(f"**Confidence:** {float(case['confidence']):.0%}")
            with b:
                st.write(f"**Severity:** {case['severity']}")
                st.write(f"**Current status:** {case['status']}")
                st.write(f"**Created:** {case['created_at']}")

            st.write("**Incident description**")
            st.write(case["description"])

            st.write("**AI summary**")
            st.write(case["summary"])

            new_status = st.selectbox(
                "Change status",
                ["New", "Under Review", "Investigating", "Closed"],
                index=["New", "Under Review", "Investigating", "Closed"].index(case["status"])
            )

            if st.button("Update Case Status", use_container_width=True):
                update_case_status(chosen_id, new_status)
                st.success("Case status updated.")
                st.rerun()

# ---------- About ----------
else:
    st.subheader("ℹ️ About the Project")
    st.markdown("""
### Project objective
Build an AI-assisted portal that classifies cybercrime complaints, creates concise incident summaries, stores the cases in SQLite, and displays statistics through a Streamlit dashboard.

### Technology stack
- Python
- Streamlit
- OpenAI API
- SQLite
- Pandas

### Example categories
- Phishing / Social Engineering
- Online Financial Fraud
- Identity Theft
- Account Compromise
- Malware / Ransomware
- Cyberbullying / Online Harassment
- Data Breach
- Other

### Important limitation
The classifier is an educational prototype. AI output can be wrong and must not be treated as an official legal classification or an investigative decision.
""")

    st.code("""
Project structure

cybercrime_portal/
├── app.py
├── classifier.py
├── db.py
├── requirements.txt
├── .env.example
└── README.md
""", language="text")
