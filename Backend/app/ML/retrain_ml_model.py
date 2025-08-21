import os
import json 
import argparse
from datetime import datetime
import hashlib
import joblib
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import SGDClassifier  
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

def get_args():
    """Parse command line arguments."""
    p = argparse.ArgumentParser(description="Incremtal bill category model retraining")
    p.add_argument("--csv", default= r"C:\Users\saifb\Downloads\PAI\data\training_data.csv", 
                   help= "Path to the training data CSV file")
    p.add_argument("--outdir", default= "ML/saved_models",
                   help= "Path to the output directory for saving the model")
    p.add_argument("--model_name", default= "bill_category_model.joblib",
                   help= "Name of the model to be saved")
    p.add_argument("--seen_file", default= "seen_hashes.json",
                   help= "Filename to store trained data hashes")
    p.add_argument("--batch_size", type=int, default=2048,
        help="Mini-batch size for partial_fit (helps with very large CSVs)."
    )
    p.add_argument("--test_size", type=float, default=0.2,
        help="Holdout share for quick accuracy check each run."
    )
    p.add_argument("--random_state", type=int, default=42,
        help="Random seed for reproducible splits."
    )
    return p.parse_args()


def load_data(csv_path: str) -> pd.DataFrame:
    # Read CSV (utf-8-sig handles BOMs from Excel)
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # Normalize headers
    df.columns = [c.replace("\ufeff", "").strip().lower() for c in df.columns]

    print(list(df.columns))  # Debug: print column names

    # Map common synonyms
    if "supplier" in df.columns and "vendor" not in df.columns:
        df = df.rename(columns={"supplier": "vendor"})
    if "details" in df.columns and "description" not in df.columns:
        df = df.rename(columns={"details": "description"})
    if "memo" in df.columns and "description" not in df.columns:
        df = df.rename(columns={"memo": "description"})
    if "label" in df.columns and "category" not in df.columns:
        df = df.rename(columns={"label": "category"})
    if "class" in df.columns and "category" not in df.columns:
        df = df.rename(columns={"class": "category"})

    # Ensure required columns exist
    required = {"vendor", "description", "category"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"CSV missing required columns: {missing}. Found: {list(df.columns)}")

    # Clean + build text
    df["vendor"] = df["vendor"].astype(str).fillna("").str.strip()
    df["description"] = df["description"].astype(str).fillna("").str.strip()
    df["category"] = df["category"].astype(str).fillna("").str.strip()
    df["text"] = (df["vendor"] + " " + df["description"]).str.lower().str.strip()

    # Drop empties
    df = df[(df["text"].str.len() > 0) & (df["category"].str.len() > 0)].reset_index(drop=True)

    return df

def row_id(text: str, category: str) -> str:
    """Create a unique and stable ID per row to avoid retraining on seen data (
     using a hash of text + category)."""
    h = hashlib.sha256() # Create a new sha256 hash object. 
    h.update((text + "||" + str(category)).encode("utf-8")) # Update the hash object with the combined text and category."))
    return h.hexdigest() # Return the hexadecimal representation of the hash with 64 characters.

def prepare_seen(outdir: str, seen_file: str) -> set:
    """Load or initialize the set of seen row hashes."""
    os.makedirs(outdir, exist_ok=True) # Ensure output directory exists for saving the seen hashes file.
    path = os.path.join(outdir, seen_file) # Full path to the seen hashes file. 
    if os.path.exists(path): # If the file exists, load the seen hashes from it.
        with open(path, "r", encoding="utf-8") as f: # Open the file for reading.
                return set(json.load(f)) # Load the JSON data and convert it to a set.
    return set() # If the file doesn't exist, return an empty set.

def save_seen(outdir: str, seen_file: str, seen_ids: set):
    """Persist the set of seen row hashes to disk."""
    path = os.path.join(outdir, seen_file) # Full path to the seen hashes file.
    with open(path, "w", encoding="utf-8") as f: # Open the file for writing.
         json.dump(sorted(list(seen_ids)), f) # Save the sorted list of seen hashes as JSON.

def build_vectorizer() -> HashingVectorizer:
     """Create a stateless text vectorizer that works for strreaming/online learning."""
     return HashingVectorizer(
        n_features = 2**20,  #Large feature space to reduce collisions
        alternate_sign=False, # Keeps the output non-negative for better interpretability
        ngram_range=(1, 2), # Uses unigrams and bigrams for better context capture
        norm="l2" # Normalizes the output to unit length for consistent scaling
     )  

def new_labels(model: SGDClassifier, labels: np.ndarray) -> np.ndarray:
     """Return labels not seen by the existing model yet to avoid retraining on them."""
     if not hasattr(model, "classes_"):  # If model has no classes (only happens when model not trained), return all unique labels.
          return list((np.unique(labels))) # If model has no classes, return all unique labels.
     return [c for c in np.unique(labels) if c not in model.classes_] # Return only new labels not seen by the model (when model is already trained).

def train_or_update_model(df: pd.DataFrame,
                          outdir: str,
                          model_name: str,
                          seen: set,
                          batch_size: int,
                          test_size: float,
                          random_state: int):
    """Train the data on the first run or update otherwise with new data incrementally:
    - It uses only rhe new rows for partial_fit.
    - If unseen categories appear, refits from scartch on All data ro register new classes.
    """
    # Compute IDs per row and split into new and seen. 
    df["row_id"] = [row_id(t, c) for t, c in zip(df["text"], df["category"])]  # Create unique row IDs based on text and category.
    df_new = df[~df["row_id"].isin(seen)].reset_index(drop=True) # Filter out rows that have already been seen."

    vectorizer = build_vectorizer() # Create a new vectorizer instance (stateless).

    latest_model_path = os.path.join(outdir, model_name) # Assigns the path for the latest model file (Initializes or loads).

    if os.path.exists(latest_model_path):  # If the model file exists, load it.
        model: SGDClassifier = joblib.load(latest_model_path) # Load the existing model.
        print(f"Loaded existing model from {latest_model_path}") # Print confirmation of model loading.

    else: 
        # First time model training with default parameters for text classification.
        model = SGDClassifier(
            loss="log_loss",  # Uses log loss for multi-class classification.
            alpha=1e-5, # Regularization term to prevent overfitting.
            max_iter=5, # Number of iterations for training.
            tol=1e-3, # Tolerance for stopping criteria.
            random_state=random_state, # Ensures reproducibility.
        )
        print("Initialized new SGDClassifier model") 
    
    # If there are labels current model doesn't know, they mush be registered via full retraining.

    unseen = new_labels(model, df_new["category"].values) # Get labels not seen by the model yet.
    if hasattr(model, "classes_") and len(unseen) > 0: # If the model is already trained and there are unseen labels.
        print(f"New categories detected: {unseen}. Re-fitting model from scratch to register them.") # Notify about new categories.
        all_classes = np.unique(df["category"].values) # Get all unique categories from the entire dataset.
        model = SGDClassifier(
            loss="log_loss",  # Uses log loss for multi-class classification.
            alpha=1e-5, # Regularization term to prevent overfitting.
            max_iter=5, # Number of iterations for training.
            tol=1e-3, # Tolerance for stopping criteria.
            random_state=random_state, # Ensures reproducibility.
        )
        _full_refit(df, model, vectorizer, all_classes, batch_size) # Refit the model from scrtatch with all data to register new classes.
        seen.update(df["row_id"].tolist()) # Update the seen set with all row IDs.
    
    else:
        if not hasattr(model, "classes_"): # If the model has no classes (not trained yet).
             all_classes = np.unique(df_new["category"].values) # Get all unique categories from the new data.
             print(f"Registering classes {list(map(str, all_classes))} ") # Notify about training on new data.

             _bootstrap_classes(df, model, vectorizer, all_classes) # Bootstrap the model with the new classes.
        
        if len(df_new) == 0: # If there are no new rows to train on.
            print("No new rows to train on. Model is up to date.") # Notify that there are no new rows.
        else:
             print(f"Training on {len(df_new)} new rows.") # Notify about the number of new rows to train on.
             _partial_fit_stream(df_new, model, vectorizer, batch_size) # Train the model incrementally on the new data.
             seen.update(df_new["row_id"].tolist()) # Update the seen set with new row IDs.
        
    acc = _quick_evaluate(df, model, vectorizer, test_size, random_state) # Quick evaluation of the model on a holdout set.

    os.makedirs(outdir, exist_ok=True) # Ensure the output directory exists.
    joblib.dump(model, latest_model_path) # Save the trained model to disk.
    ts =  datetime.now().strftime("%Y%m%dT%H%M%SZ") # Get the current timestamp.
    snapshot = os.path.join(outdir, f"bill_categorizer_incremental_{ts}.joblib") # Save a snapshot of the model with a timestamp.
    joblib.dump(model, snapshot) # Save the snapshot of the model.  

    print(f"Saved latest model to: {latest_model_path}")
    print(f"Snapshot saved to:   {snapshot}")
    print(f"Eval accuracy: {acc:.4f}")

    return model, vectorizer, seen

def _bootstrap_classes(df, model, vectorizer, all_classes):
     """Ensure that the model knows the full label set before streaming updates.
     Attempt to feed at least one example per class to the model; if not possible, pass
     the full class list."""

     x_boot = vectorizer.transform(df["text"].values[:1]) if len(df) > 0 else vectorizer.transform(["placeholder"]) # Transform the text data into feature vectors (inputs model learns from)
     y_boot = df["category"].values[:1] if len(df) > 0 else np.array(all_classes[0]) # Get the category labels for the first row or a placeholder (labels the model tries to predict).
     model.partial_fit(x_boot, y_boot, classes=all_classes) # Perform a partial fit to register the classes.    

def _partial_fit_stream(df_chunked, model, vectorizer, batch_size):
     """Stream new data in batches to the model to avoid memory spikes."""

     n = len(df_chunked)
     for start in range(0, n, batch_size): # Iterate oover the DataFrame in chunks of batch_size.
          end = min(start + batch_size, n) # Find the end index for the current batch.
          x_batch = vectorizer.transform(df_chunked["text"].values[start:end]) # Transform the text data into feature vectors for the current batch.)
          y_batch = df_chunked["category"].values[start:end] # Get the category labels for the current batch.
          model.partial_fit(x_batch, y_batch) # Perform a partial fit on the current batch of data.
          
def _full_refit(df, model, vectorizer, all_classes, batch_size):
     """Do a full but batched fit via partial_fit so the model learns new categories."""
     n = len(df)
     # FIrst call must have all classes registered.
     first_end = min(batch_size, n) # Determine the end index for the first batch.
     x0 = vectorizer.transform(df["text"].values[:first_end]) # Transform the text data into feature vectors for the first batch.
     y0 = df["category"].values[:first_end] # Get the category labels for the first batch.
     model.partial_fit(x0, y0, classes=all_classes) # Perform a partial fit on the first batch with all classes registered.
     # Continue with the rest of the data in batches.
     for start in range(first_end, n, batch_size): 
          end = min(start + batch_size, n) 
          xb = vectorizer.transform(df["text"].values[start:end]) # Transform the text data into feature vectors for the current batch.
          yb = df["category"].values[start:end] # Get the category labels for the current batch.
          model.partial_fit(xb, yb) # Perform a partial fit on the current batch of data.

def _quick_evaluate(df, model, vectorizer, test_size, random_state):
     """Quickly perform a sanity-check evaluation on a holdout set (not a full validation)."""
     
     X_text = df["text"].to_numpy() # Convert the text column to a NumPy array.
     y = df["category"].to_numpy()
     
     if len(np.unique(df["category"].values)) < 2 or len(df) < 10: # Checks if enough categories or rows
          print("Not enough data for evaluation. Skipping accuracy check.") 
          return 0.0 # If not enough data, return 0.0 accuracy.
     
     x_train, x_test, y_train, y_test = train_test_split(
          df["text"].values, df["category"].values, test_size =test_size, random_state=random_state,
          stratify=df["category"].values
     )
     
     X_train = vectorizer.transform(x_train) # Transform the training text data into feature vectors.
     X_test  = vectorizer.transform(x_test)

     y_pred = model.predict(X_test) # Predict categories for the test set.
     acc = accuracy_score(y_test, y_pred)
     print(f"Quick eval accuracy: {acc:.3f}")
     return acc

def main():
    args = get_args()

    # Ensure output directory exists (for model + seen_ids.json).
    os.makedirs(args.outdir, exist_ok=True)

    # Load the CSV every run (so we can detect newly added rows).
    df = load_data(args.csv)

    # Load or init the seen set (to avoid double-training).
    seen = prepare_seen(args.outdir, args.seen_file)

    # Train or update on the CSV content.
    model, vectorizer, seen = train_or_update_model(
        df=df,
        outdir=args.outdir,
        model_name=args.model_name,
        seen=seen,
        batch_size=args.batch_size,
        test_size=args.test_size,
        random_state=args.random_state
    )

    # Persist the seen IDs after successful update.
    save_seen(args.outdir, args.seen_file, seen)

    print("\nDone.")


if __name__ == "__main__":
    main()