"""
train_fraud_pyod.py
---------------------------------
Trains and retrains a PyOD-based anomaly detector using:
    - amount (numeric)
    - category (text)
    - is_fraud (optional binary label)

Uses: HashingVectorizer + TruncatedSVD + PyOD ECOD
Can be retrained incrementally by adding one new expense.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.decomposition import TruncatedSVD
from pyod.models.ecod import ECOD
from .pyod_wrappers import PyODSVDWrapper
from scipy import sparse as sp


# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
# DATA = ROOT / "training_data" / "financial_fraud_detection_dataset.csv"
DATA = ROOT / "training_data" / "basic_training_data.csv"
OUT = ROOT / "saved_models"
OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------
def log1p_amt(x):
    try:
        x = float(x)
        if np.isnan(x): x = 0.0
    except Exception:
        x = 0.0
    return np.log1p(max(0.0, x))


def make_sparse_features(categories: list[str], amounts: np.ndarray, vec):
    """Builds the sparse text + numeric matrix"""
    X_text = vec.transform(categories)  # hashed text
    amt_raw = np.asarray(amounts, dtype=np.float32).reshape(-1, 1)
    med = float(np.median(amt_raw))
    mad = float(np.median(np.abs(amt_raw - med))) or 1.0
    amt_scaled = (amt_raw - med) / (mad + 1e-6)
    amt_log = np.array([log1p_amt(a) for a in amounts], dtype=np.float32).reshape(-1, 1)
    if sp is not None:
        X_amt_scaled = sp.csr_matrix(amt_scaled)
        X_amt_log = sp.csr_matrix(amt_log)
        X = sp.hstack([X_text, X_amt_scaled, X_amt_log], format="csr")
    else:
        X = np.hstack([X_text.toarray(), amt_scaled, amt_log])
    return X


def build_vectorizer():
    return HashingVectorizer(
        n_features=2**18,
        alternate_sign=False,
        ngram_range=(1, 2),
        norm="l2",
    )


# ---------------------------------------------------------------------
# TRAIN FUNCTION
# ---------------------------------------------------------------------
def train_fraud_model() -> dict:
    """Trains a PyOD ECOD model on amount + category + is_fraud."""
    if not DATA.exists():
        raise FileNotFoundError(f"Training CSV not found: {DATA}")

    df = pd.read_csv(DATA, encoding="utf-8-sig")
    # df.drop(columns=["transaction_id","timestamp","sender_account","receiver_account","transaction_type","location","device_used","fraud_type","time_since_last_transaction","spending_deviation_score","velocity_score","geo_anomaly_score","payment_channel","ip_address","device_hash"])
    df.columns = [c.strip().lower() for c in df.columns]

    # sanity check
    if not {"amount", "category"}.issubset(df.columns):
        raise ValueError("Dataset must have at least 'amount' and 'category' columns.")

    # combine features
    df["category"] = df["category"].astype(str).fillna("").str.lower().str.strip()
    df["is_fraud"] = df.get("is_fraud", 0).fillna(0).astype(int)

    vec = build_vectorizer()
    Xs = make_sparse_features(df["category"].tolist(), df["amount"].to_numpy(copy=False), vec)

    svd = TruncatedSVD(n_components=200, random_state=42)
    Z = svd.fit_transform(Xs)

    detector = ECOD(contamination=0.04)
    detector.fit(Z)
    wrapped = PyODSVDWrapper(svd, detector)

    # save models
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pointer = OUT / "fraud_anomaly.joblib"
    snap = OUT / f"fraud_anomaly_{timestamp}.joblib"

    tmp = pointer.with_suffix(".joblib.tmp")
    joblib.dump(wrapped, tmp)
    tmp.replace(pointer)
    joblib.dump(wrapped, snap)

    print(f"✅ Model trained and saved: {pointer.name}")
    return {"model_path": str(pointer), "rows_trained": len(df)}


# ---------------------------------------------------------------------
# RETRAIN FUNCTION
# ---------------------------------------------------------------------
def retrain_on_single_expense(category: str, amount: float, is_fraud: int = 0) -> dict:
    """Adds one record, retrains, and returns score."""
    df = pd.read_csv(DATA, encoding="utf-8-sig") if DATA.exists() else pd.DataFrame(
        columns=["amount", "category", "is_fraud"]
    )
    new_row = {"amount": amount, "category": category, "is_fraud": is_fraud}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA, index=False, encoding="utf-8-sig")

    # --- retrain
    result = train_fraud_model()

    # --- score the new row
    latest_model = joblib.load(result["model_path"])
    vec = build_vectorizer()
    X_new = make_sparse_features([category], np.array([amount], dtype=np.float32), vec)
    score = latest_model.decision_function(X_new)[0]
    label = int(score < 0)

    return {
        "category": category,
        "amount": amount,
        "is_fraud": is_fraud,
        "score": float(score),
        "is_anomaly": bool(label),
        "model_path": result["model_path"],
    }

# ---------------------------------------------------------------------
# QUICK SCORE FUNCTION
# ---------------------------------------------------------------------
def get_expense_score(category: str, amount: float) -> dict:
    """
    Quickly loads the latest trained model and returns an anomaly score
    for a single expense (no retraining, no CSV modification).
    """
    # locate the newest model
    model_files = sorted(OUT.glob("fraud_anomaly*.joblib"))
    if not model_files:
        raise FileNotFoundError("No trained model found in saved_models/. Please train first.")
    latest_model_path = model_files[-1]
    model = joblib.load(latest_model_path)

    # rebuild the same vectorizer and feature structure
    vec = build_vectorizer()
    X_new = make_sparse_features([category], np.array([amount], dtype=np.float32), vec)

    # compute anomaly score
    score = float(model.decision_function(X_new)[0])

    return score


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
# if __name__ == "__main__":
#     # Example usage:
#     res = get_expense_score("google", 5085000.99)
#     print(res)
#     # train_fraud_model()
