# Backend/api/anomaly_api_flask.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Any, Union, Dict
import csv
import joblib
import json
import math
import numpy as np

# --- Optional: use sparse if available (preferred for text features) ---
try:
    from scipy import sparse as sp
except Exception:
    sp = None  # we'll fall back to dense concatenation

from flask import Flask, request, jsonify

# -------------------- Paths & App --------------------
API_DIR = Path(__file__).resolve().parent                 # Backend/api
ROOT    = API_DIR.parent                                  # Backend/
MODELS_DIR = ROOT / "ead" /"saved_models"                 # model artifacts
FEEDBACK_CSV = ROOT / "ead" / "training_data" / "anomaly_feedback.csv"     # where we store human labels

app = Flask(__name__)

# -------------------- Utilities --------------------
def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _safe_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")

def _log1p_or_zero(x: float) -> float:
    try:
        return float(np.log1p(max(0.0, x)))
    except Exception:
        return 0.0

# -------------------- Feature Builder --------------------
def build_vectorizer():
    """
    Match your existing text setup: stateless HashingVectorizer for streaming/online use.
    NOTE: keep this identical to your training code to avoid train/infer skew.
    """
    from sklearn.feature_extraction.text import HashingVectorizer
    return HashingVectorizer(
        n_features=2**20,
        alternate_sign=False,
        ngram_range=(1, 2),
        norm="l2",
    )

def make_features(text: str, amount: Optional[float], vectorizer) -> Union[np.ndarray, "sp.csr_matrix"]:
    """
    Combine text features + a single numeric amount feature.
    - Text -> hashing vectorizer (sparse)
    - Amount -> log1p(amount) as 1-dim feature
    We hstack them into a single feature vector.
    """
    X_text = vectorizer.transform([text])  # sparse
    amt = _log1p_or_zero(amount if amount is not None and not math.isnan(amount) else 0.0)
    amt_arr = np.array([[amt]], dtype=np.float32)

    if sp is not None:
        X_amt = sp.csr_matrix(amt_arr)
        return sp.hstack([X_text, X_amt], format="csr")
    else:
        # Fallback: convert to dense for single row only (safe)
        return np.hstack([X_text.toarray(), amt_arr])

# -------------------- Model Store (hot-reload) --------------------
class AnomalyModelStore:
    """
    Loads latest anomaly model (*.joblib) from ML/saved_models and hot-reloads if a newer file appears.
    Expected model types:
      - sklearn Pipeline (preferred): accept our feature array directly
      - bare estimator (e.g., IsolationForest): we build features with HashingVectorizer + amount and pass to model
    Scoring:
      - Try decision_function() or score_samples(); higher should mean 'more normal'.
      - We'll invert as needed if the model defines anomalies differently.
    """
    def __init__(self, models_dir: Path, filename_hint: str = "expense_anomaly"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.filename_hint = filename_hint
        self._model_path: Optional[Path] = None
        self._mtime: float = 0.0
        self._model: Optional[Any] = None
        self.vectorizer = build_vectorizer()
        self._load_latest()

    def _latest_model_path(self) -> Optional[Path]:
        # Prefer files starting with the hint, else any .joblib
        candidates = sorted(self.models_dir.glob(f"{self.filename_hint}*.joblib"))
        if not candidates:
            candidates = sorted(self.models_dir.glob("*.joblib"))
        return candidates[-1] if candidates else None

    def _load_latest(self):
        p = self._latest_model_path()
        if not p:
            raise FileNotFoundError(f"No model found in {self.models_dir}")
        mtime = p.stat().st_mtime
        if self._model_path != p or self._mtime != mtime:
            print(">>> Loading model from:", p, "size(bytes)=", p.stat().st_size)
            self._model = joblib.load(p)
            self._model_path = p
            self._mtime = mtime

    def _maybe_reload(self):
        p = self._latest_model_path()
        if p and p.stat().st_mtime != self._mtime:
            self._load_latest()

    def score(self, vendor: str, description: str, amount: Optional[float]) -> Tuple[float, Dict[str, Any]]:
        """
        Returns an anomaly score. Convention:
          - More negative -> more anomalous (IsolationForest decision_function behavior).
        """
        self._maybe_reload()
        text = f"{(vendor or '').strip()} {(description or '').strip()}".lower().strip()
        if not text and (amount is None or math.isnan(amount)):
            raise ValueError("At least one of text or amount is required.")

        model = self._model

        # Build features (works for pipelines and bare models)
        X = make_features(text, amount, self.vectorizer)

        # Try standard scoring APIs
        score_val = None
        meta: Dict[str, Any] = {}

        # Prefer decision_function (IsolationForest: larger -> more normal)
        if hasattr(model, "decision_function"):
            s = model.decision_function(X)
            score_val = float(s[0])
            meta["score_api"] = "decision_function"
        elif hasattr(model, "score_samples"):
            s = model.score_samples(X)
            score_val = float(s[0])
            meta["score_api"] = "score_samples"
        else:
            # Fallback: if model has predict with {1(normal), -1(anomaly)}, convert to score
            if hasattr(model, "predict"):
                y = model.predict(X)[0]
                # Map to a crude score: anomaly -> -1.0, normal -> +1.0
                score_val = 1.0 if int(y) == 1 else -1.0
                meta["score_api"] = "predict->proxy"
            else:
                raise RuntimeError("Model exposes neither decision_function nor score_samples nor predict.")

        # Threshold heuristic:
        # For IsolationForest, decision_function > 0 => inlier, < 0 => outlier.
        # If model has 'offset_' (IsolationForest), decision_function is already centered, so 0 is the natural cut.
        threshold = 0.0 if hasattr(model, "offset_") else 0.0
        is_anomaly = bool(score_val < threshold)

        meta.update({
            "threshold": threshold,
            "model_path": str(self._model_path),
        })
        return score_val, {"is_anomaly": is_anomaly, **meta}

# Single global store (mirrors your FastAPI app pattern)
try:
    store = AnomalyModelStore(MODELS_DIR, filename_hint="expense_anomaly")
except FileNotFoundError as e:
    # Defer error to first request; service can still start
    store = None
    _init_error = str(e)
else:
    _init_error = None

# -------------------- Feedback persistence --------------------
def append_feedback(row: Dict[str, Any]) -> None:
    FEEDBACK_CSV.parent.mkdir(parents=True, exist_ok=True)
    write_header = not FEEDBACK_CSV.exists()
    with FEEDBACK_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow([
                "date","amount","vendor","description",
                "is_anomaly_label","model_score","source","created_at_utc"
            ])
        w.writerow([
            row.get("date") or "",
            row.get("amount") if row.get("amount") is not None else "",
            row.get("vendor") or "",
            row.get("description") or "",
            row.get("is_anomaly_label"),
            row.get("model_score"),
            "anomaly_api_flask",
            _now_utc_iso(),
        ])

# -------------------- Routes --------------------
@app.route("/health", methods=["GET"])
def health():
    ok = (store is not None and _init_error is None)
    return jsonify({
        "status": "ok" if ok else "error",
        "init_error": _init_error,
        "models_dir": str(MODELS_DIR),
        "feedback_csv": str(FEEDBACK_CSV),
    }), (200 if ok else 503)

@app.route("/anomaly", methods=["POST"])
def anomaly():
    """
    Request JSON:
      {
        "vendor": "Costco",
        "description": "grocery",
        "amount": 100.0
      }
    Response JSON:
      {
        "is_anomaly": false,
        "score": 0.1432,
        "threshold": 0.0,
        "model_path": ".../saved_models/expense_anomaly_....joblib",
        "score_api": "decision_function"
      }
    """
    global store, _init_error
    if store is None:
        return jsonify({"detail": _init_error or "Model not initialized"}), 503

    data = request.get_json(silent=True) or {}
    vendor = (data.get("vendor") or "").strip()
    description = (data.get("description") or "").strip()
    amount = _safe_float(data.get("amount")) if "amount" in data else None

    try:
        score_val, meta = store.score(vendor, description, amount)
        return jsonify({
            "is_anomaly": bool(meta["is_anomaly"]),
            "score": float(score_val),
            "threshold": float(meta["threshold"]),
            "model_path": meta["model_path"],
            "score_api": meta.get("score_api", "unknown"),
        })
    except FileNotFoundError as e:
        return jsonify({"detail": str(e)}), 503
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@app.route("/feedback", methods=["POST"])
def feedback():
    """
    Let a human confirm/correct whether a record is anomalous.
    Request JSON:
      {
        "vendor": "Costco",
        "description": "grocery",
        "amount": 100.0,
        "is_anomaly_label": false,
        "date": "2025-08-12"  # optional
      }
    """
    data = request.get_json(silent=True) or {}

    # Minimal validation
    if "is_anomaly_label" not in data:
        return jsonify({"detail": "Missing 'is_anomaly_label' (true/false)."}), 400

    vendor = (data.get("vendor") or "").strip()
    description = (data.get("description") or "").strip()
    amount = _safe_float(data.get("amount")) if "amount" in data else None
    date = data.get("date") or ""

    # (Optional) store current model score next to the human label for audit
    score_val = None
    if store is not None:
        try:
            score_val, _ = store.score(vendor, description, amount)
        except Exception:
            score_val = None

    append_feedback({
        "vendor": vendor,
        "description": description,
        "amount": amount,
        "date": date,
        "is_anomaly_label": bool(data["is_anomaly_label"]),
        "model_score": float(score_val) if score_val is not None else "",
    })
    return jsonify({"status": "queued", "message": "Thanks! Your label was recorded."})

# -------------------- Main --------------------
if __name__ == "__main__":
    # Example: python Backend/api/anomaly_api_flask.py
    # Then call:  curl -X POST http://127.0.0.1:5000/anomaly -H "Content-Type: application/json" \
    #             -d '{"vendor":"Costco","description":"grocery","amount":100}'
    app.run(host="0.0.0.0", port=5000, debug=True)
