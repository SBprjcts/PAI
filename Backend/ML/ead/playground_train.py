import pandas as pd
import numpy as np
from pyod.models.iforest import IForest
from sklearn.preprocessing import StandardScaler
import joblib


def vectorize_encode(csv_path: str, clip_extreme_numeric: bool = False) -> pd.DataFrame:
    """
    Vectorize data from a valid csv file, and encode it by featurizing.
    Returns a dataframe.
    """
    df = pd.read_csv(csv_path)

    df["date"] = pd.to_datetime(df["date"])

        # --- Date handling: parse and extract numeric features, then drop raw datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["dayofweek"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
    df = df.drop(columns=["date"])

    # Look at the first few rows
    print(df)

    cat_cols = ["amount", "vendor", "description", "category"]
    df = pd.get_dummies(df, columns=cat_cols, drop_first=False)

    # (Optional) Clip extreme numeric outliers before modeling (robustness)
    if clip_extreme_numeric:
        df["amount"] = df["amount"].clip(lower=df["amount"].quantile(0.01),
                                        upper=df["amount"].quantile(0.99))

    return df


path = "training_data/basic_training_data.csv"

fdf = vectorize_encode(path)

print(fdf)

# (Optional) Learns z = ( ( x - mean) / standard deviation) per column for later use of LOF/KNN 
scaler = StandardScaler()
X = scaler.fit_transform(fdf.values)

# Train anomaly model using PyOD Isolation Forest algorithm.
# Contamination = expected % outliers
# Random state = 42: is a parameter used to control the randomness of an algorithm. It functions as a seed 
# for the pseudo-random number generator used within the algorithm. means that any operations involving 
# randomness will produce the same results every time you run your code
# Build many random trees that “isolate” points; anomalies are isolated in fewer splits (short paths).
clf = IForest(contamination=0.05, random_state=42)
clf.fit(X)

# decision_scores_: higher = more anomalous (continuous).
# labels_: binary (1=outlier, 0=inlier) using the learned threshold consistent with contamination.
scores = clf.decision_scores_
labels = clf.labels_

# Attach results back to the original rows
df_result = fdf.copy()
df_result["anomaly_score"] = scores
df_result["is_outlier"] = labels


print(f"FINAL MATRIX:\n\n{df_result}")
pd.ExcelWriter("training_data/")

# # ---------- 6) SAVE ARTIFACTS (model + scaler + feature_columns) ----------
# artifact = {
#     "model": clf,
#     "scaler": scaler,
#     "feature_columns": feature_columns,
#     "featurize_version": "v1"  # bump this if you change featurize()
# }
# joblib.dump(artifact, "anomaly_iforest.joblib")

# # ---------- 7) HOW TO SCORE NEW DATA LATER ----------
# def prepare_like_training(df_new: pd.DataFrame, feature_columns: list) -> np.ndarray:
#     """
#     Apply the exact same featurization and align columns:
#     - Create all training-time dummy columns (missing -> 0)
#     - Drop any unseen extra dummies in new data
#     - Preserve column order
#     """
#     F = featurize(df_new)

#     # Add missing columns (from training) with zeros
#     for col in feature_columns:
#         if col not in F.columns:
#             F[col] = 0

#     # Drop any extra columns that weren’t in training
#     F = F[feature_columns]

#     return F.values

# # Example: new incoming rows
# new_df = pd.DataFrame({
#     "Date": ["2025-09-08","2025-09-09"],
#     "Amount": [70, 5000],
#     "Category": ["Food","Shopping"],
#     "PaymentType": ["Credit","Credit"],
#     "Location": ["Toronto","Ottawa"]
# })

# # Load artifacts
# artifact_loaded = joblib.load("anomaly_iforest.joblib")
# clf_loaded = artifact_loaded["model"]
# scaler_loaded = artifact_loaded["scaler"]
# feature_columns_loaded = artifact_loaded["feature_columns"]

# X_new = prepare_like_training(new_df, feature_columns_loaded)
# X_new_scaled = scaler_loaded.transform(X_new)

# new_scores = clf_loaded.decision_function(X_new_scaled)  # same as negative outlier factor (higher=worse)
# new_labels = clf_loaded.predict(X_new_scaled)            # 1 = outlier, 0 = inlier

# new_df_result = new_df.copy()
# new_df_result["anomaly_score"] = new_scores
# new_df_result["is_outlier"] = new_labels

# print("\n--- NEW DATA SCORES ---")
# print(new_df_result)
