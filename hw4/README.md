# Campus Customs Shop + Chatbot (HW 4)

A React + Vite TypeScript storefront with a Python FastAPI backend. The chatbot is a
PydanticAI agent that answers price and stock questions from the local SQLite database
and shows matching products on the page.

## 1. Place the data pack

The database and product images are not in this repo. Unzip the course `data.zip` so
it sits inside `hw4/`:

```
hw4/
  data/
    campus_customs.db
    products/
```

## 2. Add your API key

```bash
cp .env.example .env
# then edit .env: set PORTKEY_API_KEY and SESSION_SECRET
```

## 3. Run the backend (terminal 1)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000   # http://localhost:8000  (API docs at /docs)
```

The chatbot uses `PORTKEY_API_KEY` and `MODEL_AGENT` (default `gpt-5.6-luna`) from `.env`.
`--reload` only watches `.py` files, so restart the server after editing
`backend/prompts/prompt.md`.

## 4. Run the frontend (terminal 2)

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

Open http://localhost:5173 in a browser. The front end calls the backend at
`http://localhost:8000` by default; to point it elsewhere, copy `frontend/.env.example`
to `frontend/.env` and set `VITE_API_URL`.
