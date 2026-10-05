"""Config, database access, and the tools the shop agent can call.

Everything the agent says about price, color, or stock comes from these functions,
which read campus_customs.db directly. The model never sees the users table.
"""

import difflib
import json
import os
import re
import sqlite3
import threading
from contextlib import closing

try:  # Unix file locking; on Windows the thread lock alone guards the audit file
    import fcntl
except ImportError:
    fcntl = None
from functools import cache
from pathlib import Path

from dotenv import load_dotenv

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")  # keep server logs clean

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from models import (
    AuditEntry,
    CustomerContext,
    PageResults,
    ProductDetail,
    ProductHit,
    ProductInfo,
    ProductNotFound,
    ProductSummary,
    SearchResult,
    SimilarProducts,
    SizeStock,
    StockLine,
    StockReport,
    StoredChatMessage,
    ViewedProduct,
)

HW4_DIR = Path(__file__).resolve().parents[1]

# Nearest .env wins: hw4/.env first, then the shared course .env further up.
for folder in [HW4_DIR, *HW4_DIR.parents]:
    if (folder / ".env").exists():
        load_dotenv(folder / ".env", override=False)

DB_PATH = (HW4_DIR / os.getenv("DB_PATH", "data/campus_customs.db")).resolve()
DATA_DIR = DB_PATH.parent
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
MAX_SEARCH_RESULTS = 8

if not DB_PATH.exists():
    raise RuntimeError(f"Database not found at {DB_PATH}. Unzip the data pack into hw4/data/.")


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


def model_name() -> str:
    return os.getenv("MODEL_AGENT") or os.getenv("MODEL_DEFAULT") or "gpt-5.6-luna"


@cache
def get_model() -> OpenAIChatModel:
    """PydanticAI model bound to OpenAI through the Portkey gateway."""
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is missing. Add it to hw4/.env (see .env.example).")
    provider = OpenAIProvider(
        api_key=api_key,
        base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
    )
    return OpenAIChatModel(model_name(), provider=provider)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def first_sentence(text: str) -> str:
    match = re.match(r"(.+?[.!?])(\s|$)", text)
    return match.group(1) if match else text


def image_url(image_file_path: str) -> str:
    return "/images/" + image_file_path.removeprefix("products/")


def stock_by_product(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT product_id, SUM(quantity) AS total FROM inventory GROUP BY product_id")
    return {r["product_id"]: r["total"] for r in rows}


def to_summary(row: sqlite3.Row, total_stock: int, sizes_in_stock: list[str] | None = None) -> ProductSummary:
    return ProductSummary(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        price=row["price"],
        short_description=first_sentence(row["description"]),
        colors=json.loads(row["colors"]),
        image_url=image_url(row["image_file_path"]),
        total_stock=total_stock,
        sizes_in_stock=sizes_in_stock or [],
    )


def list_products() -> list[ProductSummary]:
    with closing(connect()) as conn:
        stock = stock_by_product(conn)
        sizes = sizes_in_stock_by_product(conn)
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    return [to_summary(r, stock.get(r["product_id"], 0), sizes.get(r["product_id"], [])) for r in rows]


def get_product(product_id: str) -> ProductDetail | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        sizes = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchall()

    inventory = sorted(
        (SizeStock(size=s["size"], quantity=s["quantity"]) for s in sizes),
        key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else len(SIZE_ORDER),
    )
    summary = to_summary(row, sum(s.quantity for s in inventory), [s.size for s in inventory if s.quantity > 0])
    return ProductDetail(
        **summary.model_dump(),
        description=row["description"],
        search_tags=json.loads(row["search_tags"]),
        inventory=inventory,
    )


def get_products(product_ids: list[str]) -> list[ProductSummary]:
    """Summaries for the given ids, in the given order; unknown ids are dropped."""
    by_id = {p.product_id: p for p in list_products()}
    seen: set[str] = set()
    return [by_id[i] for i in product_ids if i in by_id and not (i in seen or seen.add(i))]


# ---------------------------------------------------------------------------
# Agent tools (registered on the agent in agent.py). Each returns a typed model
# from models.py whose values are read straight from the database.
# ---------------------------------------------------------------------------

LOW_STOCK = 5  # same threshold the product page uses for "Only N left"


def stock_status(quantity: int) -> str:
    if quantity == 0:
        return "sold out"
    return "low stock" if quantity <= LOW_STOCK else "in stock"


def stock_lines(conn: sqlite3.Connection, product_id: str) -> list[StockLine]:
    rows = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchall()
    lines = [StockLine(size=r["size"], quantity=r["quantity"], status=stock_status(r["quantity"])) for r in rows]
    return sorted(lines, key=lambda s: SIZE_ORDER.index(s.size))


def sizes_in_stock_by_product(conn: sqlite3.Connection) -> dict[str, list[str]]:
    in_stock: dict[str, list[str]] = {}
    for r in conn.execute("SELECT product_id, size FROM inventory WHERE quantity > 0"):
        in_stock.setdefault(r["product_id"], []).append(r["size"])
    return {pid: sorted(sizes, key=SIZE_ORDER.index) for pid, sizes in in_stock.items()}


def to_hit(row: sqlite3.Row, sizes: list[str]) -> ProductHit:
    return ProductHit(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        price=row["price"],
        colors=json.loads(row["colors"]),
        sizes_in_stock=sizes,
    )


def singular(word: str) -> str:
    """'hoodies' -> 'hoodie', 'crewnecks' -> 'crewneck', so plurals match the catalogue."""
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def search_products(
    query: str = "", max_price: float | None = None, size: str | None = None, limit: int | None = MAX_SEARCH_RESULTS
) -> SearchResult:
    """Keyword search over name, garment type, description, colors, and tags.

    Products must match every query word ("navy hoodie" = navy AND hoodie). If none do,
    it falls back to products matching the most words and says so in `match`. An empty
    query lists everything. `size` keeps only products in stock in that size. `limit=None`
    returns every match (used for the page).
    """
    words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 1]
    with closing(connect()) as conn:
        in_stock = sizes_in_stock_by_product(conn)
        rows = conn.execute("SELECT * FROM catalogue").fetchall()

    scored = []
    for r in rows:
        if max_price is not None and r["price"] > max_price:
            continue
        if size is not None and size not in in_stock.get(r["product_id"], []):
            continue
        text = " ".join(
            [r["name"], r["garment_type"], r["description"], " ".join(json.loads(r["colors"])), " ".join(json.loads(r["search_tags"]))]
        ).lower()
        score = sum(1 for w in words if re.search(rf"\b{re.escape(singular(w))}(s|es)?\b", text))
        scored.append((score, r))

    best = max((score for score, _ in scored), default=0)
    if not scored or (words and best == 0):
        return SearchResult(match="none", total_matches=0, showing=0, products=[])
    matches = sorted((r for score, r in scored if score == best), key=lambda r: (r["price"], r["name"]))
    products = [to_hit(r, in_stock.get(r["product_id"], [])) for r in matches[:limit]]
    return SearchResult(
        match="all words" if best == len(words) else f"partial ({best} of {len(words)} words)",
        total_matches=len(matches),
        showing=len(products),
        min_price=min(r["price"] for r in matches),
        max_price=max(r["price"] for r in matches),
        products=products,
    )


def find_product(conn: sqlite3.Connection, product: str) -> sqlite3.Row | None:
    """Accept a product_id, an exact name, or a name typed like an id ("Basic Hoodie Big Yale")."""
    ref = product.strip()
    slug = re.sub(r"[^a-z0-9]+", "-", ref.lower()).strip("-")
    return conn.execute(
        "SELECT * FROM catalogue WHERE product_id = ? OR lower(name) = ? OR product_id = ?",
        (ref, ref.lower(), slug),
    ).fetchone()


def not_found(product: str) -> ProductNotFound:
    with closing(connect()) as conn:
        names = {r["name"]: r for r in conn.execute("SELECT * FROM catalogue")}
        in_stock = sizes_in_stock_by_product(conn)
    # Keyword matches first (shares words with the name), then near-spellings.
    hits = search_products(product).products[:3]
    for name in difflib.get_close_matches(product, list(names), n=3, cutoff=0.4):
        if len(hits) < 3 and all(h.name != name for h in hits):
            hits.append(to_hit(names[name], in_stock.get(names[name]["product_id"], [])))
    return ProductNotFound(
        error=f"No product matches '{product}'. Use a product_id from search_products or did_you_mean.",
        did_you_mean=hits,
    )


def get_product_info(product: str) -> ProductInfo | ProductNotFound:
    """Description, colors, and price for one product."""
    with closing(connect()) as conn:
        row = find_product(conn, product)
    if row is None:
        return not_found(product)
    return ProductInfo(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        price=row["price"],
    )


def check_stock(product: str, size: str | None = None) -> StockReport | ProductNotFound:
    """Units on hand for one product, per size, with the requested size called out."""
    with closing(connect()) as conn:
        row = find_product(conn, product)
        if row is None:
            return not_found(product)
        lines = stock_lines(conn, row["product_id"])

    requested = next((line for line in lines if line.size == size), None)
    return StockReport(
        product_id=row["product_id"],
        name=row["name"],
        price=row["price"],
        requested_size=size,
        requested_size_in_stock=None if size is None else bool(requested and requested.quantity > 0),
        stock_by_size=lines,
        sizes_in_stock=[line.size for line in lines if line.quantity > 0],
        sizes_sold_out=[line.size for line in lines if line.quantity == 0],
        total_stock=sum(line.quantity for line in lines),
    )


def category_of(garment_type: str) -> str:
    """Group the catalogue's 22 garment_type labels into the site's shopper-facing categories
    (same rules as frontend/src/categories.ts)."""
    g = garment_type.lower()
    if "quarter-zip" in g:
        return "Quarter-zips"
    if "jacket" in g or "fleece" in g:
        return "Jackets & fleece"
    if "hood" in g:
        return "Hoodies"
    if "t-shirt" in g:
        return "T-shirts"
    if "long-sleeve" in g:
        return "Long sleeves"
    return "Crewnecks"


MAX_SIMILAR = 5


def find_similar_products(
    product: str, size: str | None = None, color: str | None = None, max_price: float | None = None
) -> SimilarProducts | ProductNotFound:
    """Same-category products that are in stock in `size` (and list `color`), most alike first.

    Similarity = shared search tags + shared colors, then closest price. The product itself
    is never included, and nothing out of stock in the requested size is returned.
    """
    with closing(connect()) as conn:
        base = find_product(conn, product)
        if base is None:
            return not_found(product)
        in_stock = sizes_in_stock_by_product(conn)
        rows = conn.execute("SELECT * FROM catalogue WHERE product_id != ?", (base["product_id"],)).fetchall()

    category = category_of(base["garment_type"])
    base_tags = {t.lower() for t in json.loads(base["search_tags"])}
    base_colors = {c.lower() for c in json.loads(base["colors"])}
    want_color = color.lower().strip() if color else None

    scored = []
    for r in rows:
        sizes = in_stock.get(r["product_id"], [])
        colors = [c.lower() for c in json.loads(r["colors"])]
        if category_of(r["garment_type"]) != category or not sizes:
            continue
        if size is not None and size not in sizes:
            continue
        if want_color and not any(want_color in c for c in colors):
            continue
        if max_price is not None and r["price"] > max_price:
            continue
        overlap = len(base_tags & {t.lower() for t in json.loads(r["search_tags"])}) + len(base_colors & set(colors))
        scored.append((-overlap, abs(r["price"] - base["price"]), r["name"], r))

    scored.sort(key=lambda t: t[:3])
    return SimilarProducts(
        based_on=to_hit(base, in_stock.get(base["product_id"], [])),
        category=category,
        size=size,
        color=color,
        products=[to_hit(r, in_stock.get(r["product_id"], [])) for *_, r in scored[:MAX_SIMILAR]],
    )


# ---------------------------------------------------------------------------
# Customer memory: chat history for signed-in shoppers lives in chat_messages.
# ---------------------------------------------------------------------------

with closing(connect()) as _conn, _conn:
    _conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id)")


def customer_context(user_id: int) -> CustomerContext | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT name, first_name, last_name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    first, _, last = row["name"].partition(" ")
    return CustomerContext(
        first_name=row["first_name"] or first,
        last_name=row["last_name"] or last,
        email=row["email"],
        member_since=row["created_at"][:10],
    )


def viewed_product(product_id: str | None) -> ViewedProduct | None:
    """Trust the browser's product_id only if it is a real catalogue product."""
    if not product_id:
        return None
    with closing(connect()) as conn:
        row = conn.execute("SELECT product_id, name FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    return ViewedProduct(product_id=row["product_id"], name=row["name"]) if row else None


def encode_products(products: list[ProductSummary], page: PageResults | None) -> str | None:
    """products_json: a list of product snapshots (the seeded format), or an object when results went on the page."""
    if page is not None:
        return json.dumps(
            {
                "products": [p.model_dump() for p in products],
                "page": {"title": page.title, "search_id": page.search_id, "product_ids": [p.product_id for p in page.products]},
            }
        )
    return json.dumps([p.model_dump() for p in products]) if products else None


def decode_products(raw: str | None, by_id: dict[str, ProductSummary]) -> tuple[list[ProductSummary], PageResults | None]:
    """Rebuild cards from the current catalogue by product_id, so reloaded prices are never stale."""
    if not raw:
        return [], None
    data = json.loads(raw)

    def cards(ids: list[str]) -> list[ProductSummary]:
        return [by_id[i] for i in ids if i in by_id]

    if isinstance(data, list):  # seeded rows and chat-only replies
        return cards([d["product_id"] for d in data if isinstance(d, dict) and "product_id" in d]), None
    page_data = data.get("page") or {}
    page_cards = cards(page_data.get("product_ids", []))
    page = (
        PageResults(title=page_data.get("title", "Chat results"), search_id=page_data.get("search_id", "saved"), total=len(page_cards), products=page_cards)
        if page_cards
        else None
    )
    return cards([d["product_id"] for d in data.get("products", [])]), page


def load_chat_history(user_id: int, limit: int) -> list[StoredChatMessage]:
    """The shopper's most recent `limit` messages, oldest first."""
    by_id = {p.product_id: p for p in list_products()}
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM (SELECT * FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?) ORDER BY id",
            (user_id, limit),
        ).fetchall()
    messages = []
    for r in rows:
        products, page = decode_products(r["products_json"], by_id)
        messages.append(
            StoredChatMessage(
                id=r["id"], role=r["role"], content=r["content"], products=products, page=page, created_at=r["created_at"]
            )
        )
    return messages


def save_chat_exchange(
    user_id: int, message: str, reply: str, products: list[ProductSummary], page: PageResults | None
) -> None:
    """Store the shopper's message and the assistant's reply together (both or neither)."""
    with closing(connect()) as conn, conn:
        conn.execute("INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, message))
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user_id, reply, encode_products(products, page)),
        )


def clear_chat_history(user_id: int) -> int:
    with closing(connect()) as conn, conn:
        return conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,)).rowcount


# ---------------------------------------------------------------------------
# Audit trail: output/audit_trail.json is a JSON array that is only ever appended to.
# ---------------------------------------------------------------------------

AUDIT_PATH = HW4_DIR / "output" / "audit_trail.json"
_audit_lock = threading.Lock()
CARD_NUMBER = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def redact(text: str, limit: int = 300) -> str:
    """Mask card numbers and emails, and cap the length, before anything is logged."""
    text = EMAIL.sub("[email]", CARD_NUMBER.sub("[card number]", text))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def append_audit(entry: AuditEntry) -> None:
    """Append one entry to the JSON array without rewriting earlier entries.

    Only the closing "]" is overwritten, so past entries are never touched or wiped.
    A file lock keeps two requests from interleaving their writes.
    """
    record = json.dumps(entry.model_dump(), ensure_ascii=False, indent=2).encode()
    record = b"\n".join(b"  " + line for line in record.splitlines())
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.touch(exist_ok=True)
    with _audit_lock, open(AUDIT_PATH, "r+b") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            if size == 0:
                f.write(b"[\n" + record + b"\n]\n")
                return
            f.seek(max(0, size - 64))
            tail = f.read()
            end = tail.rfind(b"]")
            if end == -1:
                raise ValueError(f"{AUDIT_PATH} is not a JSON array; refusing to modify it")
            before = tail[:end].rstrip()  # cut just after the last entry (or the opening "[")
            f.seek(size - len(tail) + len(before))
            f.truncate()
            f.write((b"\n" if before.endswith(b"[") else b",\n") + record + b"\n]\n")
        finally:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_UN)
