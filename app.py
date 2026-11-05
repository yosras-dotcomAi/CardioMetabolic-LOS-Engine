"""
CRSS: Cardiometabolic Risk & Hospital Stay Stratifier (Streamlit dashboard)
A planning calculator. The length-of-stay values are ILLUSTRATIVE ASSUMPTIONS,
not clinical evidence, and the tool is not medical advice.
Run locally:  streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from clinical_bmi_engine import CARDIAC_HISTORY_EXTRA_DAYS, TIERS, calculate_bmi, classify_bmi

st.set_page_config(page_title="CRSS: BMI and Hospital Stay Planner", page_icon="🫀", layout="wide")

TIER_NAMES = [t.name for t in TIERS]
TEAL = "#2a9d8f"

st.title("🫀 Cardiometabolic Risk & Hospital Stay Stratifier")
st.warning("**Planning tool, not clinical advice.** The length-of-stay (LOS) values are illustrative "
           "assumptions, not published effect sizes. Replace them with your own hospital's data "
           "before real use. No patient data is used.")

# ---------- Sidebar: editable assumptions ----------
st.sidebar.header("Planning assumptions")
st.sidebar.caption("Change these to test 'what if' scenarios.")
uplift = {}
for t in TIERS:
    uplift[t.name] = st.sidebar.number_input(
        f"{t.name}: extra days", min_value=0.0, max_value=15.0, value=float(t.los_uplift_days),
        step=0.1, key=f"u_{t.name}")
cardiac_days = st.sidebar.number_input(
    "Extra days: BMI 30+ with cardiac history", min_value=0.0, max_value=10.0,
    value=float(CARDIAC_HISTORY_EXTRA_DAYS), step=0.1)


def extra_days(bmi, cardiac):
    tier = classify_bmi(bmi)
    days = uplift[tier.name]
    if cardiac and bmi >= 30.0:
        days += cardiac_days
    return tier, days


tab1, tab2, tab3, tab4 = st.tabs(["Patient calculator", "Scenario planner", "Upload a cohort", "Tiers and method"])

# ---------- Tab 1: single patient ----------
with tab1:
    c1, c2, c3 = st.columns(3)
    weight = c1.number_input("Weight (kg)", 10.0, 500.0, 85.0, 0.5)
    height = c2.number_input("Height (cm)", 50.0, 250.0, 170.0, 0.5)
    cardiac = c3.checkbox("History of cardiac disease")
    bmi = calculate_bmi(weight, height)
    tier, days = extra_days(bmi, cardiac)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("BMI (kg/m²)", f"{bmi:.1f}")
    m2.metric("WHO category", tier.name)
    m3.metric("Resource priority", tier.priority)
    m4.metric("Assumed extra LOS", f"+{days:.1f} days")
    pathway = tier.pathway
    if cardiac and bmi >= 30.0:
        pathway += " plus targeted heart failure and vascular monitoring"
    st.info(f"**Suggested pathway:** {pathway}")
    st.caption(f"Reason for the tier: {tier.reason}.")

# ---------- Tab 2: scenario planner ----------
with tab2:
    st.write("Estimate how many extra bed days a group of admissions could add, "
             "using the assumptions in the sidebar.")
    s1, s2 = st.columns([1, 2])
    admissions = s1.number_input("Admissions per month", 10, 5000, 200, 10)
    cardiac_share = s1.slider("Share with cardiac history (BMI 30+)", 0, 100, 30, 5,
                              help="Applied to patients in the three obesity classes.")
    s2.write("**Mix of BMI categories** (illustrative defaults; edit to match your unit):")
    defaults = [3, 27, 33, 20, 11, 6]
    cols = s2.columns(len(TIERS))
    mix = [cols[i].number_input(TIER_NAMES[i], 0, 100, defaults[i], key=f"mix_{i}")
           for i in range(len(TIERS))]
    total_mix = sum(mix)
    if total_mix == 0:
        st.error("Enter at least one category with a share above zero.")
    else:
        rows = []
        for t, share in zip(TIERS, mix):
            patients = admissions * share / total_mix
            obese = t.lower >= 30.0
            base = patients * uplift[t.name]
            card = patients * (cardiac_share / 100) * cardiac_days if obese else 0.0
            rows.append({"Category": t.name, "Share %": round(100 * share / total_mix, 1),
                         "Patients": round(patients, 1), "Extra bed days": round(base + card, 1)})
        scen = pd.DataFrame(rows)
        total = scen["Extra bed days"].sum()
        k1, k2, k3 = st.columns(3)
        k1.metric("Extra bed days per month", f"{total:,.0f}")
        k2.metric("Per admission", f"{total / admissions:.2f} days")
        k3.metric("Average extra beds occupied", f"{total / 30:.1f}",
                  help="Extra bed days divided by 30 days.")
        fig = px.bar(scen, x="Category", y="Extra bed days", text="Extra bed days",
                     color_discrete_sequence=[TEAL], title="Where the extra bed days come from")
        fig.update_traces(texttemplate="%{text:.0f}")
        fig.update_layout(xaxis_title=None, xaxis_categoryorder="array", xaxis_categoryarray=TIER_NAMES)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(scen, hide_index=True, width="stretch")

# ---------- Tab 3: upload ----------
with tab3:
    st.write("Upload a CSV with two columns: `bmi` and `cardiac_history` (0 or 1). "
             "Use anonymised or simulated data only.")
    template = pd.DataFrame({"bmi": [22.4, 27.1, 31.0, 36.5, 41.2],
                             "cardiac_history": [0, 0, 1, 1, 1]})
    st.download_button("Download a template", template.to_csv(index=False),
                       "cohort_template.csv", "text/csv")
    up = st.file_uploader("Cohort CSV", type="csv")
    if up is not None:
        try:
            data = pd.read_csv(up)
            data["bmi"] = pd.to_numeric(data["bmi"])
            data["cardiac_history"] = data["cardiac_history"].astype(int)
            results = [extra_days(b, bool(c)) for b, c in zip(data["bmi"], data["cardiac_history"])]
            data["WHO category"] = [r[0].name for r in results]
            data["Assumed extra days"] = [round(r[1], 1) for r in results]
            u1, u2, u3 = st.columns(3)
            u1.metric("Patients", len(data))
            u2.metric("Extra bed days", f"{data['Assumed extra days'].sum():.1f}")
            u3.metric("Per patient", f"{data['Assumed extra days'].mean():.2f}")
            by_tier = data.groupby("WHO category").agg(
                Patients=("bmi", "size"), Extra_bed_days=("Assumed extra days", "sum")).reset_index()
            st.dataframe(by_tier, hide_index=True, width="stretch")
            st.dataframe(data, hide_index=True, width="stretch")
        except Exception as exc:  # shows a friendly message for bad files
            st.error(f"Could not read the file. Check the columns and values. ({exc})")

# ---------- Tab 4: tiers ----------
with tab4:
    table = pd.DataFrame({
        "WHO category": [t.name for t in TIERS],
        "BMI from": [t.lower for t in TIERS],
        "BMI below": [None if t.upper == float("inf") else t.upper for t in TIERS],
        "Priority": [t.priority for t in TIERS],
        "Assumed extra days": [uplift[t.name] for t in TIERS],
        "Suggested pathway": [t.pathway for t in TIERS],
    })
    st.dataframe(table, hide_index=True, width="stretch")
    st.markdown(
        "- BMI categories follow the [WHO adult classification]"
        "(https://www.who.int/news-room/fact-sheets/detail/obesity-and-overweight).\n"
        "- Each tier includes its lower limit and excludes its upper limit, so there are no gaps.\n"
        "- LOS values are **assumptions** and can be edited in the sidebar.\n"
        "- This is a planning calculator, not a prediction model. It has not been tested on real outcomes.")
