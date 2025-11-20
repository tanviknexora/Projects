import streamlit as st
import pandas as pd
import numpy as np
import re
import phonenumbers
import ast
import math

# Define your original functions here: parse_utm, smart_parse, extract_last_10_digits, classify_status

st.title("Call Campaign Data Analysis App")

# Upload CRM data file
crm_file = st.sidebar.file_uploader("Upload CRM user_exports Excel file", type=["xlsx"])
# Upload Dialer data file
dialer_file = st.sidebar.file_uploader("Upload Dialer export Excel file", type=["xlsx"])

if crm_file and dialer_file:
    df = pd.read_excel(crm_file)
    df.columns = df.columns.str.lower()

    if "utm_hit" in df.columns:
        df["utm_hit"] = df["utm_hit"].apply(parse_utm)
        utm_df = pd.json_normalize(df["utm_hit"]).add_prefix("utm_hit_")
        df_con = pd.concat([df.drop(columns=["utm_hit"]), utm_df], axis=1)
    else:
        df_con = df.copy()

    df_con["cleaned_phone"] = df_con["phone"].apply(extract_last_10_digits).astype(str)

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
    Dialer["answer_duration_hms"] = pd.to_timedelta(Dialer["answer_duration_sec"], unit="s").apply(lambda x: str(x).split(".")[0])
    Dialer["total_duration_hms"] = pd.to_timedelta(Dialer["total_duration_sec"], unit="s").apply(lambda x: str(x).split(".")[0])
    Dialer = Dialer.rename(columns={'customer number': 'cleaned_phone'})
    Dialer["cleaned_phone"] = Dialer["cleaned_phone"].apply(extract_last_10_digits).astype(str)

    df_calls = df_con.merge(Dialer, on="cleaned_phone", how="left")
    df_calls["first_name"] = df_calls["full_name"].str.split().str[0]

    df_calls["duration_sec"] = (df_calls["end time"] - df_calls["start time"]).dt.total_seconds()
    df_calls.loc[df_calls["call status"] == "Missed", "duration_sec"] = 0
    df_calls["contacted"] = ~df_calls["call status"].isna()
    df_calls["untouched"] = df_calls["call status"].isna()

    # Show basic summary
    total_leads = len(df_con)
    contacted_phones = df_calls["contacted"].sum()
    untouched_phones = df_calls["untouched"].sum()

    st.write(f"Total Leads: {total_leads}")
    st.write(f"Contacted Leads: {contacted_phones}")
    st.write(f"Untouched Leads: {untouched_phones}")

    # Show campaign engagement summary table
    # (Include your grouping and summary logic here, then use st.dataframe)
    # Example:
    campaign_engagement = ... # Your final campaign_engagement DataFrame from script

    st.subheader("Campaign Engagement Summary")
    st.dataframe(campaign_engagement)

    # Optionally, add charts or other visualizations

else:
    st.info("Please upload both CRM and Dialer Excel files to proceed.")
