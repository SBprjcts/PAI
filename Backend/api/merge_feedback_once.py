# Backend/api/merge_feedback_once.py
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2] # Go up two levels to get to PAI/
train_csv = ROOT / "data" / "training_data.csv" # Path to the main training data CSV file
feedback_csv = ROOT / "data" / "feedback.csv"  # Path to the feedback CSV file

df_train = pd.read_csv(train_csv, encoding="utf-8-sig") # Read the main training data CSV file
df_fb = pd.read_csv(feedback_csv, encoding="utf-8-sig") if feedback_csv.exists() else pd.DataFrame() 

if not df_fb.empty:
    df_train.columns = [c.strip().lower() for c in df_train.columns] # Normalize column names by stripping whitespace and converting to lowercase
    df_fb.columns = [c.strip().lower() for c in df_fb.columns]

    keep = ["date", "amount", "vendor", "description", "category"]
    for c in keep:
        if c not in df_train.columns: df_train[c] = "" # Creates any missing columns in df_train and fills with empty strings
        if c not in df_fb.columns: df_fb[c] = "" 
    
    df_all = pd.concat([df_train[keep], df_fb[keep]], ignore_index=True).drop_duplicates() # Only select the keep columns and drop duplicates
    # ^ Concat stacks the two dataframes vertically, ignore_index resets the index in the new dataframe

    df_all.to_csv(train_csv, index=False, encoding="utf-8") # Writes the merged dataframe back to the training data CSV file
    print(f"Merged {len(df_fb)} feedback rows -> {train_csv}")
else:
    print("No feedback to merge")
