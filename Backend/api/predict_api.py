# Backend/api/predict_api.py
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Tuple
import csv
from datetime import datetime, timezone 
import os
from fastapi.middleware.cors import CORSMiddleware # Makes the API accessible from a frontend running on a different origin


API_DIR = Path(__file__).resolve().parent # Directory of the current file
ROOT = API_DIR.parent # Go up level to get the root directory
MODELS_DIR = ROOT / "ML" / "saved_models" # Directory where models are stored
FEEDBACK_CSV = ROOT / "data" / "feedback.csv" # Path to the feedback CSV file

from app.interface import ModelStore # Import the ModelStore class from the inference module
app = FastAPI(title="Bill Categorization API", version="0.1.0") # Initialize FastAPI app
store = ModelStore(MODELS_DIR) # Initialize the model store with the models directory

app.add_middleware( # Add CORS middleware to allow requests from the frontend
    CORSMiddleware,
    allow_origins=["http://localhost:4200"], # Angular dev server origin so frontend can access the API
    allow_credentials=True, # Allow cookies and authentication headers
    allow_methods=["GET", "POST"], # Allow GET, POST methods only
    allow_headers=["Authorization", "Content-Type", "Accept"] # Allow specific headers
)

class PredictIn(BaseModel): # Validates input data for prediction
    vendor: str = Field(..., min_length=1) # Vendor name must be at least 1 character
    description: str = Field(..., min_length=1) # Description must be at least 1 character

class PredictOut(BaseModel): # Validates output data for prediction
    category: str
    top: List[Tuple[str, float]] # List of tuples containing category and its probability

class FeedbackIn(PredictIn):  # Inherits from PredictIn, adds category field for user feedback
    category: str = Field(..., min_length=1) # Category must be at least 1 character
    date: Optional[str] = None # Kept for potential future use
    amount: Optional[float] = None 

def append_feedback(row: FeedbackIn):
    """Append feedback to the CSV file."""
    FEEDBACK_CSV.parent.mkdir(parents=True, exist_ok=True) # Ensure the parent directory exists
    write_header = not FEEDBACK_CSV.exists() # Check if the CSV file already exists, returns True if it does not exist
    with FEEDBACK_CSV.open("a", newline="", encoding="utf-8") as f: # Open the CSV file in append mode, create if it doesn't exist
        w = csv.writer(f) # Create a CSV writer object
        if write_header: # If the file is new, write the header row with column names
            w.writerow(["date", "amount", "vendor", "description", "category", "source", "created_at_utc"]) 
        w.writerow([
            row.date or "",
            row.amount if row.amount is not None else "",
            row.vendor,
            row.description, 
            row.category,
            "feedback_api",
            datetime.now(timezone.utc).isoformat()
        ])

@app.post("/predict", response_model=PredictOut) # Define a POST endpoint for predictions, expects PredictIn model, returns PredictOut model
def predict(payload: PredictIn): # Define the function FASTAPI will call when this endpoint is hit
    """Endpoint to get category prediction for a given vendor and description."""
    try:
        cat, top = store.predict(payload.vendor, payload.description, top_k=3) # Get prediction from the model store with top 3 categories
        return PredictOut(category=cat, top=top) # Return the prediction in the expected format
    except FileNotFoundError as e: # If no model is found, return a 503 Service Unavailable error
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e: # For any other errors, return a 500 Internal Server Error
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback") # Define a POST endpoint for submitting feedback
def feedback(payload: FeedbackIn, bg: BackgroundTasks): #Input is validated against FeedbackIn model, BackgroundTasks allows for background processing
    """Endpoint to submut user feedback on predictions."""
    bg.add_task(append_feedback, payload) # Schedule the append_feedback function to run in the background
    return {"status": "queued", "message": "Thanks! Your correction was recorded."} # Return a response indicating the feedback was queued







