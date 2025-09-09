import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pandas import json_normalize
import ast
import phonenumbers
import streamlit as st

# Auto-generated global mapping of calling codes <-> ISO alpha-2
CALLING_CODE_TO_ISO = {
  "1": [
    "US",
    "CA",
    "AG",
    "AI",
    "AS",
    "BB",
    "BM",
    "BS",
    "DM",
    "DO",
    "GD",
    "GU",
    "JM",
    "KN",
    "KY",
    "LC",
    "MP",
    "MS",
    "PR",
    "SX",
    "TC",
    "TT",
    "VC",
    "VG",
    "VI"
  ],
  "20": [
    "EG"
  ],
  "211": [
    "SS"
  ],
  "212": [
    "MA",
    "EH"
  ],
  "213": [
    "DZ"
  ],
  "216": [
    "TN"
  ],
  "218": [
    "LY"
  ],
  "220": [
    "GM"
  ],
  "221": [
    "SN"
  ],
  "222": [
    "MR"
  ],
  "223": [
    "ML"
  ],
  "224": [
    "GN"
  ],
  "225": [
    "CI"
  ],
  "226": [
    "BF"
  ],
  "227": [
    "NE"
  ],
  "228": [
    "TG"
  ],
  "229": [
    "BJ"
  ],
  "230": [
    "MU"
  ],
  "231": [
    "LR"
  ],
  "232": [
    "SL"
  ],
  "233": [
    "GH"
  ],
  "234": [
    "NG"
  ],
  "235": [
    "TD"
  ],
  "236": [
    "CF"
  ],
  "237": [
    "CM"
  ],
  "238": [
    "CV"
  ],
  "239": [
    "ST"
  ],
  "240": [
    "GQ"
  ],
  "241": [
    "GA"
  ],
  "242": [
    "CG"
  ],
  "243": [
    "CD"
  ],
  "244": [
    "AO"
  ],
  "245": [
    "GW"
  ],
  "246": [
    "IO"
  ],
  "247": [
    "SH"
  ],
  "248": [
    "SC"
  ],
  "249": [
    "SD"
  ],
  "250": [
    "RW"
  ],
  "251": [
    "ET"
  ],
  "252": [
    "SO"
  ],
  "253": [
    "DJ"
  ],
  "254": [
    "KE"
  ],
  "255": [
    "TZ"
  ],
  "256": [
    "UG"
  ],
  "257": [
    "BI"
  ],
  "258": [
    "MZ"
  ],
  "260": [
    "ZM"
  ],
  "261": [
    "MG"
  ],
  "262": [
    "RE",
    "YT"
  ],
  "263": [
    "ZW"
  ],
  "264": [
    "NA"
  ],
  "265": [
    "MW"
  ],
  "266": [
    "LS"
  ],
  "267": [
    "BW"
  ],
  "268": [
    "SZ"
  ],
  "269": [
    "KM"
  ],
  "27": [
    "ZA"
  ],
  "290": [
    "SH"
  ],
  "291": [
    "ER"
  ],
  "500": [
    "FK"
  ],
  "501": [
    "BZ"
  ],
  "502": [
    "GT"
  ],
  "503": [
    "SV"
  ],
  "504": [
    "HN"
  ],
  "505": [
    "NI"
  ],
  "506": [
    "CR"
  ],
  "507": [
    "PA"
  ],
  "508": [
    "PM"
  ],
  "509": [
    "HT"
  ],
  "51": [
    "PE"
  ],
  "52": [
    "MX"
  ],
  "53": [
    "CU"
  ],
  "54": [
    "AR"
  ],
  "55": [
    "BR"
  ],
  "56": [
    "CL"
  ],
  "57": [
    "CO"
  ],
  "58": [
    "VE"
  ],
  "590": [
    "GP",
    "BL",
    "MF"
  ],
  "591": [
    "BO"
  ],
  "592": [
    "GY"
  ],
  "593": [
    "EC"
  ],
  "594": [
    "GF"
  ],
  "595": [
    "PY"
  ],
  "596": [
    "MQ"
  ],
  "597": [
    "SR"
  ],
  "598": [
    "UY"
  ],
  "599": [
    "CW",
    "BQ"
  ],
  "30": [
    "GR"
  ],
  "31": [
    "NL"
  ],
  "32": [
    "BE"
  ],
  "33": [
    "FR"
  ],
  "34": [
    "ES"
  ],
  "350": [
    "GI"
  ],
  "351": [
    "PT"
  ],
  "352": [
    "LU"
  ],
  "353": [
    "IE"
  ],
  "354": [
    "IS"
  ],
  "355": [
    "AL"
  ],
  "356": [
    "MT"
  ],
  "357": [
    "CY"
  ],
  "358": [
    "FI",
    "AX"
  ],
  "359": [
    "BG"
  ],
  "36": [
    "HU"
  ],
  "370": [
    "LT"
  ],
  "371": [
    "LV"
  ],
  "372": [
    "EE"
  ],
  "373": [
    "MD"
  ],
  "374": [
    "AM"
  ],
  "375": [
    "BY"
  ],
  "376": [
    "AD"
  ],
  "377": [
    "MC"
  ],
  "378": [
    "SM"
  ],
  "379": [
    "VA"
  ],
  "380": [
    "UA"
  ],
  "381": [
    "RS"
  ],
  "382": [
    "ME"
  ],
  "383": [
    "XK"
  ],
  "385": [
    "HR"
  ],
  "386": [
    "SI"
  ],
  "387": [
    "BA"
  ],
  "389": [
    "MK"
  ],
  "39": [
    "IT",
    "VA"
  ],
  "40": [
    "RO"
  ],
  "41": [
    "CH"
  ],
  "420": [
    "CZ"
  ],
  "421": [
    "SK"
  ],
  "423": [
    "LI"
  ],
  "43": [
    "AT"
  ],
  "44": [
    "GB",
    "GG",
    "JE",
    "IM"
  ],
  "45": [
    "DK"
  ],
  "46": [
    "SE"
  ],
  "47": [
    "NO",
    "SJ"
  ],
  "48": [
    "PL"
  ],
  "49": [
    "DE"
  ],
  "90": [
    "TR"
  ],
  "91": [
    "IN"
  ],
  "92": [
    "PK"
  ],
  "93": [
    "AF"
  ],
  "94": [
    "LK"
  ],
  "95": [
    "MM"
  ],
  "960": [
    "MV"
  ],
  "961": [
    "LB"
  ],
  "962": [
    "JO"
  ],
  "963": [
    "SY"
  ],
  "964": [
    "IQ"
  ],
  "965": [
    "KW"
  ],
  "966": [
    "SA"
  ],
  "967": [
    "YE"
  ],
  "968": [
    "OM"
  ],
  "970": [
    "PS"
  ],
  "971": [
    "AE"
  ],
  "972": [
    "IL"
  ],
  "973": [
    "BH"
  ],
  "974": [
    "QA"
  ],
  "975": [
    "BT"
  ],
  "976": [
    "MN"
  ],
  "977": [
    "NP"
  ],
  "98": [
    "IR"
  ],
  "992": [
    "TJ"
  ],
  "993": [
    "TM"
  ],
  "994": [
    "AZ"
  ],
  "995": [
    "GE"
  ],
  "996": [
    "KG"
  ],
  "997": [
    "KZ"
  ],
  "998": [
    "UZ"
  ],
  "60": [
    "MY"
  ],
  "61": [
    "AU",
    "CC",
    "CX"
  ],
  "62": [
    "ID"
  ],
  "63": [
    "PH"
  ],
  "64": [
    "NZ",
    "PN"
  ],
  "65": [
    "SG"
  ],
  "66": [
    "TH"
  ],
  "670": [
    "TL"
  ],
  "672": [
    "NF"
  ],
  "673": [
    "BN"
  ],
  "674": [
    "NR"
  ],
  "675": [
    "PG"
  ],
  "676": [
    "TO"
  ],
  "677": [
    "SB"
  ],
  "678": [
    "VU"
  ],
  "679": [
    "FJ"
  ],
  "680": [
    "PW"
  ],
  "681": [
    "WF"
  ],
  "682": [
    "CK"
  ],
  "683": [
    "NU"
  ],
  "685": [
    "WS"
  ],
  "686": [
    "KI"
  ],
  "687": [
    "NC"
  ],
  "688": [
    "TV"
  ],
  "689": [
    "PF"
  ],
  "690": [
    "TK"
  ],
  "691": [
    "FM"
  ],
  "692": [
    "MH"
  ],
  "81": [
    "JP"
  ],
  "82": [
    "KR"
  ],
  "84": [
    "VN"
  ],
  "850": [
    "KP"
  ],
  "852": [
    "HK"
  ],
  "853": [
    "MO"
  ],
  "855": [
    "KH"
  ],
  "856": [
    "LA"
  ],
  "86": [
    "CN"
  ],
  "880": [
    "BD"
  ],
  "886": [
    "TW"
  ],
  "7": [
    "RU",
    "KZ"
  ]
}

ISO_TO_CALLING_CODE = {
  "US": [
    "1"
  ],
  "CA": [
    "1"
  ],
  "AG": [
    "1"
  ],
  "AI": [
    "1"
  ],
  "AS": [
    "1"
  ],
  "BB": [
    "1"
  ],
  "BM": [
    "1"
  ],
  "BS": [
    "1"
  ],
  "DM": [
    "1"
  ],
  "DO": [
    "1"
  ],
  "GD": [
    "1"
  ],
  "GU": [
    "1"
  ],
  "JM": [
    "1"
  ],
  "KN": [
    "1"
  ],
  "KY": [
    "1"
  ],
  "LC": [
    "1"
  ],
  "MP": [
    "1"
  ],
  "MS": [
    "1"
  ],
  "PR": [
    "1"
  ],
  "SX": [
    "1"
  ],
  "TC": [
    "1"
  ],
  "TT": [
    "1"
  ],
  "VC": [
    "1"
  ],
  "VG": [
    "1"
  ],
  "VI": [
    "1"
  ],
  "EG": [
    "20"
  ],
  "SS": [
    "211"
  ],
  "MA": [
    "212"
  ],
  "EH": [
    "212"
  ],
  "DZ": [
    "213"
  ],
  "TN": [
    "216"
  ],
  "LY": [
    "218"
  ],
  "GM": [
    "220"
  ],
  "SN": [
    "221"
  ],
  "MR": [
    "222"
  ],
  "ML": [
    "223"
  ],
  "GN": [
    "224"
  ],
  "CI": [
    "225"
  ],
  "BF": [
    "226"
  ],
  "NE": [
    "227"
  ],
  "TG": [
    "228"
  ],
  "BJ": [
    "229"
  ],
  "MU": [
    "230"
  ],
  "LR": [
    "231"
  ],
  "SL": [
    "232"
  ],
  "GH": [
    "233"
  ],
  "NG": [
    "234"
  ],
  "TD": [
    "235"
  ],
  "CF": [
    "236"
  ],
  "CM": [
    "237"
  ],
  "CV": [
    "238"
  ],
  "ST": [
    "239"
  ],
  "GQ": [
    "240"
  ],
  "GA": [
    "241"
  ],
  "CG": [
    "242"
  ],
  "CD": [
    "243"
  ],
  "AO": [
    "244"
  ],
  "GW": [
    "245"
  ],
  "IO": [
    "246"
  ],
  "SH": [
    "247",
    "290"
  ],
  "SC": [
    "248"
  ],
  "SD": [
    "249"
  ],
  "RW": [
    "250"
  ],
  "ET": [
    "251"
  ],
  "SO": [
    "252"
  ],
  "DJ": [
    "253"
  ],
  "KE": [
    "254"
  ],
  "TZ": [
    "255"
  ],
  "UG": [
    "256"
  ],
  "BI": [
    "257"
  ],
  "MZ": [
    "258"
  ],
  "ZM": [
    "260"
  ],
  "MG": [
    "261"
  ],
  "RE": [
    "262"
  ],
  "YT": [
    "262"
  ],
  "ZW": [
    "263"
  ],
  "NA": [
    "264"
  ],
  "MW": [
    "265"
  ],
  "LS": [
    "266"
  ],
  "BW": [
    "267"
  ],
  "SZ": [
    "268"
  ],
  "KM": [
    "269"
  ],
  "ZA": [
    "27"
  ],
  "ER": [
    "291"
  ],
  "FK": [
    "500"
  ],
  "BZ": [
    "501"
  ],
  "GT": [
    "502"
  ],
  "SV": [
    "503"
  ],
  "HN": [
    "504"
  ],
  "NI": [
    "505"
  ],
  "CR": [
    "506"
  ],
  "PA": [
    "507"
  ],
  "PM": [
    "508"
  ],
  "HT": [
    "509"
  ],
  "PE": [
    "51"
  ],
  "MX": [
    "52"
  ],
  "CU": [
    "53"
  ],
  "AR": [
    "54"
  ],
  "BR": [
    "55"
  ],
  "CL": [
    "56"
  ],
  "CO": [
    "57"
  ],
  "VE": [
    "58"
  ],
  "GP": [
    "590"
  ],
  "BL": [
    "590"
  ],
  "MF": [
    "590"
  ],
  "BO": [
    "591"
  ],
  "GY": [
    "592"
  ],
  "EC": [
    "593"
  ],
  "GF": [
    "594"
  ],
  "PY": [
    "595"
  ],
  "MQ": [
    "596"
  ],
  "SR": [
    "597"
  ],
  "UY": [
    "598"
  ],
  "CW": [
    "599"
  ],
  "BQ": [
    "599"
  ],
  "GR": [
    "30"
  ],
  "NL": [
    "31"
  ],
  "BE": [
    "32"
  ],
  "FR": [
    "33"
  ],
  "ES": [
    "34"
  ],
  "GI": [
    "350"
  ],
  "PT": [
    "351"
  ],
  "LU": [
    "352"
  ],
  "IE": [
    "353"
  ],
  "IS": [
    "354"
  ],
  "AL": [
    "355"
  ],
  "MT": [
    "356"
  ],
  "CY": [
    "357"
  ],
  "FI": [
    "358"
  ],
  "AX": [
    "358"
  ],
  "BG": [
    "359"
  ],
  "HU": [
    "36"
  ],
  "LT": [
    "370"
  ],
  "LV": [
    "371"
  ],
  "EE": [
    "372"
  ],
  "MD": [
    "373"
  ],
  "AM": [
    "374"
  ],
  "BY": [
    "375"
  ],
  "AD": [
    "376"
  ],
  "MC": [
    "377"
  ],
  "SM": [
    "378"
  ],
  "VA": [
    "39",
    "379"
  ],
  "UA": [
    "380"
  ],
  "RS": [
    "381"
  ],
  "ME": [
    "382"
  ],
  "XK": [
    "383"
  ],
  "HR": [
    "385"
  ],
  "SI": [
    "386"
  ],
  "BA": [
    "387"
  ],
  "MK": [
    "389"
  ],
  "IT": [
    "39"
  ],
  "RO": [
    "40"
  ],
  "CH": [
    "41"
  ],
  "CZ": [
    "420"
  ],
  "SK": [
    "421"
  ],
  "LI": [
    "423"
  ],
  "AT": [
    "43"
  ],
  "GB": [
    "44"
  ],
  "GG": [
    "44"
  ],
  "JE": [
    "44"
  ],
  "IM": [
    "44"
  ],
  "DK": [
    "45"
  ],
  "SE": [
    "46"
  ],
  "NO": [
    "47"
  ],
  "SJ": [
    "47"
  ],
  "PL": [
    "48"
  ],
  "DE": [
    "49"
  ],
  "TR": [
    "90"
  ],
  "IN": [
    "91"
  ],
  "PK": [
    "92"
  ],
  "AF": [
    "93"
  ],
  "LK": [
    "94"
  ],
  "MM": [
    "95"
  ],
  "MV": [
    "960"
  ],
  "LB": [
    "961"
  ],
  "JO": [
    "962"
  ],
  "SY": [
    "963"
  ],
  "IQ": [
    "964"
  ],
  "KW": [
    "965"
  ],
  "SA": [
    "966"
  ],
  "YE": [
    "967"
  ],
  "OM": [
    "968"
  ],
  "PS": [
    "970"
  ],
  "AE": [
    "971"
  ],
  "IL": [
    "972"
  ],
  "BH": [
    "973"
  ],
  "QA": [
    "974"
  ],
  "BT": [
    "975"
  ],
  "MN": [
    "976"
  ],
  "NP": [
    "977"
  ],
  "IR": [
    "98"
  ],
  "TJ": [
    "992"
  ],
  "TM": [
    "993"
  ],
  "AZ": [
    "994"
  ],
  "GE": [
    "995"
  ],
  "KG": [
    "996"
  ],
  "KZ": [
    "7",
    "997"
  ],
  "UZ": [
    "998"
  ],
  "MY": [
    "60"
  ],
  "AU": [
    "61"
  ],
  "CC": [
    "61"
  ],
  "CX": [
    "61"
  ],
  "ID": [
    "62"
  ],
  "PH": [
    "63"
  ],
  "NZ": [
    "64"
  ],
  "PN": [
    "64"
  ],
  "SG": [
    "65"
  ],
  "TH": [
    "66"
  ],
  "TL": [
    "670"
  ],
  "NF": [
    "672"
  ],
  "BN": [
    "673"
  ],
  "NR": [
    "674"
  ],
  "PG": [
    "675"
  ],
  "TO": [
    "676"
  ],
  "SB": [
    "677"
  ],
  "VU": [
    "678"
  ],
  "FJ": [
    "679"
  ],
  "PW": [
    "680"
  ],
  "WF": [
    "681"
  ],
  "CK": [
    "682"
  ],
  "NU": [
    "683"
  ],
  "WS": [
    "685"
  ],
  "KI": [
    "686"
  ],
  "NC": [
    "687"
  ],
  "TV": [
    "688"
  ],
  "PF": [
    "689"
  ],
  "TK": [
    "690"
  ],
  "FM": [
    "691"
  ],
  "MH": [
    "692"
  ],
  "JP": [
    "81"
  ],
  "KR": [
    "82"
  ],
  "VN": [
    "84"
  ],
  "KP": [
    "850"
  ],
  "HK": [
    "852"
  ],
  "MO": [
    "853"
  ],
  "KH": [
    "855"
  ],
  "LA": [
    "856"
  ],
  "CN": [
    "86"
  ],
  "BD": [
    "880"
  ],
  "TW": [
    "886"
  ],
  "RU": [
    "7"
  ]
}


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
        except:
            return None
    return None

sorted_prefixes = sorted(CALLING_CODE_TO_ISO.keys(), key=lambda x: -len(x))

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
st.set_page_config(page_title="Call & CRM Analysis", layout="wide")
st.title("📞 Call & CRM Connectivity Dashboard")

# Upload files
crm_file = st.file_uploader("Upload CRM Excel (user_exports...)", type=["xlsx"])
dialer_file = st.file_uploader("Upload Dialer Log Excel", type=["xlsx"])

if crm_file and dialer_file:
    # =========================
    # CRM Data
    # =========================
    df = pd.read_excel(crm_file)
    df.columns = df.columns.astype(str).str.lower()
    
    if "utm_hit" in df.columns:
        df["utm_hit"] = df["utm_hit"].apply(parse_utm)
        utm_df = pd.json_normalize(df["utm_hit"]).add_prefix("utm_hit_")
        df = pd.concat([df.drop(columns=["utm_hit"]), utm_df], axis=1)

    df["cleaned_phone"] = df["phone"].apply(smart_parse)
    
    # =========================
    # Dialer Data
    # =========================
    dialer = pd.read_excel(dialer_file)
    dialer.columns = dialer.columns.astype(str).str.lower()
    dialer = dialer[['customer number','account','start time','queue duration','end time','call status']]

    # Convert to datetime
    dialer["start time"] = pd.to_datetime(dialer["start time"])
    dialer["end time"] = pd.to_datetime(dialer["end time"])
    dialer["queue duration"] = pd.to_datetime(dialer["queue duration"])

    # Duration calculations
    dialer["answer_duration_sec"] = (dialer["end time"] - dialer["start time"]).dt.total_seconds()
    dialer["queue_sec"] = (
        dialer["queue duration"].dt.hour * 3600
        + dialer["queue duration"].dt.minute * 60
        + dialer["queue duration"].dt.second
    )
    dialer["total_duration_sec"] = dialer["answer_duration_sec"] + dialer["queue_sec"]

    # Format to hh:mm:ss
    dialer["answer_duration_hms"] = pd.to_timedelta(dialer["answer_duration_sec"], unit="s").apply(lambda x: str(x).split(".")[0]).str.replace("0 days ", "", regex=False)
    dialer["total_duration_hms"] = pd.to_timedelta(dialer["total_duration_sec"], unit="s").apply(lambda x: str(x).split(".")[0]).str.replace("0 days ", "", regex=False)

    # Clean phone numbers
    dialer = dialer.rename(columns={'customer number':'cleaned_phone'})
    dialer["cleaned_phone"] = dialer["cleaned_phone"].apply(smart_parse)

    # =========================
    # Merge CRM + Dialer
    # =========================
    df_calls = df.merge(dialer, on="cleaned_phone", how="left")
    df_calls["first_name"] = df_calls["full_name"].str.split().str[0]

    # Ensure duration_sec exists
    df_calls["duration_sec"] = (df_calls["end time"] - df_calls["start time"]).dt.total_seconds()
    df_calls.loc[df_calls["call status"] == "Missed", "duration_sec"] = 0

    # =========================
    # Dialer Summary (including account)
    # =========================
    dialer_summary = (
        df_calls.groupby(["cleaned_phone", "first_name", "account"])
        .agg(
            answered_calls=("call status", lambda x: (x=="Answered").sum()),
            missed_calls=("call status", lambda x: (x=="Missed").sum()),
            total_duration_sec=("duration_sec","sum"),
            answered_duration_sec=("duration_sec", lambda x: x[df_calls.loc[x.index,"call status"]=="Answered"].sum())
        )
        .reset_index()
    )

    dialer_summary["answered_duration_hms"] = pd.to_timedelta(dialer_summary["answered_duration_sec"], unit="s").astype(str).str.split().str[-1]
    dialer_summary["total_duration_hms"] = pd.to_timedelta(dialer_summary["total_duration_sec"], unit="s").astype(str).str.split().str[-1]

    dialer_summary = dialer_summary[
        ["cleaned_phone","first_name","account","answered_calls","missed_calls","answered_duration_hms","total_duration_hms"]
    ]

    st.subheader("Dialer Summary by Contact")
    st.dataframe(dialer_summary, use_container_width=True)

    # =========================
    # Multi-row selection (optional dropdown for details)
    selected_phone = st.selectbox(
        "Select a contact to view detailed call logs",
        options=dialer_summary["cleaned_phone"].unique()
    )
    if selected_phone:
        st.subheader(f"📋 Detailed Calls for {selected_phone}")
        call_details = df_calls[df_calls["cleaned_phone"]==selected_phone][
            ["account","start time","end time","call status","answer_duration_hms","total_duration_hms"]
        ]
        st.dataframe(call_details, use_container_width=True)

    # =========================
    # Campaign Summary
    st.subheader("Campaign Summary (Source + Campaign)")
    campaign_summary = (
        df_calls
        .groupby(["utm_hit_utmSource","utm_hit_utmCampaign","cleaned_phone","first_name","call status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"Answered":"answered_calls","Missed":"missed_calls"})
    )
    st.dataframe(campaign_summary)

    # =========================
    # Connectivity Rate by Source
    st.subheader("Connectivity Rate by Source")
    source_connectivity = (
        df_calls.groupby(["utm_hit_utmSource","call status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"Answered":"answered_calls","Missed":"missed_calls"})
    )
    source_connectivity["total_calls"] = source_connectivity["answered_calls"] + source_connectivity["missed_calls"]
    source_connectivity["connectivity_rate"] = (source_connectivity["answered_calls"]/source_connectivity["total_calls"]).round(2)
    st.dataframe(source_connectivity)

    st.subheader("📊 Connectivity Rate by Source (Chart)")
    st.bar_chart(source_connectivity.set_index("utm_hit_utmSource")["connectivity_rate"])
