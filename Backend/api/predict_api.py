# Backend/api/predict_api.py
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Tuple, Set
import csv
from datetime import datetime, timezone
import os
from fastapi.middleware.cors import CORSMiddleware # Makes the API accessible from a frontend running on a different origin
from Backend.app.interface import UserModelStore
# Commented out - these functions are work in progress
# from Backend.ML.retrain_ml_model import train_global_from_seed, retrain_user_specialized

# NEW: DB imports (psycopg2 preferred; falls back to psycopg v3 if you use it)
try:
    import psycopg2  # pip install psycopg2-binary
    _PSYCOPG2 = True
except ImportError:
    _PSYCOPG2 = False
    try:
        import psycopg  # pip install psycopg[binary]
    except ImportError:
        psycopg = None

API_DIR = Path(__file__).resolve().parent # Directory of the current file
ROOT = API_DIR.parent # Go up level to get the root directory
MODELS_DIR = ROOT / "ML" / "saved_models" # Directory where models are stored
FEEDBACK_CSV = ROOT / "data" / "feedback.csv" # Path to the feedback CSV file

from Backend.app.interface import ModelStore # Import the ModelStore class from the inference module
app = FastAPI(title="Bill Categorization API", version="0.1.0") # Initialize FastAPI app
store = ModelStore(MODELS_DIR) # Initialize the model store with the models directory

app.add_middleware( # Add CORS middleware to allow requests from the frontend
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "https://localhost:4200",
        "https://127.0.0.1:4200",
    ], # Angular dev server origin so frontend can access the API
    allow_credentials=True, # Allow cookies and authentication headers
    allow_methods=["GET", "POST"], # Allow GET, POST methods only
    allow_headers=["Authorization", "Content-Type", "Accept"] # Allow specific headers
)

PGURL = os.getenv("PGURL") or os.getenv("DATABASE_URL")  # reuse your existing env var

def _db_conn():
    """
    Get a DB connection using PGURL/DATABASE_URL.
    Returns None if no driver or no URL is configured.
    """
    if not PGURL:
        print("[db] PGURL missing in process env")
        return None
    try:
        if _PSYCOPG2:
            print("[db] using psycopg2")
            return psycopg2.connect(PGURL)  # psycopg2 DSN/URL
        elif psycopg is not None:
            print("[db] using psycopg 3")
            return psycopg.connect(PGURL)   # psycopg v3
        else:
            print("[db] no psycopg driver installed")
            return None
    except Exception as e:
        # If DB is misconfigured, fall back silently to CSV but log for server console
        print(f"[warn] DB connect failed: {e}")
        return None

def _db_execute(sql: str, params: Optional[tuple] = None, fetch: bool = False):
    """
    Small helper to execute SQL safely.
    Uses autocommit per call for simplicity in this API.
    """
    conn = _db_conn()
    if conn is None:
        print("[db] no connection; skipping execute")
        return None
    try:
        if _PSYCOPG2:
            conn.autocommit = True
            with conn.cursor() as cur:
                print("[db] exec:", sql.replace("\n"," "), "params=", params)
                cur.execute(sql, params or ())
                return cur.fetchall() if fetch else None
        else:
            # psycopg v3
            with conn:
                with conn.cursor() as cur:
                    print("[db] exec:", sql.replace("\n"," "), "params=", params)
                    cur.execute(sql, params or ())
                    return cur.fetchall() if fetch else None
    except Exception as e:
        print(f"[db] execute error: {e}")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass

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
    user_id: int
    expense_id: Optional[int] = None

def get_store_for(user_id: int):
    """Return user's personalized store if exists; else global (user_0)."""
    user_dir = MODELS_DIR / f"user_{user_id}"
    if user_dir.exists():
        return UserModelStore(MODELS_DIR, user_id)
    return UserModelStore(MODELS_DIR, 0)

def append_feedback_csv(row: FeedbackIn):
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
        
def append_feedback_db(row: FeedbackIn):
    if not PGURL or (_db_conn() is None):
        print("[feedback] DB unavailable → CSV fallback")  # ← ADDED
        append_feedback_csv(row)
        return

    user_id    = getattr(row, "user_id", None)             
    expense_id = getattr(row, "expense_id", None)         

    # Parse date safely
    expense_date = None                                     # ← ADDED
    if getattr(row, "date", None):                          # ← ADDED
        try:
            expense_date = datetime.fromisoformat(row.date).date()
        except Exception:
            expense_date = None

    # 1) Ensure an expense row exists
    if expense_id is None:
        res = _db_execute("""
            INSERT INTO public.expenses (user_id, expense_date, amount, vendor, description, category, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, now())
            RETURNING id;
        """, (user_id, expense_date, getattr(row, "amount", None),
              row.vendor, row.description, row.category), fetch=True)       # ← ADDED
        print("[feedback] INSERT expense RETURNING ->", res)                 # ← ADDED
        expense_id = res[0][0] if res else None                              # ← ADDED
    else:
        print("[feedback] Using provided expense_id ->", expense_id)         # ← ADDED

    # 2) Upsert label
    rc1 = _db_execute("""
        INSERT INTO public.user_labels (user_id, expense_id, vendor, description, chosen_cat, predicted, source, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, 'correction', now())
        ON CONFLICT (user_id, expense_id)
        DO UPDATE SET chosen_cat=EXCLUDED.chosen_cat, source='correction', created_at=now();
    """, (user_id, expense_id, row.vendor, row.description, row.category, None))  # ← ADDED
    print("[feedback] UPSERT user_labels ->", rc1)                            # ← ADDED

    # 3) Update expense category
    if expense_id is not None:
        rc2 = _db_execute(
            "UPDATE public.expenses SET category=%s WHERE id=%s AND user_id=%s;",
            (row.category, expense_id, user_id)
        )                                                                     # ← ADDED
        print("[feedback] UPDATE expenses ->", rc2)                           # ← ADDED

      
def get_categories_from_model() -> Set[str]:
    cats: Set[str] = set()
    if hasattr(store, "labels"):
        cats.update([str(x) for x in store.labels])
    return cats

def get_categories_from_feedback_csv() -> Set[str]:
    cats: Set[str] = set()
    if FEEDBACK_CSV.exists():
        with FEEDBACK_CSV.open("r", newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                cat = (row.get("category") or "").strip()
                if cat:
                    cats.add(cat)
    return cats

def get_categories_from_db(user_id: int) -> Set[str]:
    if not PGURL or (_db_conn() is None):
        return set()
    # NOTE: We bypass training_examples (no user_id there) and query base tables directly.
    rows = _db_execute(
        """
        SELECT DISTINCT category
        FROM seed_expenses
        UNION
        SELECT DISTINCT chosen_cat AS category
        FROM user_labels
        WHERE user_id = %s AND chosen_cat IS NOT NULL
        """,
        (user_id,),
        fetch=True
    )
    cats = set()
    if rows:
        for (cat,) in rows:
            if cat:
                cats.add(str(cat))
    return cats

@app.get("/categories") #Get endpoint for category submitted with the expense
def categories(user_id: int = 3):
    """
    Return categories limited to:
      - seed_expenses
      - user_labels for the given user_id
    If DB is unavailable, falls back to CSV (feedback.csv).
    """
    # CHANGED: prioritize DB-filtered categories; do NOT merge with model labels anymore
    db_cats = get_categories_from_db(user_id)
    if db_cats:
        return {"categories": sorted(db_cats, key=lambda s: s.lower())}

    # Fallback (no DB): use CSV-only categories the user entered via API (cannot filter by user here)
    csv_cats = get_categories_from_feedback_csv()
    return {"categories": sorted(csv_cats, key=lambda s: s.lower())}


@app.post("/predict", response_model=PredictOut)
def predict(payload: PredictIn, user_id: int = Query(..., ge=0)):
    """Predict using the user's model if present; otherwise global model."""
    try:
        store_for_user = get_store_for(user_id)
        # optional hot-reload if files changed:
        if hasattr(store_for_user, "reload"):
            store_for_user.reload()

        cat, top = store_for_user.predict(payload.vendor, payload.description, top_k=3)
        return PredictOut(category=cat, top=top)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback") # Define a POST endpoint for submitting feedback
def feedback(payload: FeedbackIn, bg: BackgroundTasks): #Input is validated against FeedbackIn model, BackgroundTasks allows for background processing
    """Submit user feedback on predictions.

    Behavior:
      - If PGURL/DATABASE_URL is configured and reachable → write to Postgres.
      - Else → fall back to CSV (existing behavior).
    """
    # if PGURL and _db_conn() is not None:
    #     bg.add_task(append_feedback_db, payload)   # NEW: DB path
    # else:
    #     bg.add_task(append_feedback_csv, payload)  # CHANGED: renamed function
    # return {"status": "queued", "message": "Thanks! Your correction was recorded."}
    if PGURL and _db_conn() is not None:
        print("[feedback] Writing to Postgres (sync)…")  # ← ADDED
        append_feedback_db(payload)                       # ← CHANGED (no BackgroundTasks)
        return {"status": "ok", "message": "DB write attempted"}  # ← CHANGED
    else:
        print("[feedback] DB unavailable → CSV fallback")        # ← ADDED
        append_feedback_csv(payload)
        return {"status": "queued", "message": "CSV fallback (DB unavailable)"}  # ← CHANGED

@app.get("/health/db")
def health_db():
    try:
        rows = _db_execute("SELECT 1;", fetch=True)
        if rows and rows[0][0] == 1:
            return {"db": "ok"}
        return {"db": "unreachable"}
    except Exception as e:
        return {"db": "error", "detail": str(e)}
    
@app.post("/admin/reload-model") 
def admin_reload():
    if hasattr(store, "reload"):
        store.reload()
    return {"status":"ok","message":"model reloaded"}

# TODO: Work in progress - these endpoints require implementing missing methods in ModelStore
# Uncomment when train_global_from_seed and retrain_user_specialized are implemented

# @app.post("/admin/train-global")
# def admin_train_global():
#     train_global_from_seed(PGURL)
#     return {"ok": True, "message": "global seed model trained → user_0"}

# @app.post("/admin/retrain-user")
# def admin_retrain_user(user_id: int):
#     retrain_user_specialized(user_id, PGURL)
#     return {"ok": True, "message": f"user_{user_id} model retrained"}





