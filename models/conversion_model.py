<<<<<<< HEAD
# models/conversion_model.py
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import joblib

# ------------------------------
# Paths
# ------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "sample_data.csv"
PRED_OUT  = PROJECT_ROOT / "data" / "conversion_predictions.csv"
MODEL_OUT = PROJECT_ROOT / "models" / "conversion_model.joblib"


def run():
    print("Loading:", CSV_PATH)

    # ------------------------------
    # Load & clean data
    # ------------------------------
    df = pd.read_csv(CSV_PATH)

    # Clean column names
    df.columns = (
        df.columns.str.strip()
                  .str.replace(r"\s+", "_", regex=True)
                  .str.replace(r"[()]", "", regex=True)
    )

    TARGET_COL = "Conversion_Target"
    LEAD_ID_COL = "LeadID" if "LeadID" in df.columns else df.columns[0]

    if TARGET_COL not in df.columns:
        raise ValueError(f"Target column '{TARGET_COL}' not found in CSV.")

    print("Shape:", df.shape)
    print("Target counts:\n", df[TARGET_COL].value_counts())

    # ------------------------------
    # Preprocessing
    # ------------------------------
    df = df.dropna()

    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

    # One-hot encode categorical columns
    cat_cols = X.select_dtypes(include=["object"]).columns
    X = pd.get_dummies(X, columns=cat_cols, drop_first=True)

    print("Features after encoding:", X.shape[1])

    # ------------------------------
    # Train/test split
    # ------------------------------
    X_train, X_test, y_train, y_test, id_train, id_test = train_test_split(
        X, y, df[LEAD_ID_COL], test_size=0.2, random_state=42, stratify=y
    )
    print("Train:", X_train.shape, " Test:", X_test.shape)

    # ------------------------------
    # Train Logistic Regression
    # ------------------------------
    model = LogisticRegression(max_iter=10000, class_weight="balanced", solver="saga")
    model.fit(X_train, y_train)

    # ------------------------------
    # Predictions & metrics
    # ------------------------------
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n[Model 1] Metrics:")
    print("Accuracy:", round(accuracy_score(y_test, y_pred), 4))
    print("ROC-AUC :", round(roc_auc_score(y_test, y_prob), 4))
    print("\nClassification report:\n", classification_report(y_test, y_pred, digits=4))

    # ------------------------------
    # Save predictions
    # ------------------------------
    out = pd.DataFrame({
        LEAD_ID_COL: id_test.values,
        "conversion_probability": y_prob,
        "predicted_label": y_pred
    }).sort_values("conversion_probability", ascending=False)

    out.to_csv(PRED_OUT, index=False)
    print(f"\nSaved predictions → {PRED_OUT}")
    print(out.head())

    # ------------------------------
    # Save model
    # ------------------------------
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "columns": X.columns.tolist()}, MODEL_OUT)
    print("Saved model →", MODEL_OUT)


# Allow both direct execution and pipeline import
if __name__ == "__main__":
    run()
=======
# models/conversion_model.py
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import joblib

# ------------------------------
# Paths
# ------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "sample_data.csv"
PRED_OUT  = PROJECT_ROOT / "data" / "conversion_predictions.csv"
MODEL_OUT = PROJECT_ROOT / "models" / "conversion_model.joblib"


def run():
    print("Loading:", CSV_PATH)

    # ------------------------------
    # Load & clean data
    # ------------------------------
    df = pd.read_csv(CSV_PATH)

    # Clean column names
    df.columns = (
        df.columns.str.strip()
                  .str.replace(r"\s+", "_", regex=True)
                  .str.replace(r"[()]", "", regex=True)
    )

    TARGET_COL = "Conversion_Target"
    LEAD_ID_COL = "LeadID" if "LeadID" in df.columns else df.columns[0]

    if TARGET_COL not in df.columns:
        raise ValueError(f"Target column '{TARGET_COL}' not found in CSV.")

    print("Shape:", df.shape)
    print("Target counts:\n", df[TARGET_COL].value_counts())

    # ------------------------------
    # Preprocessing
    # ------------------------------
    df = df.dropna()

    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

    # One-hot encode categorical columns
    cat_cols = X.select_dtypes(include=["object"]).columns
    X = pd.get_dummies(X, columns=cat_cols, drop_first=True)

    print("Features after encoding:", X.shape[1])

    # ------------------------------
    # Train/test split
    # ------------------------------
    X_train, X_test, y_train, y_test, id_train, id_test = train_test_split(
        X, y, df[LEAD_ID_COL], test_size=0.2, random_state=42, stratify=y
    )
    print("Train:", X_train.shape, " Test:", X_test.shape)

    # ------------------------------
    # Train Logistic Regression
    # ------------------------------
    model = LogisticRegression(max_iter=10000, class_weight="balanced", solver="saga")
    model.fit(X_train, y_train)

    # ------------------------------
    # Predictions & metrics
    # ------------------------------
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n[Model 1] Metrics:")
    print("Accuracy:", round(accuracy_score(y_test, y_pred), 4))
    print("ROC-AUC :", round(roc_auc_score(y_test, y_prob), 4))
    print("\nClassification report:\n", classification_report(y_test, y_pred, digits=4))

    # ------------------------------
    # Save predictions
    # ------------------------------
    out = pd.DataFrame({
        LEAD_ID_COL: id_test.values,
        "conversion_probability": y_prob,
        "predicted_label": y_pred
    }).sort_values("conversion_probability", ascending=False)

    out.to_csv(PRED_OUT, index=False)
    print(f"\nSaved predictions → {PRED_OUT}")
    print(out.head())

    # ------------------------------
    # Save model
    # ------------------------------
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "columns": X.columns.tolist()}, MODEL_OUT)
    print("Saved model →", MODEL_OUT)


# Allow both direct execution and pipeline import
if __name__ == "__main__":
    run()
>>>>>>> 9d9f03bd3a3608aac50feac35cd0714e45fcf573
