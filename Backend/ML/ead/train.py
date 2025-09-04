# Backend/ML/EAD/train_expense_anomaly.py
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import HashingVectorizer

# Use scipy.sparse if available (recommended)
try:
    from scipy import sparse as sp
except Exception:
    sp = None

# --- Paths (adjust only if your tree differs) ---
# ROOT = Path(r"C:\Users\alafs\Desktop\PAI")
# DATA_CSV = ROOT / "Backend" / "ML" / "EAD" / "Training_Data" / "training_data.csv"
# OUTDIR   = ROOT / "Backend" / "ML" / "EAD" / "saved_models"
# OUTDIR.mkdir(parents=True, exist_ok=True)


ROOT = Path(__file__).resolve().parent                 # Backend/ML/ead
DATA_CSV = ROOT / "training_data" / "basic_training_data.csv"
OUTDIR = ROOT / "saved_models"
OUTDIR.mkdir(parents=True, exist_ok=True)



def build_vectorizer():
    return HashingVectorizer(
        n_features=2**20,
        alternate_sign=False,
        ngram_range=(1, 2),
        norm="l2",
    )

def log1p_amt(x):
    try:
        x = float(x)
        if np.isnan(x):
            x = 0.0
    except Exception:
        x = 0.0
    return np.log1p(max(0.0, x))

def load_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df.columns = [c.replace("\ufeff", "").strip().lower() for c in df.columns]

    for col in ["vendor", "description"]:
        if col not in df.columns:
            df[col] = ""
    if "amount" not in df.columns:
        df["amount"] = 0.0

    df["vendor"] = df["vendor"].astype(str).fillna("").str.strip()
    df["description"] = df["description"].astype(str).fillna("").str.strip()
    df["text"] = (df["vendor"] + " " + df["description"]).str.lower().str.strip()
    df = df[df["text"].str.len() > 0].reset_index(drop=True)
    return df

def make_features(texts: list[str], amounts: np.ndarray, vectorizer):
    X_text = vectorizer.transform(texts)
    amt_vals = np.array([log1p_amt(a) for a in amounts], dtype=np.float32).reshape(-1, 1)
    if sp is not None:
        X_amt = sp.csr_matrix(amt_vals)          # (n,1)
        return sp.hstack([X_text, X_amt], format="csr")
    else:
        return np.hstack([X_text.toarray(), amt_vals])

def main():
    if not DATA_CSV.exists():
        raise FileNotFoundError(f"Training CSV not found: {DATA_CSV}")

    df = load_data(DATA_CSV)
    vec = build_vectorizer()
    X = make_features(df["text"].tolist(), df["amount"].to_numpy(copy=False), vec)

    # Train IsolationForest (decision_function > 0 => normal; < 0 => anomaly)
    model = IsolationForest(
        n_estimators=200,
        contamination=0.15,
        # contamination="auto",
        random_state=42,
        n_jobs=-1,
    ).fit(X)

    latest = OUTDIR / "expense_anomaly.joblib"  # stable pointer
    snap   = OUTDIR / f"expense_anomaly_{pd.Timestamp.utcnow().strftime('%Y%m%dT%H%M%SZ')}.joblib"
    joblib.dump(model, latest)
    joblib.dump(model, snap)

    print("Saved:", latest)
    print("Saved:", snap)

if __name__ == "__main__":
    main()
