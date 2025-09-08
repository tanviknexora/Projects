import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from pandas import json_normalize
import ast
import re

# =========================
# Helper functions
# =========================
def parse_utm(x):
    if pd.isna(x):
        return None
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except Exception:
            return None
    return None

sorted_prefixes = sorted(CALLING_CODE_TO_ISO.keys(), key=lambda x: -len(x))

def detect_region(num):
    num = str(num).lstrip("+")
    for prefix in sorted_prefixes:
        if num.startswith(prefix):
            return CALLING_CODE_TO_ISO[prefix]
    return None

def smart_parse(num):
    s = str(num).strip()
    if not s:
        return None
    if not s.startswith("+"):
        s = "+" + s
    try:
        parsed = phonenumbers.parse(s, None)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            ).replace("+", "")
    except:
        return None
    return None


# =========================
# Streamlit UI
# =========================
st.set_page_config(page_title="Call & CRM Analysis", layout="wide")
st.title("📞 Call & CRM Connectivity Dashboard")

# Upload files
crm_file = st.file_uploader("Upload CRM Excel (user_exports...)", type=["xlsx"])
dialer_file = st.file_uploader("Upload Dialer Log Excel", type=["xlsx"])

if crm_file and dialer_file:
    # Read CRM data
    df = pd.read_excel(crm_file)
    df.columns = df.columns.astype(str).str.lower()
    
    # Parse UTM field
    if "utm_hit" in df.columns:
        df["utm_hit"] = df["utm_hit"].apply(parse_utm)
        utm_df = pd.json_normalize(df["utm_hit"]).add_prefix("utm_hit_")
        df = pd.concat([df.drop(columns=["utm_hit"]), utm_df], axis=1)

    # Read Dialer data
    dialer = pd.read_excel(dialer_file)
    dialer.columns = dialer.columns.astype(str).str.lower()
    dialer = dialer[['customer number','start time','end time','call status']]
    
    # Clean numbers
    df["cleaned_phone"] = df["phone"].apply(smart_parse)
    dialer["cleaned_phone"] = dialer["customer number"].apply(smart_parse)

    # Merge
    df_calls = df.merge(dialer.drop(columns=["customer number"]), 
                        on="cleaned_phone", how="left")
    df_calls["first_name"] = df_calls["full_name"].str.split().str[0]

    # =========================
    # Analysis
    # =========================
    st.subheader("Dialer Summary by Contact")
    dialer_summary = (
        df_calls.groupby(["cleaned_phone", "first_name", "call status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"Answered": "answered_calls", "Missed": "missed_calls"})
    )
    st.dataframe(dialer_summary)

    st.subheader("Campaign Summary (Source + Campaign)")
    campaign_summary = (
        df_calls.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign", 
                          "cleaned_phone", "first_name", "call status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"Answered": "answered_calls", "Missed": "missed_calls"})
    )
    st.dataframe(campaign_summary)

    st.subheader("Connectivity Rate by Source")
    source_connectivity = (
        df_calls.groupby(["utm_hit_utmSource", "call status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"Answered": "answered_calls", "Missed": "missed_calls"})
    )
    source_connectivity["total_calls"] = (
        source_connectivity["answered_calls"] + source_connectivity["missed_calls"]
    )
    source_connectivity["connectivity_rate"] = (
        source_connectivity["answered_calls"] / source_connectivity["total_calls"]
    ).round(2)
    st.dataframe(source_connectivity)

    # =========================
    # Optional charts
    # =========================
    st.subheader("📊 Connectivity Rate by Source (Chart)")
    st.bar_chart(source_connectivity.set_index("utm_hit_utmSource")["connectivity_rate"])

