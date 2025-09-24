# test_model.py
from pathlib import Path
import sys
import joblib

# ---- Locate project root (Backend) and models dir ----
# This file is likely at Backend/app/ML/test_model.py → parents[2] = Backend
ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "ML" / "saved_models"

print(f"Looking for models in: {MODELS_DIR}")

# ---- Pick latest .joblib safely ----
models = sorted(MODELS_DIR.glob("*.joblib"))
if not models:
    print(f"ERROR: No .joblib models found in {MODELS_DIR}")
    print("Tip: run your retrain script so it saves into ML/saved_models.")
    sys.exit(1)

latest_model = models[-1]
print(f"Loading model: {latest_model}")

# ---- Load model with friendly error ----
try:
    model = joblib.load(latest_model)
except Exception as e:
    print(f"ERROR: Failed to load model {latest_model}\n{e}")
    sys.exit(1)

# ---- Simple smoke test prediction ----
sample_vendor = "Hydro One"
sample_desc = "Monthly electricity bill for office"
text = f"{sample_vendor} {sample_desc}".lower().strip()

pred = model.predict([text])[0]
print("Predicted category:", pred)
