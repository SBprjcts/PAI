import joblib
from sklearn.feature_extraction.text import HashingVectorizer, TfidfVectorizer

# Load your trained pipeline
model = joblib.load("../ML/saved_models/bill_categorizer_20250817T233000Z.joblib")

# Try a sample bill
sample_vendor = "Hydro One"
sample_desc = "Monthly electricity bill for office"
text = f"{sample_vendor} {sample_desc}".lower()

# Predict
prediction = model.predict([text])
print("Predicted category:", prediction[0])