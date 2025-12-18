# Backend/api/anomaly_api_flask.py
from __future__ import annotations
from pathlib import Path
from flask import Flask, request, jsonify
from ead.train_pyod import get_expense_score

# -------------------- Paths & App --------------------
API_DIR = Path(__file__).resolve().parent                 # Backend/api
ROOT    = API_DIR.parent                                  # Backend/
MODELS_DIR = ROOT / "ML" / "ead" /"saved_models"                 # model artifacts
FEEDBACK_CSV = ROOT / "ead" / "training_data" / "anomaly_feedback.csv"     # where we store human labels

app = Flask(__name__)


@app.route("/ml/ead", methods=["POST"])
def ead():
	"""
	"""
	data = request.get_json(silent=True) or {}
	category = (data.get("category") or "").strip()
	amount = (data.get("amount")) if "amount" in data else None

	if data == {}:
		return jsonify({"error": "Bad Request", "message": "Empty input"}), 400

	if category == "":
		return jsonify({"error": "Bad Request", "message": "Empty category input"}), 400

	try:
		amount = float(amount)
	except (TypeError, ValueError):
		return jsonify({"error": "Bad Request", "message": "amount is not a float"}), 400

	try:
		score = get_expense_score(category, amount)
	except FileNotFoundError:
		return jsonify({"error": "Server Error", "message": "Model file missing"}), 500
	except EOFError:
		return jsonify({"error": "Server Error", "message": "Corrupted model file"}), 500
	except Exception as e:
		return jsonify({"error": "Server Error", "message": str(e)}), 500

	return jsonify({"score": f"{score}"}), 200
    

# -------------------- Main --------------------
if __name__ == "__main__":
  app.run(host="localhost", port=5001, debug=True)
