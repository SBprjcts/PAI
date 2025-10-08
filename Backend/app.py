from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from Models.user import User
from Database.operations import add_users, get_users
import os, time, uuid, jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash


load_dotenv()


app = Flask(__name__)
# CORS(app)  # Enable CORS for all routes
# Update CORS: allow your Angular origin and cookies
CORS(app, supports_credentials=True, origins=[os.getenv("ALLOWED_ORIGIN", "http://localhost:4200")])


JWT_SECRET = os.getenv("JWT_SECRET", "change-me-long-random")
ACCESS_TTL = 900        # 15m
REFRESH_TTL = 1209600   # 14d
REFRESH_COOKIE = "refresh_token"

def issue_access(uid: str):
    payload = {"sub": uid, "type": "access", "iat": int(time.time()), "exp": int(time.time()) + ACCESS_TTL}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def issue_refresh(uid: str):
    payload = {"sub": uid, "type": "refresh", "iat": int(time.time()),
               "exp": int(time.time()) + REFRESH_TTL, "jti": str(uuid.uuid4())}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_access(token: str):
    p = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    if p.get("type") != "access": raise jwt.InvalidTokenError("wrong type")
    return p

@app.post("/api/login")
def login():
    data = request.json or {}
    email = data.get("email", "")
    password = data.get("password", "")
    user = get_users(email, password)  # TODO: switch to hashed passwords ASAP
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    access = issue_access(user.id)
    refresh = issue_refresh(user.id)

    resp = make_response(jsonify({
        "access_token": access,
        "user": {"id": user.id, "company": user.company, "email": user.email}
    }))
    resp.set_cookie(
        REFRESH_COOKIE, refresh,
        httponly=True, secure=not app.debug, samesite="Lax", max_age=REFRESH_TTL, path="/"
    )
    return resp


@app.post("/api/refresh")
def refresh():
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        return jsonify({"error": "No refresh"}), 401
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise jwt.InvalidTokenError()
    except Exception:
        return jsonify({"error": "Invalid refresh"}), 401

    new_access = issue_access(payload["sub"])
    return jsonify({"access_token": new_access})

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

if __name__ == "__main__":
    app.run(port=5000, debug=True)
