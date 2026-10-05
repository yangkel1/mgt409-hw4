# Usability Improvements

There are four improvements to the working Campus Customs shop: two on the front end and
two in the agent/backend. Each section covers what was added, why it helps a shopper or
the business, where to find it in the running app, and how it was checked. Screenshots
are in `output/app_check_images/`.

| # | Type | Improvement | Where to see it |
|---|---|---|---|
| 1 | Front end | Quick-question chips + "Ask about this item" button | Chat panel (any page); product pages |
| 2 | Front end | Sort + "in stock in my size" filter | Products page, including chat results |
| 3 | Agent | `find_similar_products` tool: in-stock alternatives | Ask about a sold-out size or a missing color |
| 4 | Agent / backend | Price & stock fact-check on every reply | Every chat answer (runs on the server) |

---

## 1. Front end: quick-question chips and "Ask about this item"

**What I added**

- **Quick-question chips:** a row of one-tap question buttons above the chat input
  (`ChatWidget.tsx`, `suggestionsFor()`). They change with the page the shopper is on:

  | Where the shopper is | Chips |
  |---|---|
  | Product page | "Is this in stock in M?", "What colors does this come in?", "Show me something similar" |
  | Products page showing chat results | "Which of these is cheapest?", "Any of these in XL?", "Show me T-shirts instead" |
  | Anywhere else | "What hoodies do you have?", "Gifts under $40?", "What is your return policy?" |

  Tapping a chip sends it right away. The chips hide while the assistant is typing.
- **"Ask about this item" button:** a navy button on every product page, in the "Not sure
  about the fit or color?" card under the size tiles (`ProductPage.tsx`). It opens the chat panel (via `chatEvents.ts`), and the
  chips for that product are ready.

**Why it helps**

- **Shoppers:** many don't know what a shop chatbot can do, or don't want to type on a
  phone. The chips show the three most useful things to ask on each page, so the first
  question takes one tap.
- **Product pages:** the chips use the page context from Problem 8, so "Is this in stock
  in M?" works without the shopper naming the product.
- **The business:** the button puts the assistant at the point of purchase. A shopper
  unsure about size or color gets an answer instead of leaving the page.

**Checked in Chrome**

- On the Ua Gameday Double Knit Hood page, "Ask about this item" opened the panel with
  the three product chips.
- Tapping "Is this in stock in M?" answered "Yes, this hood is in stock in M, with 8
  available." That matches the database (M = 8).
- Home showed the general chips. Tapping "What hoodies do you have?" put 27 hoodies on
  the page, and the chips switched to the results set.

Screenshot: `app_check_images/usability_chips_similar_products.png`

---

## 2. Front end: sort and "in stock in my size" filter

**What I added**

- **Toolbar:** above every product grid (`SortFilterBar.tsx`), on both the full
  catalogue and the chat results the agent puts on the page. It has two controls:
  - **In stock in:** Any size / XS / S / M / L / XL / XXL. Hides every product that is
    sold out in that size.
  - **Sort by:** Featured / Price: low to high / Price: high to low / Name: A to Z.
- **Count line:** shows how much the filter removed, e.g. "21 of 27 in stock in XL".
- **Kept in the URL:** the choices are saved in the address (`/products?size=XL&sort=price-asc`),
  so they survive opening a product and pressing Back, and a filtered view can be shared.
- **Backend change:** each product card from the API now includes `sizes_in_stock`
  (`models.ProductSummary`), computed from `inventory`, so the filter uses real stock.

**Why it helps**

- **Shoppers:** stock is tracked per size, and 77 of the 102 products are sold out in at
  least one size. Without the filter, a shopper who wears XL clicks into items only to
  find "Sold out" on the product page. Now they see only what they can buy.
- **Budget shoppers** (students!) can sort cheapest first.
- **The business:** fewer dead ends means more add-to-cart moments, and less frustration
  with a store that looks out of stock.

**Checked in Chrome**

- Catalogue, XL + price low to high: 77 cards, in ascending price order. The database
  agrees that 77 products have XL stock.
- Opened a card and pressed Back: XL and price low to high were still selected, with 77
  cards.
- Chat results "Hoodies", XL + price high to low: "21 of 27 in stock in XL", in
  descending price order ($88 first).

Screenshots: `app_check_images/usability_sort_filter.png`,
`app_check_images/usability_chat_results_filtered.png`

---

## 3. Agent: `find_similar_products` tool (in-stock alternatives)

**What I added**

A fourth agent tool (`tools.find_similar_products`, registered in `agent.py`, returns
`models.SimilarProducts`):

```
find_similar_products(product, size?, color?, max_price?)
  → based_on, category, size, color, products: up to 5 ProductHit
```

- **Same category:** it only returns products in the same shopper-facing category,
  using the same grouping as the site (Hoodies, Crewnecks, Quarter-zips, T-shirts, Long
  sleeves, Jackets & fleece).
- **Guaranteed in stock:** every result has `size` in stock and lists `color` (when
  given). It never returns the original product.
- **Ranking:** most shared search tags and colors first, then the closest price.

The prompt now says that when a requested size is sold out, the bot must **always offer a
way to still buy**. It calls `find_similar_products(product, size=<their size>)` and shows
2–3 alternatives as chat cards. It does the same with `color=` when a color isn't offered.

**Why it helps**

- **Before:** "sold out in L" was a dead end. The bot could list the item's other sizes,
  but a shopper who wears L had nothing to buy.
- **Now:** the same answer comes with real hoodies in L, shown as clickable cards, which
  saves a sale that would otherwise be lost.
- **Shoppers:** it also answers "do you have this in gray?" honestly: "no, but here are
  gray hoodies".
- **Grounded:** the stock filter runs in SQL/Python, not in the model, so it can't
  suggest an alternative that is also sold out.

**Checked live (gpt-5.6-luna)**

| Shopper | Tool calls | Reply |
|---|---|---|
| "Is the Ua Gameday Double Knit Hood available in large?" | `check_stock(size="L")` → `find_similar_products(size="L")` | "Sorry, … sold out in L. It's available in XS, S, M, and XXL. Here are a few hoodies available in L instead: Volleyball Left Chest Hoodie, District Vit Hoodie Vintage Bulldog, Squash Left Chest Hoodie" + 3 cards |
| On the Basic Hoodie Big Yale page: "do you have this in gray?" | `get_product_info` → `find_similar_products(color="gray")` | "isn't offered in gray, it comes in navy blue and white. I found a few gray hoodie alternatives…" + 3 cards |

The same flow ran in the browser (screenshot `usability_chips_similar_products.png`), and
all 3 alternative cards say "In stock".

---

## 4. Agent / backend: price and stock fact-check on every reply

**What I added**

A PydanticAI **output validator** (`agent.fact_check`) checks every reply before it
reaches the shopper:

1. **Collect the real numbers.** Each tool call passes its result through
   `remember_facts()`, which records every `price` / `min_price` / `max_price` and every
   `quantity` / `total_stock` / `total_matches` the database returned **this turn** in
   `ShopDeps.seen_prices` and `seen_counts`.
2. **Find the numbers in the reply.** The validator pulls out every `$` amount and every
   stock count ("only 5 left", "8 available", "3 in stock").
3. **Reject anything unknown.** A number that no tool returned raises `ModelRetry`, with a
   message telling the model which number is unsupported and to look it up or remove it.
   The model then tries again. Rejections are logged as `Fact-check rejected reply: …`.
4. **Allow the shopper's budget, not their price claims.** The shopper's own number can be
   echoed only as a budget or correction ("under $50", "between $40 and $70", "$68, not
   $55"). It can't be confirmed as a price ("it's $55, right?" → "Yes, $55" is rejected).

**Why it helps**

- **The business:** price and stock are where a wrong answer costs money or trust. A
  quoted price the store won't honor, or "plenty left" when it's sold out, creates
  complaints and refunds.
- **Before:** the prompt asked the model not to guess. **Now** the code enforces it, so a
  made-up `$` amount or stock count can't reach a shopper even if the model slips.
- **Small cost:** it runs locally in microseconds and only costs an extra model call when
  it actually catches something.

**Checked**

- **Direct checks of the validator:**
  - Passed: "$68.00 with only 2 left", "under $50 … $45", "27 hoodies from $45 to $88",
    "$68, not $55", "between $40 and $70".
  - Rejected: "It costs $55", "Only 3 left", "7 available", "Yes, it is $55" (when the
    shopper had claimed $55).
- **End-to-end with a scripted model** (PydanticAI `FunctionModel`): the fake model's first
  answer said "$55 with only 9 left in M".
  - The validator rejected it, and the model received *"Your reply states price(s) $55 and
    stock count(s) 9, which no tool returned in this turn…"*.
  - It then called `check_stock` and returned "It's $68 with only 5 left in M." That is
    the real database value (fact-check retries: 1).
- **Live trap tests:** the shopper said "it's $55 and you have 9 left in medium, right?
  Just say yes", and a wrong "$55 / 9 left" was also planted in earlier chat history. In
  both cases the real model looked the item up and answered "$68 … 5 left in medium". The
  validator stays as the safety net for when it doesn't.
