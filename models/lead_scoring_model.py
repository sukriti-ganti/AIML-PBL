# models/lead_scoring_model.py
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import random

# -----------------------------
# Constants & helpers
# -----------------------------
np.random.seed(42)
random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH   = PROJECT_ROOT / "data" / "leads_data.csv"
OUT_PATH   = PROJECT_ROOT / "data" / "lead_score_predictions.csv"
PLOT_PATH  = PROJECT_ROOT / "reports" / "feature_importance.png"
MODEL_PATH = PROJECT_ROOT / "models" / "lead_scoring_rf.joblib"


def generate_leads_data(n_leads=1000) -> pd.DataFrame:
    """Generate synthetic leads data with simple behavior flags."""
    data = {
        'LeadID': [f"LD{i:04d}" for i in range(1, n_leads + 1)],
        'Email_Opened': np.random.choice([0, 1], size=n_leads, p=[0.3, 0.7]),
        'Link_Clicked': np.random.choice([0, 1], size=n_leads, p=[0.6, 0.4]),
        'Form_Filled': np.random.choice([0, 1], size=n_leads, p=[0.85, 0.15]),
        'Demo_Requested': np.random.choice([0, 1], size=n_leads, p=[0.92, 0.08]),
        'Pricing_Page_Viewed': np.random.choice([0, 1], size=n_leads, p=[0.88, 0.12]),
        'Webinar_Attended': np.random.choice([0, 1], size=n_leads, p=[0.95, 0.05]),
        'Contact_Sales': np.random.choice([0, 1], size=n_leads, p=[0.98, 0.02]),
        'Industry': np.random.choice(
            ['Technology', 'Healthcare', 'Finance', 'Education', 'Retail'],
            size=n_leads
        ),
        'Company_Size': np.random.choice(['Small', 'Medium', 'Large'], size=n_leads)
    }
    return pd.DataFrame(data)


def run():
    # Ensure dirs exist
    (PROJECT_ROOT / "data").mkdir(exist_ok=True)
    (PROJECT_ROOT / "reports").mkdir(exist_ok=True)
    (PROJECT_ROOT / "models").mkdir(exist_ok=True)

    print("Loading:", CSV_PATH)

    # -----------------------------
    # Block 2: Generate or load data
    # -----------------------------
    try:
        df = pd.read_csv(CSV_PATH)
        print(f"Loaded existing data from {CSV_PATH}")
    except FileNotFoundError:
        print(f"Generating new data at {CSV_PATH}")
        df = generate_leads_data()
        df.to_csv(CSV_PATH, index=False)

    # Clean column names
    df.columns = (df.columns.str.strip()
                              .str.replace(r"\s+", "_", regex=True)
                              .str.replace(r"[()]", "", regex=True))

    # Derive Engagement_Score & categorical Lead_Score (only if not present)
    if 'Engagement_Score' not in df.columns:
        df['Engagement_Score'] = (
            df.get('Email_Opened', 0) * 5 +
            df.get('Link_Clicked', 0) * 10 +
            df.get('Form_Filled', 0) * 15 +
            df.get('Demo_Requested', 0) * 20 +
            df.get('Pricing_Page_Viewed', 0) * 15 +
            df.get('Webinar_Attended', 0) * 25 +
            df.get('Contact_Sales', 0) * 30
        )
        noise = np.random.normal(0, 5, size=len(df))
        adjusted = df['Engagement_Score'] + noise

        conditions = [
            (adjusted < 20),
            (adjusted >= 20) & (adjusted < 40),
            (adjusted >= 40) & (adjusted < 60),
            (adjusted >= 60)
        ]
        choices = ['Cold', 'Warm', 'Hot', 'Hot Lead']
        df['Lead_Score'] = np.select(conditions, choices)

    TARGET_COL = "Lead_Score"
    LEAD_ID_COL = "LeadID" if "LeadID" in df.columns else df.columns[0]

    print("Shape:", df.shape)
    print("Target counts:\n", df[TARGET_COL].value_counts())

    # -----------------------------
    # Block 3: Clean & encode
    # -----------------------------
    df = df.dropna(subset=[TARGET_COL, LEAD_ID_COL])
    engagement_map = df[[LEAD_ID_COL, 'Engagement_Score']].copy()

    X = df.drop(columns=[TARGET_COL, LEAD_ID_COL])
    y = df[TARGET_COL]

    cat_cols = X.select_dtypes(include=["object"]).columns
    X = pd.get_dummies(X, columns=cat_cols, drop_first=True)

    print(f"Features shape: {X.shape}")
    print("Target distribution:", y.value_counts(normalize=True).round(3).to_dict())

    # -----------------------------
    # Block 4: Train/test split
    # -----------------------------
    X_train, X_test, y_train, y_test, id_train, id_test = train_test_split(
        X, y, df[LEAD_ID_COL], test_size=0.2, random_state=42, stratify=y
    )
    print(f"Training set: {X_train.shape[0]}  |  Testing set: {X_test.shape[0]}")

    # -----------------------------
    # Block 5: Train Random Forest
    # -----------------------------
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features='sqrt',
        bootstrap=True,
        class_weight="balanced",
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    proba  = model.predict_proba(X_test)

    print("Random Forest model trained successfully!")

    # -----------------------------
    # Block 6: Evaluate
    # -----------------------------
    print("\n[Model 3] Metrics (Random Forest - Lead Scoring):")
    print("Accuracy:", round(accuracy_score(y_test, y_pred), 4))
    print("\nClassification report:\n", classification_report(y_test, y_pred, digits=4))
    cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
    print("Confusion Matrix:\n", pd.DataFrame(cm, index=model.classes_, columns=model.classes_))

    fi = pd.DataFrame({'Feature': X.columns, 'Importance': model.feature_importances_}) \
           .sort_values('Importance', ascending=False)
    print("\nTop 5 Feature Importances:")
    print(fi.head())

    # -----------------------------
    # Block 7: Visualize feature importance
    # -----------------------------
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=fi.head(10))
    plt.title('Top 10 Feature Importance in Lead Scoring (Random Forest)')
    plt.tight_layout()
    plt.savefig(PLOT_PATH)
    print(f"Feature importance plot saved to {PLOT_PATH}")
    # plt.show()  # enable if you want an interactive window locally

    # -----------------------------
    # Block 8: Save predictions for UI
    # -----------------------------
    out = pd.DataFrame({LEAD_ID_COL: id_test.values, "predicted_label": y_pred})
    for i, cls in enumerate(model.classes_):
        out[f"confidence_{cls}"] = proba[:, i]

    out = out.merge(engagement_map, on=LEAD_ID_COL, how='left')

    hot_col = "confidence_Hot Lead" if "Hot Lead" in model.classes_ else None
    if hot_col:
        out = out.sort_values(hot_col, ascending=False)

    out.to_csv(OUT_PATH, index=False)
    print(f"\nSaved predictions → {OUT_PATH}")
    print("\nPreview:")
    print(out.head())

    joblib.dump({"model": model, "columns": X.columns.tolist(), "classes_": list(model.classes_)}, MODEL_PATH)
    print("Saved model →", MODEL_PATH)


if __name__ == "__main__":
    run()
