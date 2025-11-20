import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import numpy as np
import re
import phonenumbers
import ast
import math


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
st.header("📞 Campaign Analysis Dashboard")

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

    col1.metric("Total Leads", total_leads)
    col2.metric("Contacted Leads", contacted_leads)
    col3.metric("Untouched Leads", untouched_leads)


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

        campaign_engagement["answer_rate_%"] = campaign_engagement.apply(
            lambda x: (x["answered_leads"] / x["dialled_leads"] * 100) if x["dialled_leads"] > 0 else 0,
            axis=1
        ).round(1)

        st.subheader("📊 Campaign Engagement Summary")
        st.dataframe(campaign_engagement)

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

    st.subheader("📞 Dialer Calls Summary")
    st.dataframe(dialer_summary)


else:
    st.info("Please upload both CRM and Dialer Excel files to begin analysis.")
