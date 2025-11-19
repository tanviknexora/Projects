import streamlit as st
import pandas as pd
import ast
import re

# Parse UTM field from string/dict
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

# Extract last 10 digits from a string, return None if less than 10 digits
def extract_last_10_digits(num):
    if pd.isna(num):
        return None
    s = str(num)
    digits_only = re.sub(r'\D', '', s)  # Remove non-digit chars
    if len(digits_only) < 10:
        return None
    return digits_only[-10:]  # Last 10 digits

st.set_page_config(page_title="Call & CRM Dashboard", layout="wide")
st.title("📞 Call & CRM Analysis")

crm_file = st.file_uploader("Upload CRM file", type=["xlsx"])
dialer_file = st.file_uploader("Upload Dialer file", type=["xlsx"])

if crm_file and dialer_file:
    # Load CRM and parse UTM hit if present
    df_crm = pd.read_excel(crm_file)
    df_crm.columns = df_crm.columns.str.lower()
    if "utm_hit" in df_crm.columns:
        df_crm["utm_hit"] = df_crm["utm_hit"].apply(parse_utm)
        utm_df = pd.json_normalize(df_crm["utm_hit"]).add_prefix("utm_hit_")
        df_crm = pd.concat([df_crm.drop(columns=["utm_hit"]), utm_df], axis=1)

    # Phone cleaning by extracting last 10 digits consistently
    df_crm["cleaned_phone"] = df_crm["phone"].apply(extract_last_10_digits)

    st.write("CRM cleaned phones sample:", df_crm["cleaned_phone"].dropna().sample(min(10, len(df_crm))))

    # Load Dialer and extract last 10 digits similarly
    df_dialer = pd.read_excel(dialer_file)
    df_dialer.columns = df_dialer.columns.str.lower()
    df_dialer = df_dialer[['customer number', 'account', 'start time', 'queue duration', 'end time', 'call status']]

    df_dialer["cleaned_phone"] = df_dialer["customer number"].apply(extract_last_10_digits)

    st.write("Dialer cleaned phones sample:", df_dialer["cleaned_phone"].dropna().sample(min(10, len(df_dialer))))

    df_dialer["start time"] = pd.to_datetime(df_dialer["start time"])
    df_dialer["end time"] = pd.to_datetime(df_dialer["end time"])
    df_dialer["queue duration"] = pd.to_datetime(df_dialer["queue duration"])

    df_dialer["answer_duration_sec"] = (df_dialer["end time"] - df_dialer["start time"]).dt.total_seconds()
    df_dialer["queue_sec"] = (
        df_dialer["queue duration"].dt.hour * 3600 +
        df_dialer["queue duration"].dt.minute * 60 +
        df_dialer["queue duration"].dt.second
    )
    df_dialer["total_duration_sec"] = df_dialer["answer_duration_sec"] + df_dialer["queue_sec"]
    df_dialer["answer_duration_hms"] = pd.to_timedelta(df_dialer["answer_duration_sec"], unit="s").astype(str).str.split().str[0]
    df_dialer["total_duration_hms"] = pd.to_timedelta(df_dialer["total_duration_sec"], unit="s").astype(str).str.split().str[0]

    # Merge CRM and Dialer on cleaned_phone (last 10 digits)
    df_calls = df_crm.merge(df_dialer, on="cleaned_phone", how="left")
    df_calls["first_name"] = df_calls["full_name"].str.split().str[0]

    df_calls["duration_sec"] = (df_calls["end time"] - df_calls["start time"]).dt.total_seconds()
    df_calls.loc[df_calls["call status"] == "Missed", "duration_sec"] = 0

    crm_unique_phones = set(df_crm["cleaned_phone"].dropna().unique())
    dialed_unique_phones = set(df_dialer["cleaned_phone"].dropna().unique())

    untouched_phones = crm_unique_phones - dialed_unique_phones
    contacted_phones = dialed_unique_phones

    df_crm["contacted"] = df_crm["cleaned_phone"].isin(contacted_phones)
    df_crm["untouched"] = df_crm["cleaned_phone"].isin(untouched_phones)

    if "utm_hit_utmSource" in df_crm.columns and "utm_hit_utmCampaign" in df_crm.columns:
        total_leads = (
            df_crm.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign"], dropna=False)["cleaned_phone"]
            .nunique()
            .reset_index(name="total_leads")
        )

        def classify_status(gr):
            if 'Answered' in gr.values:
                return 'Answered'
            elif 'Missed' in gr.values:
                return 'Missed'
            else:
                return 'None'

        lead_status = (
            df_calls.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign", "cleaned_phone"], dropna=False)["call status"]
            .agg(classify_status)
            .reset_index()
        )

        summary = (
            lead_status.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign", "call status"], dropna=False)["cleaned_phone"]
            .nunique()
            .unstack(fill_value=0)
            .reset_index()
        )
        summary = summary.rename(columns={'Answered': 'answered_leads', 'Missed': 'missed_leads', 'None': 'other_leads'})

        for col in ['answered_leads', 'missed_leads']:
            if col not in summary.columns:
                summary[col] = 0

        summary["dialled_leads"] = summary['answered_leads'] + summary['missed_leads']

        campaign_engagement = total_leads.merge(summary, on=["utm_hit_utmSource", "utm_hit_utmCampaign"], how="left").fillna(0)
        campaign_engagement["untouched_leads"] = campaign_engagement["total_leads"] - campaign_engagement["dialled_leads"]
        campaign_engagement["contact_rate_%"] = ((campaign_engagement["dialled_leads"] / campaign_engagement["total_leads"]) * 100).round(1)
        campaign_engagement["answer_rate_%"] = campaign_engagement.apply(
            lambda x: (x["answered_leads"] / x["dialled_leads"] * 100) if x["dialled_leads"] > 0 else 0,
            axis=1,
        ).round(1)

        st.subheader("📊 Campaign Engagement Summary")
        st.dataframe(campaign_engagement, use_container_width=True)

        dialer_summary = (
            df_calls.groupby(["cleaned_phone", "first_name", "account"])
            .agg(
                answered_calls=("call status", lambda x: (x == "Answered").sum()),
                missed_calls=("call status", lambda x: (x == "Missed").sum()),
                total_duration_sec=("duration_sec", "sum"),
                answered_duration_sec=("duration_sec", lambda x: x[df_calls.loc[x.index, "call status"] == "Answered"].sum()),
            )
            .reset_index()
        )

        dialer_summary["answered_duration_hms"] = pd.to_timedelta(dialer_summary["answered_duration_sec"], unit="s").astype(str).str.split().str[-1]
        dialer_summary["total_duration_hms"] = pd.to_timedelta(dialer_summary["total_duration_sec"], unit="s").astype(str).str.split().str[-1]

        dialer_summary = dialer_summary[
            [
                "cleaned_phone",
                "first_name",
                "account",
                "answered_calls",
                "missed_calls",
                "answered_duration_hms",
                "total_duration_hms",
            ]
        ]

        st.sidebar.header("Filters")
        selected_names = st.sidebar.multiselect("Filter by First Name", options=dialer_summary["first_name"].unique())
        selected_accounts = st.sidebar.multiselect("Filter by Account", options=dialer_summary["account"].unique())
        selected_phones = st.sidebar.multiselect("Filter by Phone", options=dialer_summary["cleaned_phone"].unique())

        filtered_summary = dialer_summary.copy()
        if selected_names:
            filtered_summary = filtered_summary[filtered_summary["first_name"].isin(selected_names)]
        if selected_accounts:
            filtered_summary = filtered_summary[filtered_summary["account"].isin(selected_accounts)]
        if selected_phones:
            filtered_summary = filtered_summary[filtered_summary["cleaned_phone"].isin(selected_phones)]

        st.subheader("Dialer Summary")
        st.dataframe(filtered_summary, use_container_width=True)

        selected_phone = st.selectbox("Select phone to view detailed calls", options=filtered_summary["cleaned_phone"].unique())
        if selected_phone:
            st.subheader(f"Detailed Calls for {selected_phone}")
            call_details = df_calls[df_calls["cleaned_phone"] == selected_phone][
                ["start time", "end time", "call status", "answer_duration_hms", "total_duration_hms"]
            ]
            st.dataframe(call_details, use_container_width=True)

        source_connectivity = df_calls.groupby(["utm_hit_utmSource", "call status"]).size().unstack(fill_value=0).reset_index()
        if "Answered" not in source_connectivity.columns:
            source_connectivity["Answered"] = 0
        if "Missed" not in source_connectivity.columns:
            source_connectivity["Missed"] = 0
        source_connectivity = source_connectivity.rename(columns={"Answered": "answered_calls", "Missed": "missed_calls"})
        source_connectivity["total_calls"] = source_connectivity["answered_calls"] + source_connectivity["missed_calls"]
        source_connectivity["connectivity_rate"] = (source_connectivity["answered_calls"] / source_connectivity["total_calls"]).round(2)

        st.subheader("Connectivity Rate by Source")
        st.dataframe(source_connectivity, use_container_width=True)
