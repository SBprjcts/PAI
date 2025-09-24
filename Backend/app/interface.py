from pathlib import Path
import joblib
import time
from typing import Dict, List, Tuple
import numpy as np
from ML.retrain_ml_model import build_vectorizer
from sklearn.pipeline import Pipeline

# This module provides an interface for laoding a reusable ML model from a directory.

class ModelStore:
    def __init__(self, models_dir: Path): 
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._model_path = None 
        self._model = None
        self.mtime = 0.0
        self._load_latest()
        self.vectorizer = build_vectorizer()
    
    def _latest_model_path(self) -> Path | None:
        """Finds the latest model file in the models directory."""
        files = sorted(self.models_dir.glob("*.joblib")) # Looks for and sorts all files ending in joblib in models_dir
        return files[-1] if files else None # index is -1 because the latest file is last in sorted list (smallest to largest number)
    
    def _load_latest(self):
        """Gets the path from the most recent model file and throws an error if none found. Also 
        checks if the model is already loaded and reloads if not."""
        p = self._latest_model_path() # Get the path of the latest model file
        if not p:
            raise FileNotFoundError(f"No model found in {self.models_dir}") 
        mtime = p.stat().st_mtime # Get the last modified time of the file
        if p != self._model_path or mtime != self.mtime: # If the path or modified time has changed, reload the model
            self._model = joblib.load(p) 
            self._model_path = p
            self._mtime = mtime
            
        # Extract classes for later use
        if hasattr(self._model, "classes_"):
            self.labels = list(self._model.classes_)
        elif isinstance(self._model, Pipeline) and hasattr(self._model, "classes_"):
            self.labels = list(self._model.classes_)
        else:
            self.labels = []

    def _maybe_reload(self):
        """Cheap check to see each call, reload if a newer file is dropped in the folder"""
        p = self._latest_model_path() # Sets the path to the latest model file
        if p and p.stat().st_mtime != self.mtime: # If the modified time has changed, reload the model
            self._load_latest()

    def predict(self, vendor: str, description: str, top_k: int = 3) -> Tuple[str, List[Tuple[str, float]]]:
        """Predict the category for a given vendor and description using the loaded model."""
        self._maybe_reload() # Check if the model needs to be reloaded before making a prediction
        text = f"{(vendor or '').strip()} {(description or '').strip()}".lower().strip() # Combine vendor and description into a single text string

        if not text:
            raise ValueError("Vendor/description not provided.")
        model = self._model
        top: List[Tuple[str, float]] = [] # To store the top k predictions(categories)

        # Case A: model is a Pipeline that includes the vectorizer
        if isinstance(model, Pipeline):
            # Pipeline can take raw text directly
            y_pred = model.predict([text])[0]

            probs = None
            classes = None
            # If the last step supports predict_proba, Pipeline exposes it too
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba([text])[0]
                classes = list(getattr(model, "classes_", []))
            elif hasattr(model, "decision_function"):
                # Fallback: turn scores into pseudo-probabilities
                scores = model.decision_function([text])[0]
                # Ensure 1D array
                scores = np.array(scores, dtype=float)
                # Softmax
                exps = np.exp(scores - np.max(scores))
                probs = exps / exps.sum()
                classes = list(getattr(model, "classes_", []))

        else:
            # Case B: bare classifier — vectorize text first
            # Make sure self.vectorizer exists (e.g., set in __init__ via build_vectorizer())
            X = self.vectorizer.transform([text])

            y_pred = model.predict(X)[0]

            probs = None
            classes = None
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(X)[0]
                classes = list(getattr(model, "classes_", []))
            elif hasattr(model, "decision_function"):
                scores = model.decision_function(X)[0]
                scores = np.array(scores, dtype=float)
                exps = np.exp(scores - np.max(scores))
                probs = exps / exps.sum()
                classes = list(getattr(model, "classes_", []))

        if probs is not None and classes:
            ranked = sorted(zip(classes, probs), key=lambda x: float(x[1]), reverse=True)[:top_k]
            top = [(str(c), float(p)) for c, p in ranked]

        return str(y_pred), top

        # y_pred = model.predict([text])[0] # Runs classification on the tect input, 
        # top = [] # To store the top k predictions(categoryies)

        # if hasattr(model, "predict_proba"):
        #     probs = model.predict_proba([text])[0]
        #     classes = list(getattr(model, "classes_", [])) # Retrieves the class labels from the model, classes_ is an attribute of some sklearn models, fallback to empty list if not present
        
        # else:
        #     clf = getattr(model, "steps", [])[-1][1] if hasattr(model, "steps") else None # If the model is a pipeline, get the last step (the classifier)
        #     if clf is not None and hasattr(clf, "predict_proba"): # Check if the classifier has a predict_proba method
        #         probs = clf.predict_proba(model[:-1].transform([text]))[0]  # Transform the text using all steps except the last one (predictor step), then predict probabilities
        #         classes = list(getattr(clf, "classes_", [])) # Get the class labels from the classifier
        #     else:
        #         probs, classes = None, None # If no probabilities can be computed, set to None

        # if probs is not None and classes:
        #     ranked = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)[:top_k] # Sort the classes by their predicted probabilities and take the top k
        #     top = [(c, float(p)) for c, p in ranked]
            
        # return str(y_pred), top
        






        
