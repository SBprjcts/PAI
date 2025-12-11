# PAI - AI-Powered Expense Categorization

**Intelligent expense categorization system that automatically classifies financial transactions using machine learning and improves through user feedback.**

## Features

- 🤖 **Automatic Categorization** - AI-powered predictions using natural language processing
- 📊 **Confidence Scores** - Top-k predictions with probability rankings
- 🔄 **Feedback Loop** - User corrections continuously improve the model
- 📈 **Incremental Learning** - Models update without full retraining using SGDClassifier
- 👤 **User Personalization** - Individual models fine-tuned from global seed data
- 💾 **Flexible Storage** - PostgreSQL support with automatic CSV fallback
- ⚡ **Real-time Predictions** - Instant categorization via REST API

## Technology Stack

### Backend
- **Python 3.13** - Core language
- **FastAPI** - Modern async REST API framework
- **scikit-learn** - Machine learning (SGDClassifier + HashingVectorizer)
- **PostgreSQL** - Optional database (psycopg2)
- **pandas & NumPy** - Data processing
- **joblib** - Model persistence

### Frontend
- **Angular 20.2** - TypeScript framework with standalone components
- **RxJS** - Reactive programming for async operations
- **TypeScript 5.9** - Type-safe development

## Prerequisites

- Python 3.10+ (tested with 3.13)
- Node.js 18+ and npm
- PostgreSQL (optional - app works with CSV files)
- Git

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/SBprjcts/PAI.git
cd PAI
git checkout bill_categorization
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install fastapi uvicorn scikit-learn pandas numpy joblib psycopg2-binary
```

### 3. Frontend Setup

```bash
cd Frontend
npm install
cd ..
```

### 4. Required: Copy Model File

The application requires a trained model file. Copy the existing model to the user directory:

**Windows:**
```cmd
copy "Backend\ML\saved_models\bill_category_model.joblib" "Backend\ML\saved_models\user_0\bill_category_model.joblib"
```

**Linux/Mac:**
```bash
cp Backend/ML/saved_models/bill_category_model.joblib Backend/ML/saved_models/user_0/bill_category_model.joblib
```

## Running the Application

### Start the Backend API

From the **root PAI directory**:

```bash
py -m uvicorn Backend.api.predict_api:app --reload --host 127.0.0.1 --port 8000
```

✅ Backend will be available at: http://127.0.0.1:8000
📚 API docs (Swagger UI) at: http://127.0.0.1:8000/docs

### Start the Frontend

In a new terminal:

```bash
cd Frontend
npm start
```

✅ Frontend will be available at: http://localhost:4200

## Using the Bill Categorization Feature

1. **Open your browser** to http://localhost:4200

2. **Fill in the expense form:**
   - **Date**: Select transaction date
   - **Amount**: Enter transaction amount (e.g., `45.67`)
   - **Vendor**: Enter merchant name (e.g., `Walmart`)
   - **Description**: Enter purchase details (e.g., `Bought eggs, milk, and snacks`)

3. **Click "Continue"** to get AI prediction

4. **Review the results:**
   - Top predicted category shown with confidence score
   - Alternative suggestions displayed as chips
   - Probabilities ranked from most to least likely

5. **Submit your feedback:**
   - **Accept prediction**: Click the predicted category chip
   - **Choose alternative**: Click any suggested category
   - **Custom category**: Type your own in the text field

6. **Click "Submit"** to save the expense and improve the model

The system learns from your corrections and will provide better predictions over time!

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict?user_id=0` | POST | Get category prediction for vendor + description |
| `/feedback?user_id=0` | POST | Submit user correction to improve model |
| `/categories?user_id=0` | GET | Get list of available categories |
| `/health/db` | GET | Check database connection status |
| `/admin/reload-model` | POST | Force reload model from disk |

### Example API Usage

**Predict Category:**
```bash
curl -X POST "http://127.0.0.1:8000/predict?user_id=0" \
  -H "Content-Type: application/json" \
  -d '{"vendor": "Walmart", "description": "groceries"}'
```

**Response:**
```json
{
  "category": "Groceries",
  "top": [
    ["Groceries", 0.92],
    ["Shopping", 0.05],
    ["Household", 0.03]
  ]
}
```

## Configuration

### Database (Optional)

To use PostgreSQL instead of CSV files, set the environment variable:

**Windows:**
```cmd
set PGURL=postgresql://user:password@localhost:5432/pai_db
```

**Linux/Mac:**
```bash
export PGURL=postgresql://user:password@localhost:5432/pai_db
```

If `PGURL` is not set, the app automatically uses CSV files stored in `Backend/data/feedback.csv`.

### API Base URL

The frontend is configured to use `http://127.0.0.1:8000` by default.

To change this, edit `Frontend/src/environments/environment.ts`:

```typescript
export const environment = {
    production: false,
    API_BASE: 'http://127.0.0.1:8000'  // Change this URL
};
```

## Troubleshooting

### "[object Object]" error in frontend
**Cause**: Backend not running or model file missing
**Solution**:
- Verify backend is running on port 8000
- Ensure model file exists in `Backend/ML/saved_models/user_0/`

### "No model found in user_0" error
**Cause**: Model file not copied to user directory
**Solution**: Run the copy command from step 4 of Installation

### 422 Unprocessable Content
**Cause**: Missing `user_id` query parameter (should be fixed in latest code)
**Solution**: Ensure you're on the latest `bill_categorization` branch

### Port 8000 already in use
**Solution 1**: Kill the existing process
```cmd
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Solution 2**: Use a different port
```bash
py -m uvicorn Backend.api.predict_api:app --reload --port 8001
```
Then update `environment.ts` to use port 8001

### Import errors / Circular import
**Cause**: Running from wrong directory
**Solution**: Always run the backend from the **root PAI directory**, not from the Backend folder

## Project Structure

```
PAI/
├── Backend/
│   ├── api/
│   │   └── predict_api.py          # FastAPI endpoints
│   ├── app/
│   │   └── interface.py            # Model loading & inference
│   ├── ML/
│   │   ├── retrain_ml_model.py     # Incremental training logic
│   │   ├── vectorizer_utils.py     # Text vectorization
│   │   └── saved_models/           # Trained model files
│   │       └── user_0/             # Global model directory
│   └── data/
│       └── feedback.csv            # CSV fallback storage
├── Frontend/
│   └── src/
│       ├── app/
│       │   ├── pages/predict.comp/ # Main prediction UI
│       │   └── services/predict.ts # API service
│       └── environments/
│           └── environment.ts      # API configuration
└── Database/
    ├── seed_expenses.sql           # Initial training data
    └── global_training_for_seed_categories.sql
```

## Development Notes

- **Models**: Stored in `Backend/ML/saved_models/`
- **User Models**: Per-user models in `Backend/ML/saved_models/user_{id}/`
- **Feedback**: Automatically saved to CSV or PostgreSQL
- **Versioning**: Model snapshots saved with timestamps
- **Hot Reload**: Models automatically reload when updated on disk
- **Admin Endpoints**: `/admin/train-global` and `/admin/retrain-user` are work-in-progress

## Machine Learning Pipeline

### Data Flow
1. **Extract**: User input (vendor + description) or training data (CSV/PostgreSQL)
2. **Transform**:
   - Text normalization (lowercase, trimming)
   - Feature extraction (HashingVectorizer with bi-grams, 2^20 feature space)
   - Deduplication using SHA-256 hashing
3. **Load**: Incremental model updates using `partial_fit` on SGDClassifier

### Model Training
- **Algorithm**: Stochastic Gradient Descent (log loss)
- **Vectorization**: Stateless HashingVectorizer (supports streaming)
- **Learning**: Online/incremental (no need to retrain from scratch)
- **Persistence**: Models saved as `.joblib` files
- **Evaluation**: Train/test split with stratification

## Contributing

**Branch**: `bill_categorization`
**Repository**: https://github.com/SBprjcts/PAI

## License

This project is part of a personal AI portfolio.

---

**Built with Claude Code** 🤖
