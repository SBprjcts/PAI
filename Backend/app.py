from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from Models.user import User
from Database.operations import add_user_db, get_user_db, add_expense_db, get_expense_db, update_expense_db, delete_expense_db
import os, time, uuid, jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from functools import wraps

load_dotenv()


app = Flask(__name__)
# CORS(app)  # Enable CORS for all routes
# Update CORS: allow your Angular origin and cookies
CORS(app, supports_credentials=True, origins=[os.getenv("ALLOWED_ORIGIN", "http://localhost:4200")])


JWT_SECRET = os.getenv("JWT_SECRET", "change-me-long-random")
ACCESS_TTL = 900        # 15m
REFRESH_TTL = 1209600   # 14d
REFRESH_COOKIE = "refresh_token"


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        token = auth.split(" ", 1)[1]
        try:
            payload = verify_access(token)
        except Exception:
            return jsonify({"error": "Unauthorized"}), 401
        request.user_id = payload["sub"]
        return f(*args, **kwargs)
    return wrapper


def issue_access(uid: str | int):
    payload = {
        "sub": str(uid),          # 👈 cast to string
        "type": "access",
        "iat": int(time.time()),
        "exp": int(time.time()) + ACCESS_TTL,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def issue_refresh(uid: str | int):
    payload = {
        "sub": str(uid),          # 👈 cast to string
        "type": "refresh",
        "iat": int(time.time()),
        "exp": int(time.time()) + REFRESH_TTL,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_access(token: str):
    p = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    if p.get("type") != "access":
        raise jwt.InvalidTokenError("wrong type")
    return p


@app.post("/api/login")
def login():
    data = request.json or {}
    email = data.get("email", "")
    password = data.get("password", "")
    user = get_user_db(email, password)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    access = issue_access(user.id)
    refresh = issue_refresh(user.id)

    resp = make_response(jsonify({
        "access_token": access,
        "user": {"id": user.id, "company": user.company, "email": user.email}
    }))
    # in BOTH /api/login and /api/refresh responses
    resp.set_cookie(
        "refresh_token", refresh,
        httponly=True,
        secure=False,      # dev over HTTP; set True only when using HTTPS
        samesite="Lax",    # ok for same-origin via proxy
        max_age=REFRESH_TTL,
        path="/"           # NOT "/api"
        # DO NOT set 'domain'  (host-only cookie)
    )
    return resp


@app.post("/api/refresh")
def refresh():
    tok = request.cookies.get(REFRESH_COOKIE)
    if not tok:
        return jsonify({"error": "No refresh"}), 401

    try:
        payload = jwt.decode(tok, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise jwt.InvalidTokenError("wrong type")
        uid = payload["sub"]              # this is a string now
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Expired refresh"}), 401
    except Exception as e:
        print("refresh(): decode error ->", repr(e))
        return jsonify({"error": "Invalid refresh"}), 401

    new_access  = issue_access(uid)       # safe; issue_access str-casts anyway
    new_refresh = issue_refresh(uid)

    resp = make_response(jsonify({"access_token": new_access}))
    resp.set_cookie(
        REFRESH_COOKIE, new_refresh,
        httponly=True,
        secure=False,          # dev over HTTP; set True with HTTPS in prod
        samesite="Lax",
        max_age=REFRESH_TTL,
        path="/"
    )
    return resp, 200



@app.get("/api/me")
def me():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "): return jsonify({"error": "Unauthorized"}), 401
    token = auth.split(" ", 1)[1]
    try:
        p = verify_access(token)
    except Exception:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"id": p["sub"]})

@app.post("/api/logout")
def logout():
    resp = make_response(jsonify({"ok": True}))
    resp.set_cookie(REFRESH_COOKIE, "", max_age=0, path="/")  # clear cookie
    return resp


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json
    company = data.get("company", "")
    email = data.get("email", "")
    password = data.get("password", "")

    if not company or not email or not password:
            return jsonify({"status": "error", "message": "All fields required"}), 400
    
    password_hash = generate_password_hash(password)

    new_user = User(company, email, password_hash)

    add_users(new_user)

    return jsonify({"status": "success"})


# Add a new expense
@app.route('/api/expense', methods=['POST'])
@require_auth
def add_expense():
    user_id = request.user_id  # 👈 logged-in user ID
    data = request.get_json()
    date = data.get("date")
    amount = data.get("amount")
    vendor = data.get("vendor")
    description = data.get("description")
    category = data.get("category")

    # TODO: Calculate anomaly score
    anomaly_score = data.get("anomaly_score")

    # Save expense linked to this user
    add_expense_db(user_id, date, amount, vendor, description, category, anomaly_score)

    return jsonify({"status": "success"}), 201


# Get all expenses
@app.route('/api/expense', methods=['GET'])
@require_auth
def get_expenses():
    user_id = request.user_id
    expenses = get_expense_db(user_id)  # Fetch only this user’s expenses
    return jsonify({expenses})


# Update an existing expense
@app.route('/api/expense/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    data = request.get_json()
    for exp in expenses:
        if exp['id'] == expense_id:
            exp.update(data)
            return jsonify(exp)
    return jsonify({'error': 'Expense not found'}), 404

# Delete an expense
@app.route('/api/expense/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    global expenses
    expenses = [exp for exp in expenses if exp['id'] != expense_id]
    return jsonify({'message': f'Expense {expense_id} deleted'}), 200


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
