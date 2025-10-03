# models/funnel_model.py
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

# ------------------------------
# Paths
# ------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH   = PROJECT_ROOT / "data" / "sample_data.csv"          # input dataset
PRED_OUT   = PROJECT_ROOT / "data" / "funnel_predictions.csv"   # output predictions
MODEL_PATH = PROJECT_ROOT / "models" / "funnel_model.joblib"    # saved model


def _safe(df: pd.DataFrame, col: str, default=0):
    """Return a column if present, else a default-valued Series aligned to df."""
    return df[col] if col in df.columns else pd.Series(default, index=df.index)


def derive_funnel_labels(df: pd.DataFrame) -> pd.Series:
    """
    Heuristic labels if the dataset doesn't already contain funnel stages.
    Stages: Awareness -> Interest -> Consideration -> Action
    """
    # Try to use common behavior signals (fallback to 0 if missing)
    visits     = _safe(df, "WebsiteVisits")
    pages      = _safe(df, "PagesViewed")
    time_min   = _safe(df, "TimeSpent_minutes")
    email_sent = _safe(df, "EmailSent")
    email_open = _safe(df, "EmailOpened")
    demo_req   = _safe(df, "Demo_Requested")
    pricing    = _safe(df, "Pricing_Page_Viewed")
    social_eng = _safe(df, "SocialMediaEngagement")
    converted  = _safe(df, "Conversion_Target")  # if 1, treat as Action

    # Simple engagement score (tunable weights)
    score = (
        visits.fillna(0) * 1.0
        + pages.fillna(0) * 0.5
        + time_min.fillna(0) * 0.1
        + email_sent.fillna(0) * 0.5
        + email_open.fillna(0) * 2.0
        + pricing.fillna(0) * 3.0
        + demo_req.fillna(0) * 4.0
        + social_eng.fillna(0) * 0.02
    )

    stage = pd.Series("Awareness", index=df.index, dtype="object")
    stage[(score >= 5)  & (score < 12)] = "Interest"
    stage[(score >= 12) & (score < 25)] = "Consideration"
    # If the dataset already has a conversion flag, mark as Action
    stage[converted == 1] = "Action"
    return stage


def run():
    print("Loading:", CSV_PATH)
    df = pd.read_csv(CSV_PATH)

    # Clean headers
    df.columns = (
        df.columns.str.strip()
                  .str.replace(r"\s+", "_", regex=True)
                  .str.replace(r"[()]", "", regex=True)
    )

    LEAD_ID_COL  = "LeadID" if "LeadID" in df.columns else df.columns[0]
    TARGET_STAGE = "FunnelStage"

    # If no labeled stages, derive them heuristically
    if TARGET_STAGE not in df.columns:
        df[TARGET_STAGE] = derive_funnel_labels(df)

    # Minimal cleaning
    df = df.dropna(subset=[TARGET_STAGE])

    # Features / target
    X = df.drop(columns=[TARGET_STAGE, LEAD_ID_COL], errors="ignore")
    y = df[TARGET_STAGE]

    # Encode categoricals
    cat_cols = X.select_dtypes(include=["object"]).columns
    X = pd.get_dummies(X, columns=cat_cols, drop_first=True)

    # Split
    X_train, X_test, y_train, y_test, id_train, id_test = train_test_split(
        X, y, df[LEAD_ID_COL], test_size=0.2, random_state=42, stratify=y
    )

    # Model
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_split=4,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    print("\n[Model 2] Metrics:")
    print("Accuracy:", round(accuracy_score(y_test, y_pred), 4))
    print(classification_report(y_test, y_pred, digits=4))

    # Save predictions
    out = pd.DataFrame({
        LEAD_ID_COL: id_test.values,
        "predicted_stage": y_pred
    })
    out.to_csv(PRED_OUT, index=False)
    print(f"Saved → {PRED_OUT}")
    print(out.head())

    # Save model bundle (model + training columns + class order)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": model, "columns": X.columns.tolist(), "classes_": list(model.classes_)},
        MODEL_PATH
    )
    print("Saved model →", MODEL_PATH)


if __name__ == "__main__":
    run()
