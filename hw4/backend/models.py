"""Pydantic types shared by the API and the PydanticAI agent."""

from typing import Literal

from pydantic import BaseModel, Field


class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductSummary(BaseModel):
    """What a product card needs on the Products page."""

    product_id: str
    name: str
    garment_type: str
    price: float
    short_description: str
    colors: list[str]
    image_url: str
    total_stock: int
    sizes_in_stock: list[str] = Field(default_factory=list, description="Sizes with quantity > 0, XS to XXL")


class ProductDetail(ProductSummary):
    """Everything the single-item page shows."""

    description: str
    search_tags: list[str]
    inventory: list[SizeStock]


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    """The only user fields that ever leave the server (never the password hash)."""

    id: int
    first_name: str
    last_name: str
    email: str


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------


class ChatTurn(BaseModel):
    """One earlier message in the conversation, as the website remembers it."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class PageContext(BaseModel):
    """Where the shopper is on the site when they send a message (sent by the browser)."""

    path: str = Field(default="/", max_length=200, description="Current URL path, e.g. /products/basic-hoodie-big-yale")
    product_id: str | None = Field(default=None, max_length=120, description="Set when on a single-item page")
    results_title: str | None = Field(default=None, max_length=120, description="Heading of chat results shown on the Products page")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    # Guests only: signed-in history is loaded from the database instead.
    history: list[ChatTurn] = Field(default_factory=list, max_length=40)
    page: PageContext | None = None


class ShopReply(BaseModel):
    """The agent's structured output."""

    reply: str = Field(description="The message shown to the shopper, in plain text (no Markdown).")
    product_ids: list[str] = Field(
        default_factory=list,
        description="product_id values (from tool results) of products to show as cards in the chat, most relevant first. Empty if none apply or if page_search_id is set.",
    )
    page_search_id: str | None = Field(
        default=None,
        description="search_id of a search_products result to show as product cards on the website's Products page. Set it when the shopper is browsing a type of item; leave null otherwise.",
    )
    page_title: str | None = Field(
        default=None,
        description='Short heading for the page results, e.g. "Hoodies" or "Navy items under $50". Required when page_search_id is set.',
    )


class PageResults(BaseModel):
    """Search results the website shows as product cards on the Products page."""

    title: str
    search_id: str
    total: int
    products: list[ProductSummary]


class ChatResponse(BaseModel):
    """What POST /api/chat returns. All product data is built from the database, never from model text."""

    reply: str
    products: list[ProductSummary] = Field(description="Small cards shown inside the chat")
    page: PageResults | None = Field(default=None, description="Matches to show on the Products page, or null")


# ---------------------------------------------------------------------------
# Agent tool results. Every value is copied from campus_customs.db by tools.py;
# derived fields (status, in_stock, sizes_*) are computed in Python so the model
# never has to do the arithmetic or comparisons itself.
# ---------------------------------------------------------------------------

Size = Literal["XS", "S", "M", "L", "XL", "XXL"]
StockStatus = Literal["in stock", "low stock", "sold out"]


class ProductHit(BaseModel):
    """One search result: enough to recommend a product, not to quote its stock per size."""

    product_id: str
    name: str
    garment_type: str
    price: float = Field(description="US dollars, from catalogue.price")
    colors: list[str]
    sizes_in_stock: list[Size] = Field(description="Sizes with quantity > 0")


class SearchResult(BaseModel):
    search_id: str | None = Field(
        default=None, description="Pass this as page_search_id to show ALL total_matches products on the website"
    )
    match: str = Field(description='"all words", "partial (n of m words)", or "none"')
    total_matches: int
    showing: int
    min_price: float | None = Field(default=None, description="Lowest price across ALL total_matches products")
    max_price: float | None = Field(default=None, description="Highest price across ALL total_matches products")
    products: list[ProductHit]


class ProductInfo(BaseModel):
    """Description and price for one product."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    price: float = Field(description="US dollars, from catalogue.price")


class StockLine(BaseModel):
    size: Size
    quantity: int = Field(description="Units on hand, from inventory.quantity")
    status: StockStatus


class StockReport(BaseModel):
    """Stock for one product, for every size or the one the shopper asked about."""

    product_id: str
    name: str
    price: float
    requested_size: Size | None = Field(description="The size asked about, or null for all sizes")
    requested_size_in_stock: bool | None = Field(description="True if requested_size has quantity > 0; null when no size was asked")
    stock_by_size: list[StockLine] = Field(description="All six sizes, XS to XXL")
    sizes_in_stock: list[Size]
    sizes_sold_out: list[Size]
    total_stock: int


class SimilarProducts(BaseModel):
    """In-stock alternatives to one product (e.g. when the shopper's size is sold out)."""

    based_on: ProductHit
    category: str = Field(description="Shopper-facing category the alternatives come from, e.g. Hoodies")
    size: Size | None = Field(description="Every alternative has this size in stock, when given")
    color: str | None = Field(description="Every alternative lists this color, when given")
    products: list[ProductHit] = Field(description="Up to 5 alternatives, most similar first")


class ProductNotFound(BaseModel):
    """Returned instead of a lookup when the id or name doesn't match a product."""

    error: str
    did_you_mean: list[ProductHit]


# ---------------------------------------------------------------------------
# Customer memory
# ---------------------------------------------------------------------------


class CustomerContext(BaseModel):
    """What the agent knows about a signed-in shopper. Never the password hash."""

    first_name: str
    last_name: str
    email: str
    member_since: str = Field(description="Account creation date, YYYY-MM-DD")


class ViewedProduct(BaseModel):
    """The product on the page the shopper is looking at, verified against the catalogue."""

    product_id: str
    name: str


class StoredChatMessage(BaseModel):
    """One saved chat_messages row, as the website shows it on return."""

    id: int
    role: Literal["user", "assistant"]
    content: str
    products: list[ProductSummary] = Field(default_factory=list)
    page: PageResults | None = None
    created_at: str


# ---------------------------------------------------------------------------
# Audit trail (output/audit_trail.json): one AuditEntry per chat turn, appended.
# ---------------------------------------------------------------------------


class AuditStep(BaseModel):
    """One thing that happened inside the agent loop."""

    time: str = Field(description="UTC ISO timestamp")
    kind: Literal["tool", "retry"] = Field(description="tool = a tool call; retry = an output validator sent the model back")
    name: str = Field(description="Tool name, or the validator that raised the retry")
    args: dict = Field(default_factory=dict, description="Tool arguments as the model sent them")
    result: str = Field(description="One-line summary of the tool result, or the retry reason")


class AuditUsage(BaseModel):
    requests: int = Field(description="Model calls in this turn (capped by request_limit)")
    tool_calls: int
    input_tokens: int
    output_tokens: int


class AuditEntry(BaseModel):
    """One chat turn through the agent loop. No names, emails, or passwords are stored."""

    time: str = Field(description="UTC ISO timestamp when the turn started")
    run_id: str
    model: str
    shopper: str = Field(description='"guest" or "user:<id>" (no name or email)')
    page: str | None = Field(description="Path the shopper was on, e.g. /products/basic-hoodie-big-yale")
    message: str = Field(description="Shopper message, truncated, with card numbers / emails masked")
    steps: list[AuditStep]
    stop_reason: str = Field(
        description='"final_result" (normal), "content_filter", "usage_limit", "validator_gave_up", or "error:<Type>"'
    )
    reply: str | None = Field(description="Reply shown to the shopper, truncated")
    chat_product_ids: list[str] = Field(default_factory=list)
    page_search_id: str | None = None
    page_total: int | None = Field(default=None, description="Cards put on the Products page")
    usage: AuditUsage | None = None
    duration_ms: int
