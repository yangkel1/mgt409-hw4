"""Campus Customs FastAPI app — run from backend/ with: uvicorn main:app --reload"""

import hashlib
import hmac
import logging
import os
import re
import secrets
import sqlite3
import time
from contextlib import closing

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import tools  # loads .env and checks the database before anything else
from agent import run_chat
from models import (
    ChatRequest,
    ChatResponse,
    ChatTurn,
    LoginRequest,
    ProductDetail,
    ProductSummary,
    SignupRequest,
    StoredChatMessage,
    UserPublic,
)
from tools import connect

log = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs")

# The Vite dev server (5173) is a different origin from this API (8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product photos: catalogue paths are relative to data/ (e.g. products/x.jpg).
app.mount("/images", StaticFiles(directory=tools.DATA_DIR / "products"), name="images")


@app.get("/api/health")
def health():
    return {"ok": True, "model": tools.model_name()}


@app.get("/api/products", response_model=list[ProductSummary])
def list_products():
    return tools.list_products()


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str):
    product = tools.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


HISTORY_FOR_AGENT = 20  # earlier messages the model sees
HISTORY_FOR_PAGE = 100  # messages the chat panel reloads


def as_turn(m: StoredChatMessage) -> ChatTurn:
    """Saved message -> agent history. Cards are named so "the first one" still resolves."""
    shown = m.page.products if m.page else m.products
    note = "\n[Products shown: " + "; ".join(f"{p.name} ({p.product_id})" for p in shown[:8]) + "]" if shown else ""
    return ChatTurn(role=m.role, content=m.content + note)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request):
    user = current_user(request)
    if user is not None:
        # Signed in: memory comes from the database, not from the browser.
        history = [as_turn(m) for m in tools.load_chat_history(user.id, HISTORY_FOR_AGENT)]
        customer = tools.customer_context(user.id)
    else:
        history, customer = body.history, None

    try:
        response = await run_chat(body.message, history, customer, body.page, user.id if user else None)
    except Exception:
        log.exception("Chat agent failed")
        raise HTTPException(status_code=502, detail="The shop assistant is having trouble right now. Please try again.")

    if user is not None:
        tools.save_chat_exchange(user.id, body.message, response.reply, response.products, response.page)
    return response


@app.get("/api/chat/history", response_model=list[StoredChatMessage])
def chat_history(request: Request):
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to see saved chat history.")
    return tools.load_chat_history(user.id, HISTORY_FOR_PAGE)


@app.delete("/api/chat/history", status_code=204)
def delete_chat_history(request: Request):
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to manage chat history.")
    tools.clear_chat_history(user.id)


# ---------------------------------------------------------------------------
# Accounts: passwords are salted PBKDF2-SHA256 hashes; sessions are signed cookies.
# ---------------------------------------------------------------------------

PBKDF2_ITERATIONS = 600_000  # OWASP guidance for PBKDF2-HMAC-SHA256
LEGACY_ITERATIONS = 120_000  # seeded rows use pbkdf2_sha256$<salt>$<hex> with no count stored
SESSION_COOKIE = "cc_session"
SESSION_SECONDS = 7 * 24 * 3600
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"  # true when served over HTTPS
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 15 * 60
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Without a configured secret, sessions still work but reset whenever the server restarts.
SESSION_SECRET = os.getenv("SESSION_SECRET") or secrets.token_urlsafe(48)

failed_logins: dict[str, list[float]] = {}


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def parse_hash(stored: str) -> tuple[int, str, str] | None:
    parts = stored.split("$")
    if len(parts) == 4 and parts[0] == "pbkdf2_sha256" and parts[1].isdigit():
        return int(parts[1]), parts[2], parts[3]
    if len(parts) == 3 and parts[0] == "pbkdf2_sha256":
        return LEGACY_ITERATIONS, parts[1], parts[2]
    return None


def verify_password(password: str, stored: str) -> bool:
    parsed = parse_hash(stored)
    if parsed is None:
        return False
    iterations, salt, expected = parsed
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
    return hmac.compare_digest(digest, expected)


# Checked when an email is unknown, so a miss takes as long as a wrong password.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def sign(payload: str) -> str:
    return hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_session_token(user_id: int) -> str:
    payload = f"{user_id}.{int(time.time()) + SESSION_SECONDS}"
    return f"{payload}.{sign(payload)}"


def read_session_token(token: str) -> int | None:
    parts = token.split(".")
    if len(parts) != 3 or not hmac.compare_digest(parts[2], sign(f"{parts[0]}.{parts[1]}")):
        return None
    user_id, expires = int(parts[0]), int(parts[1])
    return user_id if expires > time.time() else None


def set_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        make_session_token(user_id),
        max_age=SESSION_SECONDS,
        httponly=True,  # page JavaScript can't read it, so injected scripts can't steal it
        samesite="lax",
        secure=COOKIE_SECURE,
    )


def to_public(row: sqlite3.Row) -> UserPublic:
    first, _, last = row["name"].partition(" ")
    return UserPublic(
        id=row["id"],
        first_name=row["first_name"] or first,
        last_name=row["last_name"] or last,
        email=row["email"],
    )


def current_user(request: Request) -> UserPublic | None:
    token = request.cookies.get(SESSION_COOKIE)
    user_id = read_session_token(token) if token else None
    if user_id is None:
        return None
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return to_public(row) if row else None


def clean_email(email: str) -> str:
    email = email.strip().lower()
    if len(email) > 254 or not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    return email


@app.post("/api/auth/signup", response_model=UserPublic, status_code=201)
def signup(body: SignupRequest, response: Response):
    first, last = body.first_name.strip(), body.last_name.strip()
    if not (0 < len(first) <= 50 and 0 < len(last) <= 50):
        raise HTTPException(status_code=400, detail="Please enter your first and last name.")
    email = clean_email(body.email)
    if not 8 <= len(body.password) <= 128:
        raise HTTPException(status_code=400, detail="Password must be 8 to 128 characters.")

    with closing(connect()) as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        try:
            with conn:
                cur = conn.execute(
                    "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                    (f"{first} {last}", email, hash_password(body.password), first, last),
                )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()

    set_session(response, row["id"])
    return to_public(row)


@app.post("/api/auth/login", response_model=UserPublic)
def login(body: LoginRequest, response: Response):
    email = body.email.strip().lower()
    now = time.time()
    recent = [t for t in failed_logins.get(email, []) if now - t < LOCKOUT_SECONDS]
    if len(recent) >= MAX_FAILED_LOGINS:
        raise HTTPException(status_code=429, detail="Too many failed attempts. Please try again in 15 minutes.")

    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
        ok = verify_password(body.password, row["password_hash"] if row else DUMMY_HASH) and row is not None
        if not ok:
            failed_logins[email] = recent + [now]
            # Same message either way, so the form can't be used to discover who has an account.
            raise HTTPException(status_code=401, detail="Incorrect email or password.")

        failed_logins.pop(email, None)
        if parse_hash(row["password_hash"])[0] < PBKDF2_ITERATIONS:
            with conn:  # upgrade older, weaker hashes now that we know the password
                conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(body.password), row["id"]))

    set_session(response, row["id"])
    return to_public(row)


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax", secure=COOKIE_SECURE)


@app.get("/api/auth/me", response_model=UserPublic)
def me(request: Request):
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not signed in.")
    return user
