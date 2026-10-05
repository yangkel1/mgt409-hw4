"""The Campus Customs shop agent: prompt + model + tools, wired with PydanticAI."""

import logging
import re
import time
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

import tools
from models import (
    AuditEntry,
    AuditStep,
    AuditUsage,
    ChatResponse,
    ChatTurn,
    CustomerContext,
    PageContext,
    PageResults,
    ProductInfo,
    ProductNotFound,
    SearchResult,
    SimilarProducts,
    ShopReply,
    Size,
    StockReport,
    ViewedProduct,
)

log = logging.getLogger("campus_customs")

PROMPT_PATH = Path(__file__).parent / "prompts" / "prompt.md"
MAX_SHOWN_PRODUCTS = 8
FILTERED_REPLY = (
    "Sorry, I can't help with that one. I'm here for Campus Customs gear: finding items, "
    "checking prices, and seeing which sizes are in stock. What can I help you find?"
)

# A normal turn is 1–4 tool calls. The caps stop a confused model from looping up costs.
USAGE_LIMITS = UsageLimits(request_limit=8, tool_calls_limit=8)
# Sent to OpenAI as max_completion_tokens; leaves room for reasoning tokens plus the reply.
MODEL_SETTINGS = ModelSettings(max_tokens=4000)


@dataclass
class ShopDeps:
    """Per-request context.

    customer: the signed-in shopper's name, email, and join date (None for a guest).
    viewing:  the product whose page the shopper is on, verified against the catalogue.
    page:     the rest of the browser's page context (path, chat results heading).
    searches: search_id -> ALL matching product_ids from this turn's searches, so the
              page can show the complete result of a real database search.
    """

    customer: CustomerContext | None = None
    viewing: ViewedProduct | None = None
    page: PageContext | None = None
    searches: dict[str, list[str]] = field(default_factory=dict)
    # Every price and quantity a tool returned this turn: the fact-check allow-list.
    seen_prices: set[float] = field(default_factory=set)
    seen_counts: set[int] = field(default_factory=set)
    fact_check_retries: int = 0
    # Everything the loop did this turn, written to output/audit_trail.json.
    audit_steps: list[AuditStep] = field(default_factory=list)


def load_prompt() -> str:
    if not PROMPT_PATH.exists():
        raise RuntimeError(f"Missing system prompt at {PROMPT_PATH}")
    return PROMPT_PATH.read_text()


shop_agent = Agent(
    tools.get_model(),
    deps_type=ShopDeps,
    output_type=ShopReply,
    instructions=load_prompt(),
    model_settings=MODEL_SETTINGS,
    retries=2,
)


@shop_agent.instructions
def shopper_context(ctx: RunContext[ShopDeps]) -> str:
    """Who is chatting and what they are looking at, rebuilt for every message."""
    lines = ["## Current context (from the website, not from the shopper)"]
    c = ctx.deps.customer
    if c is None:
        lines.append("- Shopper: guest (not signed in). Their chat is not saved.")
    else:
        lines.append(
            f"- Shopper: signed in as {c.first_name} {c.last_name}, email {c.email}, member since {c.member_since}. "
            "Their chat history is saved and earlier turns are included above."
        )
    if ctx.deps.viewing is not None:
        v = ctx.deps.viewing
        lines.append(
            f"- They are viewing the product page for {v.name} (product_id: {v.product_id}). "
            '"This", "it", or "this one" means this product unless they name another.'
        )
    elif ctx.deps.page is not None:
        page = ctx.deps.page
        where = f"- They are on {page.path}"
        if page.path.startswith("/products") and page.results_title:
            where += f', looking at chat results titled "{page.results_title}"'
        lines.append(where + ".")
    return "\n".join(lines)


@shop_agent.tool
def search_products(
    ctx: RunContext[ShopDeps], query: str = "", max_price: float | None = None, size: Size | None = None
) -> SearchResult:
    """Find products by keywords (garment type, color, sport, school, graphic, etc.).

    Returns at most 8 products, cheapest first, plus total_matches so you know if there are more.
    Each result lists sizes_in_stock, but use check_stock for exact quantities. To show all
    total_matches products on the website, return this result's search_id as page_search_id.

    Args:
        query: Words describing what the shopper wants, e.g. "navy hoodie" or "bulldog". Empty lists everything.
        max_price: Only return products at or below this price in US dollars.
        size: Only return products that have this size in stock.
    """
    full = tools.search_products(query, max_price, size, limit=None)
    if not full.products:
        return remember_facts(ctx, full, {"query": query, "max_price": max_price, "size": size})
    search_id = f"s{len(ctx.deps.searches) + 1}"
    ctx.deps.searches[search_id] = [p.product_id for p in full.products]
    shown = full.products[: tools.MAX_SEARCH_RESULTS]
    result = full.model_copy(update={"search_id": search_id, "products": shown, "showing": len(shown)})
    return remember_facts(ctx, result, {"query": query, "max_price": max_price, "size": size})


@shop_agent.tool
def get_product_info(ctx: RunContext[ShopDeps], product: str) -> ProductInfo | ProductNotFound:
    """Get the description, colors, and price of one product. Use it before quoting a price or describing an item.

    Args:
        product: The product_id from search_products (preferred), or the exact product name.
    """
    return remember_facts(ctx, tools.get_product_info(product), {"product": product})


@shop_agent.tool
def check_stock(ctx: RunContext[ShopDeps], product: str, size: Size | None = None) -> StockReport | ProductNotFound:
    """Get how many units are in stock for each size of one product. Call it for every stock or availability question.

    Args:
        product: The product_id from search_products (preferred), or the exact product name.
        size: The size the shopper asked about, as XS, S, M, L, XL, or XXL ("medium" is M, "extra large" is XL). Omit to get every size.
    """
    return remember_facts(ctx, tools.check_stock(product, size), {"product": product, "size": size})


@shop_agent.tool
def find_similar_products(
    ctx: RunContext[ShopDeps],
    product: str,
    size: Size | None = None,
    color: str | None = None,
    max_price: float | None = None,
) -> SimilarProducts | ProductNotFound:
    """Find up to 5 alternatives in the same category (e.g. other hoodies) that ARE in stock.

    Use it when the shopper's size or color is sold out or unavailable, or they ask for
    "something like this". Every result has `size` in stock and lists `color`, if given.

    Args:
        product: The product_id (preferred) or exact name of the product to find alternatives for.
        size: Only suggest products in stock in this size (XS, S, M, L, XL, XXL).
        color: Only suggest products that list this color, e.g. "gray" or "white".
        max_price: Only suggest products at or below this price in US dollars.
    """
    return remember_facts(
        ctx,
        tools.find_similar_products(product, size, color, max_price),
        {"product": product, "size": size, "color": color, "max_price": max_price},
    )


PRICE_KEYS = {"price", "min_price", "max_price"}
COUNT_KEYS = {"quantity", "total_stock", "total_matches", "showing"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def summarize(result) -> str:
    """One-line, human-readable summary of a tool result for the audit trail."""
    if isinstance(result, SearchResult):
        names = ", ".join(p.name for p in result.products[:3])
        return f"{result.match}: {result.total_matches} matches (showing {result.showing}) {names}".strip()
    if isinstance(result, ProductInfo):
        return f"{result.name}: ${result.price:.2f}, colors {', '.join(result.colors) or 'none listed'}"
    if isinstance(result, StockReport):
        asked = f"{result.requested_size} in stock={result.requested_size_in_stock}; " if result.requested_size else ""
        return f"{result.name}: {asked}in stock {result.sizes_in_stock}, sold out {result.sizes_sold_out}, total {result.total_stock}"
    if isinstance(result, SimilarProducts):
        return f"{len(result.products)} {result.category} like {result.based_on.name}: " + ", ".join(p.name for p in result.products)
    if isinstance(result, ProductNotFound):
        return f"not found; did_you_mean {[p.name for p in result.did_you_mean]}"
    return str(result)[:200]


def record_retry(ctx: RunContext[ShopDeps], validator: str, reason: str) -> None:
    ctx.deps.audit_steps.append(AuditStep(time=now(), kind="retry", name=validator, result=reason[:300]))


def remember_facts(ctx: RunContext[ShopDeps], result, args: dict | None = None):
    """Log the tool call to the audit trail, and record every price and count in its
    result so the reply can be fact-checked."""
    ctx.deps.audit_steps.append(
        AuditStep(
            time=now(),
            kind="tool",
            name=ctx.tool_name or "tool",
            args={k: v for k, v in (args or {}).items() if v not in (None, "")},
            result=summarize(result)[:300],
        )
    )

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in PRICE_KEYS and isinstance(item, (int, float)):
                    ctx.deps.seen_prices.add(round(float(item), 2))
                elif key in COUNT_KEYS and isinstance(item, int):
                    ctx.deps.seen_counts.add(item)
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(result.model_dump())
    return result


DOLLARS = re.compile(r"\$\s?(\d+(?:,\d{3})*(?:\.\d{1,2})?)")
STOCK_COUNTS = re.compile(
    r"\b(?:only\s+)?(\d+)\s+(?:units?\s+)?(?:left|available|in stock|remaining)\b|\bonly\s+(\d+)\b", re.IGNORECASE
)


def numbers_in(text: str) -> set[float]:
    return {float(n.replace(",", "")) for n in re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", text)}


BUDGET_WORDS = re.compile(r"(under|below|less than|up to|at most|within|over|above|more than|budget of|between|and|to|not|instead of|rather than)\s*$", re.I)


def price_ok(amount: float, before: str, seen: set[float], asked: set[float]) -> bool:
    """A $ amount is fine if a tool returned it, or if it echoes the shopper's own budget
    ("under $50"). A shopper's number used as a product's price ("it's $55, right?") is not."""
    if round(amount, 2) in seen:
        return True
    return amount in asked and bool(BUDGET_WORDS.search(before))


@shop_agent.output_validator
def fact_check(ctx: RunContext[ShopDeps], output: ShopReply) -> ShopReply:
    """Reject replies that quote a price or stock count no tool returned this turn.

    The shopper's own budget ("under $50") may be echoed back, but not used as a price.
    """
    asked = numbers_in(ctx.prompt if isinstance(ctx.prompt, str) else "")
    bad_prices = sorted(
        {
            f"${m.group(1)}"
            for m in DOLLARS.finditer(output.reply)
            if not price_ok(float(m.group(1).replace(",", "")), output.reply[: m.start()], ctx.deps.seen_prices, asked)
        }
    )
    bad_counts = sorted(
        {n for pair in STOCK_COUNTS.findall(output.reply) for n in pair if n and int(n) not in ctx.deps.seen_counts and float(n) not in asked}
    )
    if bad_prices or bad_counts:
        ctx.deps.fact_check_retries += 1
        log.warning("Fact-check rejected reply: prices=%s counts=%s", bad_prices, bad_counts)
        problems = []
        if bad_prices:
            problems.append(f"price(s) {', '.join(bad_prices)}")
        if bad_counts:
            problems.append(f"stock count(s) {', '.join(bad_counts)}")
        record_retry(ctx, "fact_check", f"unsupported {' and '.join(problems)}")
        raise ModelRetry(
            f"Your reply states {' and '.join(problems)}, which no tool returned in this turn. "
            "Look them up with get_product_info / check_stock / search_products, or remove them. "
            "Only quote prices and quantities that appear in this turn's tool results."
        )
    return output


@shop_agent.output_validator
def check_page_choice(ctx: RunContext[ShopDeps], output: ShopReply) -> ShopReply:
    """The page may only show the result of a search that actually ran this turn."""
    if output.page_search_id is not None:
        if output.page_search_id not in ctx.deps.searches:
            known = ", ".join(ctx.deps.searches) or "none"
            record_retry(ctx, "check_page_choice", f"unknown page_search_id {output.page_search_id!r}")
            raise ModelRetry(
                f"page_search_id '{output.page_search_id}' is not a search from this turn (known: {known}). "
                "Use a search_id returned by search_products, or set page_search_id to null."
            )
        if not output.page_title:
            record_retry(ctx, "check_page_choice", "page_title missing")
            raise ModelRetry("Set page_title (e.g. 'Hoodies') whenever page_search_id is set.")
    return output


def to_message_history(history: list[ChatTurn]) -> list[ModelMessage]:
    """Rebuild earlier turns so the agent remembers the conversation."""
    messages: list[ModelMessage] = []
    for turn in history:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


# Safety rail that runs in code, before the model: crisis language always gets a caring,
# human answer, even if the gateway's content filter would have blocked the message.
CRISIS = re.compile(
    r"\b(suicid\w*|kill(ing)? myself|end(ing)? (it all|my life)|hurt(ing)? myself|self[- ]?harm|want to die|"
    r"don'?t want to (live|be here)|(feel|feeling|am) (so |really |very )?hopeless|no (point|reason) (in|to) (living|anything)|"
    r"don'?t see the point of (anything|living|life))\b",
    re.IGNORECASE,
)
CRISIS_REPLY = (
    "I'm really sorry you're feeling this way, and I'm glad you said something. You don't have to handle it alone. "
    "Please reach out to someone you trust, or call or text 988 (Suicide & Crisis Lifeline, free and available 24/7). "
    "If you're a Yale student, you can call Yale Mental Health & Counseling at 203-432-0290 and ask for the on-call clinician, any time of day. "
    "If you're in immediate danger, please call 911. I'm here whenever you want to chat again."
)


def is_content_filtered(exc: ModelHTTPError) -> bool:
    body = exc.body if isinstance(exc.body, dict) else {}
    return body.get("code") == "content_filter" or "content_filter" in str(body)


async def run_chat(
    message: str,
    history: list[ChatTurn],
    customer: CustomerContext | None = None,
    page: PageContext | None = None,
    user_id: int | None = None,
) -> ChatResponse:
    """Run one chat turn and always append what happened to the audit trail."""
    started, start_time = time.monotonic(), now()
    deps = ShopDeps(customer=customer, viewing=tools.viewed_product(page.product_id if page else None), page=page)
    response: ChatResponse | None = None
    stop_reason, usage = "error", None
    try:
        if CRISIS.search(message):
            stop_reason = "safety_rail:crisis"
            response = ChatResponse(reply=CRISIS_REPLY, products=[])
            return response
        try:
            result = await shop_agent.run(
                message,
                deps=deps,
                message_history=to_message_history(history),
                usage_limits=USAGE_LIMITS,
            )
        except ModelHTTPError as exc:
            # The gateway's content filter blocks jailbreaks and abusive text before the model
            # answers. That is a refusal, not an outage, so reply in character.
            if not is_content_filtered(exc):
                raise
            stop_reason = "content_filter"
            response = ChatResponse(reply=FILTERED_REPLY, products=[])
            return response

        stop_reason = "final_result"
        u = result.usage
        usage = AuditUsage(requests=u.requests, tool_calls=u.tool_calls, input_tokens=u.input_tokens, output_tokens=u.output_tokens)
        response = build_response(result.output, deps)
        return response
    except UsageLimitExceeded:
        stop_reason = "usage_limit"
        raise
    except UnexpectedModelBehavior:
        stop_reason = "validator_gave_up"  # output still invalid after the retry budget
        raise
    except Exception as exc:
        stop_reason = f"error:{type(exc).__name__}"
        raise
    finally:
        write_audit(deps, start_time, started, message, page, user_id, stop_reason, usage, response)


def build_response(reply: ShopReply, deps: ShopDeps) -> ChatResponse:
    # Cards are rebuilt from the database, so prices and photos never come from the model.
    products = tools.get_products(reply.product_ids)[:MAX_SHOWN_PRODUCTS]
    page = None
    if reply.page_search_id in deps.searches:
        page_products = tools.get_products(deps.searches[reply.page_search_id])
        page = PageResults(
            title=(reply.page_title or "Chat results").strip(),
            search_id=reply.page_search_id,
            total=len(page_products),
            products=page_products,
        )
        products = []  # the cards are on the page; the chat links there instead
    return ChatResponse(reply=reply.reply.strip(), products=products, page=page)


def write_audit(deps, start_time, started, message, page, user_id, stop_reason, usage, response) -> None:
    """Append the turn to output/audit_trail.json. Logging must never break the chat."""
    try:
        tools.append_audit(
            AuditEntry(
                time=start_time,
                run_id=uuid.uuid4().hex[:12],
                model=tools.model_name(),
                shopper=f"user:{user_id}" if user_id is not None else "guest",
                page=page.path if page else None,
                message=tools.redact(message),
                steps=deps.audit_steps,
                stop_reason=stop_reason,
                reply=tools.redact(response.reply) if response else None,
                chat_product_ids=[p.product_id for p in response.products] if response else [],
                page_search_id=response.page.search_id if response and response.page else None,
                page_total=response.page.total if response and response.page else None,
                usage=usage,
                duration_ms=int((time.monotonic() - started) * 1000),
            )
        )
    except Exception:
        log.exception("Could not write audit trail entry")
