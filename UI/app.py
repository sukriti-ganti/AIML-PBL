<<<<<<< HEAD
# UI/app.py
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import joblib

# ---------------------------
# Paths and model loading
# ---------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONV_MODEL_PATH    = PROJECT_ROOT / "models" / "conversion_model.joblib"   # Model 1 (LogReg)
FUNNEL_MODEL_PATH  = PROJECT_ROOT / "models" / "funnel_model.joblib"       # Model 2 (RF)
LEAD_RF_MODEL_PATH = PROJECT_ROOT / "models" / "lead_scoring_rf.joblib"    # Model 3 (optional RF)

# Saved CSV outputs (optional to display)
CONV_OUT_PATH   = PROJECT_ROOT / "data" / "conversion_predictions.csv"
FUNNEL_OUT_PATH = PROJECT_ROOT / "data" / "funnel_predictions.csv"

st.set_page_config(page_title="IntenSync - Lead Scoring", layout="wide")

# ---------------------------
# Styles (minimal)
# ---------------------------
st.markdown("""
<style>
:root {
  --brandBg: #DDF4E7;
  --brandPrimary: #234C6A;
  --brandText: #1B3C53;
  --brandAccent: #D2C1B6;
}
html, body, [class*="css"] { color: var(--brandText); }
.block-container { padding-top: 1.5rem; }
h1,h2,h3 { color: var(--brandPrimary); }
div[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.stButton>button {
  background: var(--brandPrimary); color: var(--brandAccent);
  border-radius: 20px; border: none; padding: 0.5rem 1rem;
}
.stButton>button:hover { background: #456882; }
.stTabs [data-baseweb="tab-list"] { gap: 1rem; border-bottom: 1px solid #234C6A20; }
.stTabs [data-baseweb="tab"] { font-weight: 700; color: var(--brandPrimary); }
.stDataFrame { border-radius: 10px; }
.small-hint { color: #5a7a8e; font-size: 13px; }
.badge-ok { color: #1b7f4e; font-weight: 600; }
.badge-miss { color: #7a2f2f; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Helpers
# ---------------------------
def tidy_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
                  .str.replace(r"\s+", "_", regex=True)
                  .str.replace(r"[()]", "", regex=True)
    )
    return df

def encode_align(df: pd.DataFrame, train_cols: list) -> pd.DataFrame:
    """One-hot encode object cols and align to training column order."""
    df = tidy_columns(df)
    cat_cols = df.select_dtypes(include=["object"]).columns
    df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
    # add missing columns from training
    for c in train_cols:
        if c not in df.columns:
            df[c] = 0
    # remove extras not in training & order columns
    df = df[train_cols]
    return df

def load_bundle(path: Path):
    try:
        if path.exists():
            return joblib.load(path)
        return None
    except Exception as e:
        st.warning(f"Could not load: {path.name}. Error: {e}")
        return None

def map_stage_heuristic(row_dict: dict) -> str:
    """Fallback stage logic for single-lead demo if no funnel model is used."""
    w = {
        "Email_Opened": 5,
        "Link_Clicked": 10,
        "Form_Filled": 15,
        "Demo_Requested": 20,
        "Pricing_Page_Viewed": 15,
        "Webinar_Attended": 25,
        "Contact_Sales": 30,
    }
    score = sum(w[k] for k, v in row_dict.items() if k in w and v)
    if score >= 25: return "Action"
    if score >= 12: return "Consideration"
    if score >= 5:  return "Interest"
    return "Awareness"

def to_lead_score_0_100(engagement: int) -> int:
    max_possible = 5+10+15+20+15+25+30  # 120
    val = round((engagement / max_possible) * 100)
    return min(100, max(0, val))

def compute_engagement_from_flags(flags: dict) -> int:
    weights = {
        "Email_Opened": 5,
        "Link_Clicked": 10,
        "Form_Filled": 15,
        "Demo_Requested": 20,
        "Pricing_Page_Viewed": 15,
        "Webinar_Attended": 25,
        "Contact_Sales": 30,
    }
    return sum(weights[k] if flags.get(k, False) else 0 for k in weights)

# ---------------------------
# Header (no images)
# ---------------------------
st.title("IntenSync – Lead Intelligence")
st.caption("This app mirrors your HTML demo and can also run trained Python models on uploaded CSVs.")

# ---------------------------
# Load models (if present)
# ---------------------------
conv_bundle    = load_bundle(CONV_MODEL_PATH)      # {"model": clf, "columns": [...]}
funnel_bundle  = load_bundle(FUNNEL_MODEL_PATH)    # {"model": clf, "columns": [...], "classes_":[...]}
lead_rf_bundle = load_bundle(LEAD_RF_MODEL_PATH)   # optional

st.sidebar.header("Model status")
st.sidebar.write(f"Model 1 (Conversion): {'Available' if conv_bundle else 'Missing'}")
st.sidebar.write(f"Model 2 (Funnel):     {'Available' if funnel_bundle else 'Missing'}")
st.sidebar.write(f"Model 3 (Lead RF):    {'Available' if lead_rf_bundle else 'Missing'}")

# ---------------------------
# Tabs
# ---------------------------
tabs = st.tabs(["Basic Scoring", "Advanced Scoring", "Model Management"])

# --------------------------------
# Tab 1: Basic Scoring (checkbox demo)
# --------------------------------
with tabs[0]:
    st.subheader("Basic Scoring")
    st.write("Select the activities the lead has performed to determine their funnel stage and a 0–100 lead score.")

    with st.form("basic_form"):
        colA, colB = st.columns([1,1])

        with colA:
            lead_id   = st.text_input("Lead ID (optional)", "")
            lead_name = st.text_input("Lead Name / Email (optional)", "")

        with colB:
            st.write("Activities")
            Email_Opened        = st.checkbox("Email Opened")
            Link_Clicked        = st.checkbox("Link Clicked")
            Form_Filled         = st.checkbox("Form Filled")
            Demo_Requested      = st.checkbox("Demo Requested")
            Pricing_Page_Viewed = st.checkbox("Pricing Page Viewed")
            Webinar_Attended    = st.checkbox("Webinar Attended")
            Contact_Sales       = st.checkbox("Contact Sales")

        submitted = st.form_submit_button("Score Lead")

    if "basic_table" not in st.session_state:
        st.session_state.basic_table = pd.DataFrame(
            columns=["LeadID","Name","Engagement","Stage","LeadScore_0_100"]
        )

    if submitted:
        flags = {
            "Email_Opened": Email_Opened,
            "Link_Clicked": Link_Clicked,
            "Form_Filled": Form_Filled,
            "Demo_Requested": Demo_Requested,
            "Pricing_Page_Viewed": Pricing_Page_Viewed,
            "Webinar_Attended": Webinar_Attended,
            "Contact_Sales": Contact_Sales,
        }
        engagement = compute_engagement_from_flags(flags)
        stage = map_stage_heuristic(flags)
        score100 = to_lead_score_0_100(engagement)

        st.success(f"Engagement: {engagement} | Stage: {stage} | Lead Score: {score100}")
        new_row = pd.DataFrame([{
            "LeadID": lead_id or f"LD-{str(len(st.session_state.basic_table)+1).zfill(4)}",
            "Name": lead_name or "-",
            "Engagement": engagement,
            "Stage": stage,
            "LeadScore_0_100": score100
        }])
        st.session_state.basic_table = pd.concat([st.session_state.basic_table, new_row], ignore_index=True)

    if len(st.session_state.basic_table):
        st.dataframe(st.session_state.basic_table.iloc[::-1].reset_index(drop=True))
        st.download_button(
            "Download CSV",
            st.session_state.basic_table.to_csv(index=False).encode("utf-8"),
            file_name="scored_leads_basic.csv",
            mime="text/csv"
        )

    st.caption("Weights: Email 5, Click 10, Form 15, Demo 20, Pricing 15, Webinar 25, Contact 30. Stage mapping: <5 Awareness, 5–11 Interest, 12–24 Consideration, ≥25 Action.")

# --------------------------------
# Tab 2: Advanced Scoring (run trained models on CSV)
# --------------------------------
with tabs[1]:
    st.subheader("Advanced Scoring (Models)")
    st.write("Upload a CSV of leads. We will run available models on it and return predictions.")

    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    run_models = st.button("Run Models")

    if uploaded and run_models:
        df_raw = pd.read_csv(uploaded)
        df_raw = tidy_columns(df_raw)

        # Keep a copy of an ID column if present
        lead_id_col = "LeadID" if "LeadID" in df_raw.columns else df_raw.columns[0]
        result = pd.DataFrame({lead_id_col: df_raw[lead_id_col]})

        # Model 1: Conversion Probability -> lead score 0-100
        if conv_bundle:
            model1 = conv_bundle["model"]
            cols1  = conv_bundle["columns"]
            X1 = encode_align(df_raw.drop(columns=[lead_id_col], errors="ignore"), cols1)
            try:
                probs = model1.predict_proba(X1)[:, 1]
                preds = (probs >= 0.5).astype(int)
                result["conversion_probability"] = probs
                result["converted_pred"] = preds
                result["lead_score_0_100"] = (result["conversion_probability"] * 100).round().astype(int)
            except Exception as e:
                st.warning(f"Model 1 failed: {e}")
        else:
            st.info("Model 1 not available; skipping conversion probability.")

        # Model 2: Funnel Stage
        if funnel_bundle:
            model2 = funnel_bundle["model"]
            cols2  = funnel_bundle["columns"]
            X2 = encode_align(df_raw.drop(columns=[lead_id_col], errors="ignore"), cols2)
            try:
                stage_pred = model2.predict(X2)
                result["predicted_stage"] = stage_pred
            except Exception as e:
                st.warning(f"Model 2 failed: {e}")
        else:
            st.info("Model 2 not available; skipping funnel stage.")

        # Display results
        st.subheader("Predictions")
        st.dataframe(result.head(200))
        st.download_button(
            "Download Predictions CSV",
            result.to_csv(index=False).encode("utf-8"),
            file_name="advanced_predictions.csv",
            mime="text/csv"
        )

        # Simple charts if available
        if "predicted_stage" in result.columns:
            st.subheader("Funnel Stage Distribution")
            st.bar_chart(result["predicted_stage"].value_counts())

        if "lead_score_0_100" in result.columns:
            st.subheader("Top Leads by Score")
            st.dataframe(result.sort_values("lead_score_0_100", ascending=False).head(20))

    elif not uploaded:
        st.info("Upload a CSV to run the trained models.")

# --------------------------------
# Tab 3: Model Management
# --------------------------------
with tabs[2]:
    st.subheader("Model Management")
    st.write("This section shows available models and saved outputs.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Models Detected**")
        st.write(f"- Model 1 (Conversion): {'Present' if conv_bundle else 'Missing'}")
        st.write(f"- Model 2 (Funnel): {'Present' if funnel_bundle else 'Missing'}")
        st.write(f"- Model 3 (Lead RF): {'Present' if lead_rf_bundle else 'Missing'}")

    with c2:
        st.markdown("**Saved Outputs (from main.py)**")
        st.write(f"- conversion_predictions.csv: {'Present' if CONV_OUT_PATH.exists() else 'Missing'}")
        st.write(f"- funnel_predictions.csv: {'Present' if FUNNEL_OUT_PATH.exists() else 'Missing'}")

    st.markdown("---")
    st.write("How to prepare:")
    st.code("python main.py", language="bash")
    st.write("Then come back here and use Advanced Scoring to upload and score any CSV with your trained models.")
=======
# UI/app.py
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import joblib

# ---------------------------
# Paths and model loading
# ---------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONV_MODEL_PATH    = PROJECT_ROOT / "models" / "conversion_model.joblib"   # Model 1 (LogReg)
FUNNEL_MODEL_PATH  = PROJECT_ROOT / "models" / "funnel_model.joblib"       # Model 2 (RF)
LEAD_RF_MODEL_PATH = PROJECT_ROOT / "models" / "lead_scoring_rf.joblib"    # Model 3 (optional RF)

# Saved CSV outputs (optional to display)
CONV_OUT_PATH   = PROJECT_ROOT / "data" / "conversion_predictions.csv"
FUNNEL_OUT_PATH = PROJECT_ROOT / "data" / "funnel_predictions.csv"

st.set_page_config(page_title="IntenSync - Lead Scoring", layout="wide")

# ---------------------------
# Styles (minimal)
# ---------------------------
st.markdown("""
<style>
:root {
  --brandBg: #DDF4E7;
  --brandPrimary: #234C6A;
  --brandText: #1B3C53;
  --brandAccent: #D2C1B6;
}
html, body, [class*="css"] { color: var(--brandText); }
.block-container { padding-top: 1.5rem; }
h1,h2,h3 { color: var(--brandPrimary); }
div[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.stButton>button {
  background: var(--brandPrimary); color: var(--brandAccent);
  border-radius: 20px; border: none; padding: 0.5rem 1rem;
}
.stButton>button:hover { background: #456882; }
.stTabs [data-baseweb="tab-list"] { gap: 1rem; border-bottom: 1px solid #234C6A20; }
.stTabs [data-baseweb="tab"] { font-weight: 700; color: var(--brandPrimary); }
.stDataFrame { border-radius: 10px; }
.small-hint { color: #5a7a8e; font-size: 13px; }
.badge-ok { color: #1b7f4e; font-weight: 600; }
.badge-miss { color: #7a2f2f; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Helpers
# ---------------------------
def tidy_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
                  .str.replace(r"\s+", "_", regex=True)
                  .str.replace(r"[()]", "", regex=True)
    )
    return df

def encode_align(df: pd.DataFrame, train_cols: list) -> pd.DataFrame:
    """One-hot encode object cols and align to training column order."""
    df = tidy_columns(df)
    cat_cols = df.select_dtypes(include=["object"]).columns
    df = pd.get_dummies(df, columns=cat_cols, drop_first=True)
    # add missing columns from training
    for c in train_cols:
        if c not in df.columns:
            df[c] = 0
    # remove extras not in training & order columns
    df = df[train_cols]
    return df

def load_bundle(path: Path):
    try:
        if path.exists():
            return joblib.load(path)
        return None
    except Exception as e:
        st.warning(f"Could not load: {path.name}. Error: {e}")
        return None

def map_stage_heuristic(row_dict: dict) -> str:
    """Fallback stage logic for single-lead demo if no funnel model is used."""
    w = {
        "Email_Opened": 5,
        "Link_Clicked": 10,
        "Form_Filled": 15,
        "Demo_Requested": 20,
        "Pricing_Page_Viewed": 15,
        "Webinar_Attended": 25,
        "Contact_Sales": 30,
    }
    score = sum(w[k] for k, v in row_dict.items() if k in w and v)
    if score >= 25: return "Action"
    if score >= 12: return "Consideration"
    if score >= 5:  return "Interest"
    return "Awareness"

def to_lead_score_0_100(engagement: int) -> int:
    max_possible = 5+10+15+20+15+25+30  # 120
    val = round((engagement / max_possible) * 100)
    return min(100, max(0, val))

def compute_engagement_from_flags(flags: dict) -> int:
    weights = {
        "Email_Opened": 5,
        "Link_Clicked": 10,
        "Form_Filled": 15,
        "Demo_Requested": 20,
        "Pricing_Page_Viewed": 15,
        "Webinar_Attended": 25,
        "Contact_Sales": 30,
    }
    return sum(weights[k] if flags.get(k, False) else 0 for k in weights)

# ---------------------------
# Header (no images)
# ---------------------------
st.title("IntenSync – Lead Intelligence")
st.caption("This app mirrors your HTML demo and can also run trained Python models on uploaded CSVs.")

# ---------------------------
# Load models (if present)
# ---------------------------
conv_bundle    = load_bundle(CONV_MODEL_PATH)      # {"model": clf, "columns": [...]}
funnel_bundle  = load_bundle(FUNNEL_MODEL_PATH)    # {"model": clf, "columns": [...], "classes_":[...]}
lead_rf_bundle = load_bundle(LEAD_RF_MODEL_PATH)   # optional

st.sidebar.header("Model status")
st.sidebar.write(f"Model 1 (Conversion): {'Available' if conv_bundle else 'Missing'}")
st.sidebar.write(f"Model 2 (Funnel):     {'Available' if funnel_bundle else 'Missing'}")
st.sidebar.write(f"Model 3 (Lead RF):    {'Available' if lead_rf_bundle else 'Missing'}")

# ---------------------------
# Tabs
# ---------------------------
tabs = st.tabs(["Basic Scoring", "Advanced Scoring", "Model Management"])

# --------------------------------
# Tab 1: Basic Scoring (checkbox demo)
# --------------------------------
with tabs[0]:
    st.subheader("Basic Scoring")
    st.write("Select the activities the lead has performed to determine their funnel stage and a 0–100 lead score.")

    with st.form("basic_form"):
        colA, colB = st.columns([1,1])

        with colA:
            lead_id   = st.text_input("Lead ID (optional)", "")
            lead_name = st.text_input("Lead Name / Email (optional)", "")

        with colB:
            st.write("Activities")
            Email_Opened        = st.checkbox("Email Opened")
            Link_Clicked        = st.checkbox("Link Clicked")
            Form_Filled         = st.checkbox("Form Filled")
            Demo_Requested      = st.checkbox("Demo Requested")
            Pricing_Page_Viewed = st.checkbox("Pricing Page Viewed")
            Webinar_Attended    = st.checkbox("Webinar Attended")
            Contact_Sales       = st.checkbox("Contact Sales")

        submitted = st.form_submit_button("Score Lead")

    if "basic_table" not in st.session_state:
        st.session_state.basic_table = pd.DataFrame(
            columns=["LeadID","Name","Engagement","Stage","LeadScore_0_100"]
        )

    if submitted:
        flags = {
            "Email_Opened": Email_Opened,
            "Link_Clicked": Link_Clicked,
            "Form_Filled": Form_Filled,
            "Demo_Requested": Demo_Requested,
            "Pricing_Page_Viewed": Pricing_Page_Viewed,
            "Webinar_Attended": Webinar_Attended,
            "Contact_Sales": Contact_Sales,
        }
        engagement = compute_engagement_from_flags(flags)
        stage = map_stage_heuristic(flags)
        score100 = to_lead_score_0_100(engagement)

        st.success(f"Engagement: {engagement} | Stage: {stage} | Lead Score: {score100}")
        new_row = pd.DataFrame([{
            "LeadID": lead_id or f"LD-{str(len(st.session_state.basic_table)+1).zfill(4)}",
            "Name": lead_name or "-",
            "Engagement": engagement,
            "Stage": stage,
            "LeadScore_0_100": score100
        }])
        st.session_state.basic_table = pd.concat([st.session_state.basic_table, new_row], ignore_index=True)

    if len(st.session_state.basic_table):
        st.dataframe(st.session_state.basic_table.iloc[::-1].reset_index(drop=True))
        st.download_button(
            "Download CSV",
            st.session_state.basic_table.to_csv(index=False).encode("utf-8"),
            file_name="scored_leads_basic.csv",
            mime="text/csv"
        )

    st.caption("Weights: Email 5, Click 10, Form 15, Demo 20, Pricing 15, Webinar 25, Contact 30. Stage mapping: <5 Awareness, 5–11 Interest, 12–24 Consideration, ≥25 Action.")

# --------------------------------
# Tab 2: Advanced Scoring (run trained models on CSV)
# --------------------------------
with tabs[1]:
    st.subheader("Advanced Scoring (Models)")
    st.write("Upload a CSV of leads. We will run available models on it and return predictions.")

    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    run_models = st.button("Run Models")

    if uploaded and run_models:
        df_raw = pd.read_csv(uploaded)
        df_raw = tidy_columns(df_raw)

        # Keep a copy of an ID column if present
        lead_id_col = "LeadID" if "LeadID" in df_raw.columns else df_raw.columns[0]
        result = pd.DataFrame({lead_id_col: df_raw[lead_id_col]})

        # Model 1: Conversion Probability -> lead score 0-100
        if conv_bundle:
            model1 = conv_bundle["model"]
            cols1  = conv_bundle["columns"]
            X1 = encode_align(df_raw.drop(columns=[lead_id_col], errors="ignore"), cols1)
            try:
                probs = model1.predict_proba(X1)[:, 1]
                preds = (probs >= 0.5).astype(int)
                result["conversion_probability"] = probs
                result["converted_pred"] = preds
                result["lead_score_0_100"] = (result["conversion_probability"] * 100).round().astype(int)
            except Exception as e:
                st.warning(f"Model 1 failed: {e}")
        else:
            st.info("Model 1 not available; skipping conversion probability.")

        # Model 2: Funnel Stage
        if funnel_bundle:
            model2 = funnel_bundle["model"]
            cols2  = funnel_bundle["columns"]
            X2 = encode_align(df_raw.drop(columns=[lead_id_col], errors="ignore"), cols2)
            try:
                stage_pred = model2.predict(X2)
                result["predicted_stage"] = stage_pred
            except Exception as e:
                st.warning(f"Model 2 failed: {e}")
        else:
            st.info("Model 2 not available; skipping funnel stage.")

        # Display results
        st.subheader("Predictions")
        st.dataframe(result.head(200))
        st.download_button(
            "Download Predictions CSV",
            result.to_csv(index=False).encode("utf-8"),
            file_name="advanced_predictions.csv",
            mime="text/csv"
        )

        # Simple charts if available
        if "predicted_stage" in result.columns:
            st.subheader("Funnel Stage Distribution")
            st.bar_chart(result["predicted_stage"].value_counts())

        if "lead_score_0_100" in result.columns:
            st.subheader("Top Leads by Score")
            st.dataframe(result.sort_values("lead_score_0_100", ascending=False).head(20))

    elif not uploaded:
        st.info("Upload a CSV to run the trained models.")

# --------------------------------
# Tab 3: Model Management
# --------------------------------
with tabs[2]:
    st.subheader("Model Management")
    st.write("This section shows available models and saved outputs.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Models Detected**")
        st.write(f"- Model 1 (Conversion): {'Present' if conv_bundle else 'Missing'}")
        st.write(f"- Model 2 (Funnel): {'Present' if funnel_bundle else 'Missing'}")
        st.write(f"- Model 3 (Lead RF): {'Present' if lead_rf_bundle else 'Missing'}")

    with c2:
        st.markdown("**Saved Outputs (from main.py)**")
        st.write(f"- conversion_predictions.csv: {'Present' if CONV_OUT_PATH.exists() else 'Missing'}")
        st.write(f"- funnel_predictions.csv: {'Present' if FUNNEL_OUT_PATH.exists() else 'Missing'}")

    st.markdown("---")
    st.write("How to prepare:")
    st.code("python main.py", language="bash")
    st.write("Then come back here and use Advanced Scoring to upload and score any CSV with your trained models.")
>>>>>>> 9d9f03bd3a3608aac50feac35cd0714e45fcf573
