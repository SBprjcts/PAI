import joblib
import pandas as pd
from playground_train import hash_text_to_int
import numpy as np
import glob
import os


def featurize_like_training(df_new: pd.DataFrame, feature_columns: list[int | str]) -> pd.DataFrame:
    """Apply same featurization as training and align to the saved feature schema."""
    # Reuse your training-time function
    F, _orig = vectorize_encode_df(df_new)  # see wrapper below
    # Add any missing training columns
    for col in feature_columns:
        if col not in F.columns:
            F[col] = 0
    # Drop extras and enforce column order
    F = F[feature_columns]
    # Safety: ensure numeric dtype
    return F.apply(pd.to_numeric, errors="coerce").fillna(0.0)

def vectorize_encode_df(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Same as vectorize_encode but takes a DataFrame instead of CSV path."""
    df = df_raw.copy()
    df_orig = df.copy()

    # Date → features
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["dayofweek"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
    df = df.drop(columns=["date"])

    # Numeric
    # (optional) winsorization can be toggled by caller if needed
    # df["amount"] = df["amount"].clip(df["amount"].quantile(0.01), df["amount"].quantile(0.99))

    # Hash text
    if "description" in df.columns:
        df["desc_hash"] = df["description"].astype(str).apply(lambda s: hash_text_to_int(s, buckets=512))
        df = df.drop(columns=["description"])

    # Dummies
    cat_cols = [c for c in ["vendor", "category"] if c in df.columns]
    df = pd.get_dummies(df, columns=cat_cols, drop_first=False)

    # Clean
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    # Drop any non-numerics that might slip in
    non_numeric = df.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric:
        df = df.drop(columns=non_numeric)

    return df, df_orig


# ------- Example: scoring new rows -------
# Find all models that match the naming pattern
files = glob.glob("saved_models/anomaly_iforest_*.joblib")

if not files:
    raise FileNotFoundError("No saved models found!")

# Pick the most recently created one
latest_model_path = max(files, key=os.path.getctime)

# Load it
artifact = joblib.load(latest_model_path)

print(f"Loaded latest model: {latest_model_path}")

clf = artifact["model"]
scaler = artifact["scaler"]
feature_columns = artifact["feature_columns"]

# new_df = pd.DataFrame({
#     "date": ["2025-09-10", "2025-09-11", "2025-12-23"],
#     "amount": [72, 5000, 50050.00],
#     "vendor": ["Starbucks", "Apple", "Spotify"],
#     "description": ["Grande latte", "MacBook Pro", "Music Subscription"],
#     "category": ["Food", "Shopping", "Software"]
# })

path = "training_data/user_data.csv"
new_df = pd.read_csv(path)

X_new_df = featurize_like_training(new_df, feature_columns)
X_new = scaler.transform(X_new_df.values)

new_scores = clf.decision_function(X_new)  # higher = more anomalous
new_labels = clf.predict(X_new)            # 1 = outlier, 0 = inlier

new_out = new_df.copy()
new_out["anomaly_score"] = new_scores
new_out["is_outlier"] = new_labels
print(new_out.sort_values("anomaly_score", ascending=False))