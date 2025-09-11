import pandas as pd
import numpy as np
from pyod.models.iforest import IForest
from sklearn.preprocessing import StandardScaler
import joblib
import hashlib
import datetime


def vectorize_encode(csv_path: str, clip_extreme_numeric: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read CSV -> feature engineer -> one-hot encode categoricals.
    Returns (features_df, original_df_with_same_rows).
    """
    df = pd.read_csv(csv_path)

    # Keep a copy of the original rows for attaching results later
    df_orig = df.copy()

    # --- Date handling: parse and extract numeric features, then drop raw datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["dayofweek"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
    df = df.drop(columns=["date"])

    # --- Numeric column(s)
    # Keep amount numeric; optional winsorization
    if clip_extreme_numeric:
        df["amount"] = df["amount"].clip(
            lower=df["amount"].quantile(0.01),
            upper=df["amount"].quantile(0.99)
        )


    df["desc_hash"] = df["description"].astype(str).apply(lambda s: hash_text_to_int(s, buckets=512))
    df = df.drop(columns=["description"])

    # --- Choose categoricals to one-hot. Avoid high-cardinality 'description' (drop or hash).
    # If you really need description, consider hashing or text embeddings instead of get_dummies.
    cat_cols = ["vendor", "category"]  # <- not 'amount'; avoid 'description' for now
    present_cat = [c for c in cat_cols if c in df.columns]
    df = pd.get_dummies(df, columns=present_cat, drop_first=False)

    # Ensure everything left is numeric (object columns that slipped through -> drop)
    non_numeric = df.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric:
        # simplest: drop them; or convert if you know how
        df = df.drop(columns=non_numeric)

    # Fill any NaNs that may have arisen (scalers/models expect finite values)
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df, df_orig


def hash_text_to_int(text: str, buckets: int = 512) -> int:
    if pd.isna(text):
        return 0
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(h, 16) % buckets


# # ---- Train pipeline
# path = "training_data/basic_training_data.csv"
# X_df, df_orig = vectorize_encode(path, clip_extreme_numeric=False)

# print("FEATURE MATRIX (pre-scale):")
# print(X_df.head())

# # Scale (not required for IsolationForest but useful for LOF/KNN swaps)
# # (Optional) Learns z = ( ( x - mean) / standard deviation) per column for later use of LOF/KNN 
# scaler = StandardScaler()
# X = scaler.fit_transform(X_df.values)

# # PyOD Isolation Forest
# clf = IForest(contamination=0.05, random_state=42)
# clf.fit(X)


# # Scores & labels
# scores = clf.decision_scores_  # higher = more anomalous
# labels = clf.labels_           # 1 = outlier, 0 = inlier

# # Attach back to original rows
# df_result = df_orig.copy()
# df_result["anomaly_score"] = scores
# df_result["is_outlier"] = labels
# print("\nRESULTS:")
# print(df_result.sort_values("anomaly_score", ascending=False))

# # Save artifacts to reuse on new data
# # artifact = {
# #     "model": clf,
# #     "scaler": scaler,
# #     "feature_columns": X_df.columns.tolist()
# # }
# artifact = {
#     "model": clf,
#     "scaler": scaler,
#     "feature_columns": X_df.columns.tolist(),
#     "featurize_version": "v1",
#     "hash_buckets": 512,
#     "categoricals": ["vendor", "category"]
# }
# joblib.dump(artifact, f"saved_models/anomaly_iforest_{str(datetime.datetime.now()).replace(" ", "_").replace(":", "_")}.joblib")

