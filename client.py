import streamlit as st
import pandas as pd
import numpy as np
import ast
import phonenumbers
import re
import math


# ======================================
# ⚙️ Helper functions (from your code)
# ======================================
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

def smart_parse(num):
    if num is None:
        return None
    if isinstance(num, float) and math.isnan(num):
        return None

    # Handle floats (including scientific notation) by converting to int string
    if isinstance(num, float):
        try:
            s = str(int(num))
        except:
            return None
    else:
        s = str(num).strip()

    # Remove non-digits for digit count
    digits_only = re.sub(r'\D', '', s)

    # If exactly 10 digits and no '+' prefix, assume Indian local number and prepend +91
    if len(digits_only) == 10 and not s.startswith("+"):
        s = "+91" + digits_only
    elif not s.startswith("+"):
        s = "+" + s

    try:
        parsed = phonenumbers.parse(s, None)
        if phonenumbers.is_valid_number(parsed):
            # Format as E164 and remove '+'
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164).replace("+", "")
    except:
        return None

    return None

# ======================================
# Streamlit UI
# ======================================
st.set_page_config(page_title="Call & CRM Dashboard", layout="wide")
st.title("📞 Call & CRM Analysis")

# Upload files
crm_file = st.file_uploader("Upload CRM file", type=["xlsx"])
dialer_file = st.file_uploader("Upload Dialer file", type=["xlsx"])

if crm_file and dialer_file:
    # -------------------
    # Load CRM
    # -------------------
    df = pd.read_excel(crm_file)
    df.columns = df.columns.str.lower()
    if "utm_hit" in df.columns:
        df["utm_hit"] = df["utm_hit"].apply(parse_utm)
        utm_df = pd.json_normalize(df["utm_hit"]).add_prefix("utm_hit_")
        df_con = pd.concat([df.drop(columns=["utm_hit"]), utm_df], axis=1)
    else:
        df_con = df.copy()
    
    df_con["cleaned_phone"] = df_con["phone"].astype(str).str[-10:]

    # -------------------
    # Load Dialer
    # -------------------
    Dialer = pd.read_excel(dialer_file)
    Dialer.columns = Dialer.columns.str.lower()
    Dialer = Dialer[['customer number','account','start time','queue duration','end time','call status']]
    
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

    Dialer = Dialer.rename(columns={'customer number':'cleaned_phone'})
    
    Dialer["cleaned_phone"] = Dialer["cleaned_phone"].apply(smart_parse)

    # -------------------
    # Merge
    # -------------------
    df_calls = df_con.merge(Dialer, on="cleaned_phone", how="left")
    df_calls["first_name"] = df_calls["full_name"].str.split().str[0]

    # Duration
    df_calls["duration_sec"] = (df_calls["end time"] - df_calls["start time"]).dt.total_seconds()
    df_calls.loc[df_calls["call status"] == "Missed", "duration_sec"] = 0
    
    # These are the unique numbers loaded in CRM
    crm_unique_phones = set(df_con["cleaned_phone"].dropna().unique())

    # These are the unique numbers dialled at least once (including missed or answered)
    dialled_unique_phones = set(Dialer["cleaned_phone"].dropna().unique())

    # Untouched = in CRM but never dialled
    untouched_phones = crm_unique_phones - dialled_unique_phones

    # Contacted = dialled at least once
    contacted_phones = dialled_unique_phones

    # For campaign summary, show actual unique phone numbers for contacted/untouched leads
    df_con["contacted"] = df_con["cleaned_phone"].isin(contacted_phones)
    df_con["untouched"] = df_con["cleaned_phone"].isin(untouched_phones)

    # Then for each campaign
    campaign_contacted = df_con[df_con["contacted"]].groupby(
        ["utm_hit_utmSource", "utm_hit_utmCampaign"]
    )["cleaned_phone"].unique().reset_index(name="contacted_leads")
    campaign_untouched = df_con[df_con["untouched"]].groupby(
        ["utm_hit_utmSource", "utm_hit_utmCampaign"]
    )["cleaned_phone"].unique().reset_index(name="untouched_leads")
    # -------------------
    # Campaign Engagement Summary (paste here)
    # -------------------
    if "utm_hit_utmSource" in df_con.columns and "utm_hit_utmCampaign" in df_con.columns:
        total_leads = (
            df_con.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign"],dropna='False')["cleaned_phone"]
            .nunique()
            .reset_index(name="total_leads")
        )

        dialled_leads = (
            df_calls.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign"],dropna='False')["cleaned_phone"]
            .nunique()
            .reset_index(name="dialled_leads")
        )

        # For each source/campaign & phone, determine the HIGHEST call status
        def classify_status(gr):
            if 'Answered' in gr.values:
                return 'Answered'
            elif 'Missed' in gr.values:
                return 'Missed'
            else:
                return 'None'

        lead_status = (
            df_calls.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign", "cleaned_phone"],dropna='False')["call status"]
            .agg(classify_status)
            .reset_index()
        )

        summary = (
            lead_status
            .groupby(["utm_hit_utmSource", "utm_hit_utmCampaign", "call status"],dropna='False')["cleaned_phone"]
            .nunique()
            .unstack(fill_value=0)
            .reset_index()
        )
        summary = summary.rename(columns={'Answered': 'answered_leads', 'Missed': 'missed_leads', 'None': 'other_leads'})
        summary["dialled_leads"] = summary.get('answered_leads', 0) + summary.get('missed_leads', 0)

        # Get total and untouched leads
        total_leads = df_con.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign"], dropna=False)["cleaned_phone"].nunique().reset_index(name="total_leads")
        campaign_engagement = total_leads.merge(summary, on=["utm_hit_utmSource", "utm_hit_utmCampaign"], how="left").fillna(0)
        campaign_engagement["untouched_leads"] = campaign_engagement["total_leads"] - campaign_engagement["dialled_leads"]

        campaign_engagement["contact_rate_%"] = (
            (campaign_engagement["dialled_leads"] / campaign_engagement["total_leads"]) * 100
        ).round(1)

        campaign_engagement["answer_rate_%"] = campaign_engagement.apply(
            lambda x: (x["answered_leads"] / x["dialled_leads"] * 100) if x["dialled_leads"] > 0 else 0,
            axis=1
        ).round(1)

        st.subheader("📊 Campaign Engagement Summary")
        st.dataframe(campaign_engagement, use_container_width=True)
        # -------------------
        # Dialer Summary
        # -------------------
        dialer_summary = (
            df_calls.groupby(["cleaned_phone","first_name","account"])
            .agg(
                 answered_calls=("call status", lambda x: (x=="Answered").sum()),
                 missed_calls=("call status", lambda x: (x=="Missed").sum()),
                 total_duration_sec=("duration_sec","sum"),
                 answered_duration_sec=("duration_sec", lambda x: x[df_calls.loc[x.index,"call status"]=="Answered"].sum())
             ).reset_index()
        )

        dialer_summary["answered_duration_hms"] = pd.to_timedelta(dialer_summary["answered_duration_sec"], unit="s").astype(str).str.split().str[-1]
        dialer_summary["total_duration_hms"] = pd.to_timedelta(dialer_summary["total_duration_sec"], unit="s").astype(str).str.split().str[-1]
        dialer_summary = dialer_summary[["cleaned_phone","first_name","account","answered_calls","missed_calls","answered_duration_hms","total_duration_hms"]]

    # -------------------
    # Filters
    # -------------------
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

    # -------------------
    # Detailed Call Logs
    # -------------------
    selected_phone = st.selectbox("Select phone to view detailed calls", options=filtered_summary["cleaned_phone"].unique())
    if selected_phone:
        st.subheader(f"Detailed Calls for {selected_phone}")
        call_details = df_calls[df_calls["cleaned_phone"]==selected_phone][["start time","end time","call status","answer_duration_hms","total_duration_hms"]]
        st.dataframe(call_details, use_container_width=True)


    # -------------------
    # Connectivity Rate
    # -------------------
    source_connectivity = (
        df_calls.groupby(["utm_hit_utmSource","call status"])
        .size().unstack(fill_value=0).reset_index()
        .rename(columns={"Answered":"answered_calls","Missed":"missed_calls"})
    )
    source_connectivity["total_calls"] = source_connectivity["answered_calls"] + source_connectivity["missed_calls"]
    source_connectivity["connectivity_rate"] = (source_connectivity["answered_calls"]/source_connectivity["total_calls"]).round(2)
    st.subheader("Connectivity Rate by Source")
    st.dataframe(source_connectivity)
        
        # -------------------
        # Campaign Lead Engagement Summary
        # -------------------
    # if "utm_hit_utmSource" in df_con.columns and "utm_hit_utmCampaign" in df_con.columns:
    #     # Total leads per campaign
    #     campaign_leads = (
    #         df_con.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign"], dropna=False)
    #         .agg(total_leads=("cleaned_phone", "nunique"))
    #         .reset_index()
    #     )

    #     # Dialled leads per campaign
    #     dialled = df_calls.groupby(["utm_hit_utmSource", "utm_hit_utmCampaign"], dropna=False)["cleaned_phone"].nunique().reset_index(name="dialled_leads")
    #     answered = df_calls[df_calls["call status"]=="Answered"].groupby(["utm_hit_utmSource", "utm_hit_utmCampaign"], dropna=False)["cleaned_phone"].nunique().reset_index(name="answered_leads")
    #     missed = df_calls[df_calls["call status"]=="Missed"].groupby(["utm_hit_utmSource", "utm_hit_utmCampaign"], dropna=False)["cleaned_phone"].nunique().reset_index(name="missed_leads")

    #     # Merge all together
    #     campaign_summary_table = (
    #         campaign_leads
    #         .merge(dialled, on=["utm_hit_utmSource", "utm_hit_utmCampaign"], how="left")
    #         .merge(answered, on=["utm_hit_utmSource", "utm_hit_utmCampaign"], how="left")
    #         .merge(missed, on=["utm_hit_utmSource", "utm_hit_utmCampaign"], how="left")
    #         .fillna(0)
    #     )

    #     # Calculate untouched leads
    #     campaign_summary_table["untouched_leads"] = campaign_summary_table["total_leads"] - campaign_summary_table["dialled_leads"]

    #     # Display in Streamlit
    #     st.subheader("Campaign Lead Engagement Summary")
    #     st.dataframe(campaign_summary_table, use_container_width=True)
  
    #     st.subheader("Connectivity Chart")
    #     st.bar_chart(source_connectivity.set_index("utm_hit_utmSource")["connectivity_rate"])


























