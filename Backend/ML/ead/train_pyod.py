# Backend/ML/ead/train_pyod.py
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.decomposition import TruncatedSVD

# Try SciPy sparse (recommended); if missing we’ll dense-convert small arrays
try:
    from scipy import sparse as sp
except Exception:
    sp = None

# --- PyOD ---
from pyod.models.ecod import ECOD  # good default; needs dense

ROOT = Path(__file__).resolve().parent          # Backend/ML/ead
DATA = ROOT / "training_data" / "basic_training_data.csv"
OUT  = ROOT / "saved_models"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------- Feature helpers ----------------
def log1p_amt(x):
    try:
        x = float(x)
        if np.isnan(x): x = 0.0
    except Exception:
        x = 0.0
    return np.log1p(max(0.0, x))

def load_data(p: Path) -> pd.DataFrame:
    df = pd.read_csv(p, encoding="utf-8-sig")
    df.columns = [c.replace("\ufeff","").strip().lower() for c in df.columns]
    for c in ["vendor","description"]:
        if c not in df.columns: df[c] = ""
    if "amount" not in df.columns: df["amount"] = 0.0
    df["vendor"] = df["vendor"].astype(str).fillna("").str.strip()
    df["description"] = df["description"].astype(str).fillna("").str.strip()
    df["text"] = (df["vendor"] + " " + df["description"]).str.lower().str.strip()
    df = df[df["text"].str.len() > 0].reset_index(drop=True)
    if len(df) == 0:
        raise ValueError("No non-empty rows after preprocessing.")
    return df

def build_vectorizer():
    return HashingVectorizer(
        n_features=2**18,        # smaller than 2**20 since we’ll SVD; tweak if needed
        alternate_sign=False,
        ngram_range=(1,2),
        norm="l2",
    )

def make_sparse_features(texts: list[str], amounts: np.ndarray, vec):
    X_text = vec.transform(texts)  # sparse
    amt_raw = np.asarray(amounts, dtype=np.float32).reshape(-1,1)
    # robust scale-ish: center by median, scale by MAD
    med = float(np.median(amt_raw))
    mad = float(np.median(np.abs(amt_raw - med))) or 1.0
    amt_raw_scaled = (amt_raw - med) / (mad + 1e-6)
    amt_log = np.array([log1p_amt(a) for a in amounts], dtype=np.float32).reshape(-1,1)
    if sp is not None:
        X_amt_raw = sp.csr_matrix(amt_raw_scaled)
        X_amt_log = sp.csr_matrix(amt_log)
        X = sp.hstack([X_text, X_amt_raw, X_amt_log], format="csr")
    else:
        # fallback: dense combine (ok for tiny datasets)
        X = np.hstack([X_text.toarray(), amt_raw_scaled, amt_log])
    return X

# ------------- Wrapper so API can still pass sparse X -------------
class PyODSVDWrapper:
    """
    Accepts the SAME sparse feature matrix your API builds.
    Internally:
      - Applies fitted TruncatedSVD to get low-dim dense features
      - Calls PyOD detector.decision_function (outlier score; higher=worse)
      - Converts to 'normality' score (>0 normal, <0 anomaly), so your API keeps threshold=0.0
    """
    def __init__(self, svd: TruncatedSVD, detector):
        self.svd = svd
        self.detector = detector
        # PyOD sets threshold_ from contamination
        if not hasattr(detector, "threshold_"):
            raise ValueError("Detector missing threshold_ (fit with contamination set).")
        self.outlier_threshold_ = float(detector.threshold_)

    def decision_function(self, X):
        # X can be sparse or dense; SVD handles sparse directly
        Z = self.svd.transform(X)               # (n_samples, n_components) dense
        out_scores = self.detector.decision_function(Z)  # higher = more anomalous
        normal_scores = self.outlier_threshold_ - out_scores
        return normal_scores

    def predict(self, X):
        Z = self.svd.transform(X)
        y = self.detector.predict(Z)  # 0=inlier, 1=outlier
        return np.where(y == 0, 1, -1)

def main():
    if not DATA.exists():
        raise FileNotFoundError(f"Training CSV not found: {DATA}")

    df  = load_data(DATA)
    vec = build_vectorizer()
    Xs  = make_sparse_features(df["text"].tolist(), df["amount"].to_numpy(copy=False), vec)

    # Dimensionality reduction: sparse -> low-dim dense
    # Choose components to balance fidelity & speed. 100–300 works well.
    svd = TruncatedSVD(n_components=200, random_state=42)
    Z   = svd.fit_transform(Xs)   # dense array

    # PyOD detector on dense embedding
    detector = ECOD(contamination=0.05)  # tune 0.02–0.10 for sensitivity
    detector.fit(Z)

    wrapped = PyODSVDWrapper(svd, detector)

    # Save pointer atomically + timestamped snapshot
    pointer = OUT / "expense_anomaly.joblib"
    snap    = OUT / f"expense_anomaly_{pd.Timestamp.utcnow().strftime('%Y%m%dT%H%M%SZ')}.joblib"

    tmp = pointer.with_suffix(".joblib.tmp")
    joblib.dump(wrapped, tmp)
    tmp.replace(pointer)
    joblib.dump(wrapped, snap)

    print("Saved:", pointer, "size=", pointer.stat().st_size)
    print("Saved:", snap,    "size=", snap.stat().st_size)

    # quick sanity
    m = joblib.load(pointer)
    test_scores = m.decision_function(Xs[:3])
    print("Sanity decision_function shape:", np.asarray(test_scores).shape)

if __name__ == "__main__":
    main()
