import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import numpy as np
import re
import phonenumbers
import ast
import math
import plotly.express as px

st.markdown("""
<style>

div.stMetric {
    background: linear-gradient(135deg, #121212 0%, #1e1e1e 100%);
    border: 1px solid #1f6feb;     /* Neon blue border */
    border-radius: 14px;

    padding: 18px 14px;
    margin-bottom: 18px;

    box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.6);

    transition: all 0.25s ease-in-out;
}

/* Hover effect */
div.stMetric:hover {
    transform: translateY(-3px);
    border-color: #58a6ff;         /* Brighter blue on hover */
    box-shadow: 0px 4px 14px rgba(88, 166, 255, 0.35);
}

/* Metric label text */
div.stMetric label {
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #c9d1d9 !important;     /* Soft grey (GitHub Dark text) */
}

/* Metric value text */
div.stMetric > div > div {
    color: #58a6ff !important;     /* Neon blue value */
    font-weight: 800 !important;
    font-size: 22px !important;
}

</style>
""", unsafe_allow_html=True)


# -------------------------------
# Helper Functions
# -------------------------------

def parse_utm(x):
    if pd.isna(x):
        return None
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except:
            return None
    return None

def extract_last_10_digits(num):
    if pd.isna(num):
        return None
    s = str(num)
    digits_only = re.sub(r'\D', '', s)
    if len(digits_only) < 10:
        return None
    return digits_only[-10:]

def classify_status(gr):
    if 'Answered' in gr.values:
        return 'Answered'
    elif 'Missed' in gr.values:
        return 'Missed'
    else:
        return 'None'


# -------------------------------
# Streamlit UI
# -------------------------------
st.header("Campaign Analysis")

crm_file = st.sidebar.file_uploader("Upload CRM user_exports Excel file", type=["xlsx"])
dialer_file = st.sidebar.file_uploader("Upload Dialer export Excel file", type=["xlsx"])

if crm_file and dialer_file:

    # -------------------------------
    # CRM FILE
    # -------------------------------
    df = pd.read_excel(crm_file)
    df.columns = df.columns.str.lower()

    if "utm_hit" in df.columns:
        df["utm_hit"] = df["utm_hit"].apply(parse_utm)
        utm_df = pd.json_normalize(df["utm_hit"]).add_prefix("utm_hit_")
        df_con = pd.concat([df.drop(columns=["utm_hit"]), utm_df], axis=1)
    else:
        df_con = df.copy()

    df_con["cleaned_phone"] = df_con["phone"].apply(extract_last_10_digits)
    df_con["cleaned_phone"] = df_con["cleaned_phone"].astype(str)


    # -------------------------------
    # DIALER FILE
    # -------------------------------
    Dialer = pd.read_excel(dialer_file)
    Dialer.columns = Dialer.columns.str.lower()
    Dialer = Dialer[['customer number', 'account', 'start time', 'queue duration', 'end time', 'call status']]

    Dialer["start time"] = pd.to_datetime(Dialer["start time"])
    Dialer["end time"] = pd.to_datetime(Dialer["end time"])
    Dialer["queue duration"] = pd.to_datetime(Dialer["queue duration"])

    Dialer["answer_duration_sec"] = (Dialer["end time"] - Dialer["start time"]).dt.total_seconds()
    Dialer["queue_sec"] = (
        Dialer["queue duration"].dt.hour * 3600 +
        Dialer["queue duration"].dt.minute * 60 +
        Dialer["queue duration"].dt.second
    )
    Dialer["total_duration_sec"] = Dialer["answer_duration_sec"] + Dialer["queue_sec"]
    Dialer["answer_duration_hms"] = pd.to_timedelta(Dialer["answer_duration_sec"], unit="s").astype(str).str.split().str[0]
    Dialer["total_duration_hms"] = pd.to_timedelta(Dialer["total_duration_sec"], unit="s").astype(str).str.split().str[0]

    Dialer = Dialer.rename(columns={"customer number": "cleaned_phone"})
    Dialer["cleaned_phone"] = Dialer["cleaned_phone"].apply(extract_last_10_digits)
    Dialer["cleaned_phone"] = Dialer["cleaned_phone"].astype(str)


    # -------------------------------
    # MERGE CRM + DIALER
    # -------------------------------
    df_calls = df_con.merge(Dialer, on="cleaned_phone", how="left")
    df_calls["first_name"] = df_calls["full_name"].str.split().str[0]

    df_calls["duration_sec"] = (df_calls["end time"] - df_calls["start time"]).dt.total_seconds()
    df_calls.loc[df_calls["call status"] == "Missed", "duration_sec"] = 0


    # -------------------------------
    # CORRECT CONTACTED / UNTOUCHED LOGIC
    # -------------------------------
    crm_phones = set(df_con["cleaned_phone"].dropna().unique())
    dialled_phones = set(Dialer["cleaned_phone"].dropna().unique())

    contacted_leads = len(crm_phones & dialled_phones)
    untouched_leads = len(crm_phones - dialled_phones)
    total_leads = len(crm_phones)


    # -------------------------------
    # DISPLAY METRICS
    # -------------------------------
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Leads", total_leads)
    with col2:
        st.metric("Contacted Leads", contacted_leads)
    with col3:
        st.metric("Untouched Leads", untouched_leads)



    # -------------------------------
    # CAMPAIGN ENGAGEMENT SUMMARY
    # -------------------------------
    if "utm_hit_utmSource" in df_con.columns and "utm_hit_utmCampaign" in df_con.columns:

        lead_status = (
            df_calls.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign", "cleaned_phone"], dropna=False)["call status"]
            .agg(classify_status)
            .reset_index()
        )

        summary = (
            lead_status
            .groupby(["utm_hit_utmSource", "utm_hit_utmCampaign", "call status"], dropna=False)["cleaned_phone"]
            .nunique()
            .unstack(fill_value=0)
            .reset_index()
        )

        summary = summary.rename(columns={
            "Answered": "answered_leads",
            "Missed": "missed_leads",
            "None": "other_leads"
        })

        summary["dialled_leads"] = summary["answered_leads"] + summary["missed_leads"]

        total_leads_df = (
            df_con.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign"], dropna=False)["cleaned_phone"]
            .nunique()
            .reset_index(name="total_leads")
        )

        campaign_engagement = total_leads_df.merge(summary, on=["utm_hit_utmSource", "utm_hit_utmCampaign"], how="left").fillna(0)
        campaign_engagement["untouched_leads"] = campaign_engagement["total_leads"] - campaign_engagement["dialled_leads"]

        campaign_engagement["contact_rate_%"] = (
            (campaign_engagement["dialled_leads"] / campaign_engagement["total_leads"]) * 100
        ).round(1)

        campaign_engagement["answer_rate"] = campaign_engagement.apply(
                    lambda x: (x["answered_leads"] / x["dialled_leads"] * 100) if x["dialled_leads"] > 0 else 0,
                    axis=1
                ).round(1)
        utm_source_data = (
            campaign_engagement
            .groupby('utm_hit_utmSource', dropna=False)
            .agg(
                total_leads=('total_leads', 'sum'),
                answer_rate=('answer_rate', 'mean')
            )
            .reset_index()
        )


        def style_campaign(df):
            return (
                df.style
                .background_gradient(cmap="Blues", subset=["total_leads"])
                .background_gradient(cmap="Greens", subset=["dialled_leads"])
                .background_gradient(cmap="Oranges", subset=["answered_leads"])
                .background_gradient(cmap="Reds", subset=["missed_leads"])
                .format("{:.1f}", subset=["contact_rate_%", "answer_rate"])
                .set_properties(**{
                    "background-color": "#0e1117",
                    "color": "white",
                    "border-color": "#1f6feb",
                    "border-width": "1px",
                    "border-style": "solid"
                })
                .set_table_styles([
                    {"selector": "th", "props": [
                        ("background-color", "#161b22"),
                        ("color", "white"),
                        ("font-weight", "bold"),
                        ("border-color", "#30363d")
                    ]},
                    {"selector": "tr:hover", "props": [
                        ("background-color", "#1f2936")
                    ]}
                ])
            )
        st.subheader("Campaign Engagement Summary")
        # Donut chart for total leads by UTM Source
        col1, col2 = st.columns([3, 2])

        with col1:
            fig_leads = px.pie(
                utm_source_data,
                names='utm_hit_utmSource',
                values='total_leads',
                hole=0.5,
                title='UTM Source: Total Leads',
                color_discrete_sequence=px.colors.sequential.Blues
            )
            fig_leads.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='white')),
                margin=dict(t=50, b=10, l=10, r=10)
            )
            fig_leads.update_traces(marker=dict(line=dict(color='white', width=2)))
            st.plotly_chart(fig_leads, use_container_width=True)

        with col2:
            fig_answer_rate = px.pie(
                utm_source_data,
                names='utm_hit_utmSource',
                values='answer_rate',
                hole=0.5,
                title='Answer Rate % by UTM Source',
                color_discrete_sequence=px.colors.sequential.Oranges
            )
            fig_answer_rate.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='white')),
                margin=dict(t=50, b=10, l=10, r=10)
            )
            fig_answer_rate.update_traces(marker=dict(line=dict(color='white', width=2)), textinfo='percent+label')
            st.plotly_chart(fig_answer_rate, use_container_width=True)
        st.dataframe(style_campaign(campaign_engagement), use_container_width=True)
    else:
        st.warning("UTM source or campaign columns missing in CRM file.")


    # -------------------------------
    # DIALER SUMMARY TABLE
    # -------------------------------
    dialer_summary = (
        df_calls.groupby(["cleaned_phone", "first_name", "account"])
        .agg(
            answered_calls=("call status", lambda x: (x == "Answered").sum()),
            missed_calls=("call status", lambda x: (x == "Missed").sum()),
            total_duration_sec=("duration_sec", "sum"),
            answered_duration_sec=("duration_sec",
                                   lambda x: x[df_calls.loc[x.index, "call status"] == "Answered"].sum())
        )
        .reset_index()
    )

    dialer_summary["answered_duration_hms"] = pd.to_timedelta(dialer_summary["answered_duration_sec"], unit="s").astype(str)
    dialer_summary["total_duration_hms"] = pd.to_timedelta(dialer_summary["total_duration_sec"], unit="s").astype(str)

    dialer_summary["total_calls"] = dialer_summary["answered_calls"] + dialer_summary["missed_calls"]

    dialer_summary = dialer_summary[
        ["cleaned_phone", "first_name", "account",
         "answered_calls", "missed_calls", "total_calls",
         "answered_duration_hms", "total_duration_hms"]
    ]

    st.subheader("Dialer Calls Summary")
    st.dataframe(dialer_summary)


else:
    st.info("Please upload both CRM and Dialer Excel files to begin analysis.")






















