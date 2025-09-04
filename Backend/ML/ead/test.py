# repair_pointer.py
from pathlib import Path
import joblib, shutil

MODELS = Path(r"C:\Users\alafs\Desktop\PAI\Backend\ML\ead\saved_models")
pointer = MODELS / "expense_anomaly.joblib"
snap    = MODELS / f"expense_anomaly_20250904T041040Z.joblib"  # your snapshot
print(f"snap:{snap}")
print("pointer size:", pointer.stat().st_size if pointer.exists() else "missing")
print("snapshot size:", snap.stat().st_size if snap.exists() else "missing")

# Try loading the snapshot (should not raise)
m = joblib.load(snap)
print("Loaded snapshot OK:", type(m))

# Replace the bad pointer atomically
tmp = pointer.with_suffix(".joblib.tmp")
joblib.dump(m, tmp)          # write a fresh valid file
tmp.replace(pointer)         # atomic rename on same drive

# Double-check that the new pointer loads
m2 = joblib.load(pointer)
print("Pointer now loads:", type(m2))
