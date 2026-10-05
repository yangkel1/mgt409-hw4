# AI_prompts.md

Log of the prompts I typed into my vibe coder (Claude Code) while building HW4, with one
section per problem. Spelling and grammar in my prompts have been corrected for
readability, and the intent of each prompt is unchanged. My real Portkey API key never
appears here. It lives only in `.env`, which is excluded from the repo.

**Project:** Campus Customs shop + chatbot. React + Vite TypeScript front end, FastAPI
backend, and a PydanticAI agent that answers from the local SQLite database.

---

## Setup: course material, scenario, and project layout

*(Before the numbered problems: making sure the vibe coder had the slides, the scenario,
and the required repo layout.)*

**Prompt 1**

> I need to do HW 4. Do you have all the slides to reference to complete it successfully?

**Follow-up**

> I just uploaded the lectures. Do you see them?

*What was lacking after the first:* the Lecture 7 and 8 slides (web apps and deployment)
were not in the workspace yet, so the vibe coder could not reference them.

**Prompt 2**

> Here are the instructions for HW 4.
>
> *(attached: the HW 4 scenario and data section. Build a React + Vite TS front end and
> a FastAPI backend with a PydanticAI agent. `data/campus_customs.db` has `catalogue`,
> `inventory`, and `users` tables, and `data/products/` has the images. Use
> `PORTKEY_API_KEY`, push to a public GitHub repo, and don't commit the DB or images.)*

**Prompt 3**

> Output of HW4: push to GitHub and submit the URL. Put your code in a folder named `hw4`
> and push it to a public GitHub repository. On Canvas, submit the repo URL (the link
> graders can open and clone). You don't need a zip for this homework. Do not put the
> real `.env`, `campus_customs.db`, or product images in the GitHub repo. Use
> `.gitignore`. Include `.env.example` with placeholders only. The expected file layout
> is in the screenshot.
>
> *(attached: expected `hw4/` file tree)*

---

## Problem 1: Vibe coder prompts

**Prompt**

> Problem 1: vibe coder prompts. Create `AI_prompts.md` at the start of the assignment
> and keep it updated as you work. This file is the log of what I typed into the vibe
> coder. Describe each problem to your vibe coder. Put one section for each problem. Each
> section must include: the problem number and title, at least one prompt I typed, one
> follow-up prompt if needed, and one sentence on what was lacking after the first. Your
> running site, database writes, and screenshots are the evidence; you do not need an
> extra proof essay beyond these prompts. If I make a spelling error, assume it was a
> mistake and assume I wrote everything with proper grammar and spelling.

*Follow-up:* none needed. The log already existed from setup and was restructured into
one section per problem.

---

## Problem 2: Analyze the database

**Prompt**

> Problem 2: analyze the database. Unzip the `data.zip` folder posted in my AI folder so
> you have the database. Look at the database `data/campus_customs.db` and understand the
> fields of each table. Make sure you understand `catalogue`, `inventory`, and `users`, as
> well as the other ones.

**Follow-up**

> Part 2 of Problem 2: start the file `output/harness.md`. Write down each table and its
> fields, with one short line on why each field matters for the shop or chatbot. You will
> keep growing this harness file in later problems (models, tools, safety, specs).

*What was lacking after the first:* the vibe coder understood the schema, but there was
no written record of each field's purpose to build the models and tools on.

---

## Problem 3: Build the Campus Customs website

**Prompt**

> Problem 3: build the Campus Customs website. Scaffold a React + Vite + TypeScript front
> end for Campus Customs. Put a nav bar at the top that links to the main pages: Home,
> Products, About Us, Log in, Create account. Pull Campus Customs–style wording from
> yalebulldogblue.com for Home and About Us, but write these pages in different words from
> the original site text. On the Products page, show product images from the catalogue
> (use the image paths in the database) with basic product info (name, price, short
> description). Make each product open a single-item page (large image on one side, full
> product text on the other: description, price, size/stock when you have them).
> Clicking a card on Products should take the shopper there. Add a chat interface in the
> bottom right of the site (a floating chat panel is fine). It does not need to talk to an
> agent yet; a stub that will call the backend later is enough for this problem. You will
> need a small API soon to read the database. It is fine to start a simple FastAPI app in
> `backend/main.py` just to serve products and images, then grow it into the agent backend
> in Problem 5.

*Follow-up:* none needed. The site was checked in a real browser (102 product cards,
category filter, card → item page with per-size stock, chat stub with typing indicator,
mobile layout).

---

## Problem 4: Create account and login

**Prompt**

> Problem 4: create account and login. Build a normal create-account / login flow. Create
> account: first name, last name, email, password (a confirm-password field would be nice
> as well). Login: email and password. New accounts go into the `users` table. Make sure
> to store passwords securely so hackers (human or AI) cannot access them. The seed
> database already has a test user you can use while building: email
> `test@campuscustoms.yale.edu`, password `password`. Confirm that you can log in as that
> user and that a brand-new account you create also works. Update `output/harness.md`
> with how auth works (what you store for a user and how passwords are protected).

*Follow-up:* none needed. The vibe coder matched the database's existing PBKDF2 format
(confirmed with the test user's password) and verified both accounts in a real browser.

---

## Problem 5: PydanticAI agent backend

**Prompt**

> Problem 5: PydanticAI agent backend. Build the shop chatbot as a PydanticAI agent behind
> FastAPI, plugged into your front-end chat widget. Put the API app in `backend/main.py`;
> that is the file you run with uvicorn. Keep the agent as these 4 files next to it (same
> idea as HW 3), as in the screenshot. Put the Campus Customs voice and safety basics into
> `prompts/prompt.md` (you will expand tools and safety later). Start or update types in
> `models.py` for chat replies and product cards as needed. In `output/harness.md`, note
> how the front end talks to FastAPI and how the agent is loaded (prompt file + model).
> Make sure the backend runs from the `backend/` folder like this:
> `uvicorn main:app --reload --port 8000`.
>
> *(attached: the four agent files: `prompts/prompt.md` system prompt, `agent.py` entry
> and wiring, `tools.py` tools the agent can call, `models.py` Pydantic / PydanticAI
> structured types; `main.py` exposes a chat route so a message from the website returns
> a reply from the agent.)*

*Follow-up:* none needed from me. While testing, the vibe coder found and fixed three
gaps: search counted any-word matches ("82 navy hoodies"), a jailbreak message caused a
502 from the gateway's content filter, and replies repeated the product list the cards
already showed.

---

## Problem 6: Tools for product info and stock

**Prompt**

> Problem 6: tools for product info and stock. Give the agent tools that look up real
> info from `campus_customs.db`: product description, price, and how many are in stock
> (by size when the customer asks). The agent must use the database; it should not invent
> prices or quantities. If a size is out of stock, say so clearly. Expand
> `prompts/prompt.md` so the agent knows to call these tools for price and stock
> questions. Add or update return types in `models.py`. In `output/harness.md`, list each
> tool and explain which model fields you chose for lookup results and why.

*Follow-up:* none needed. In the vibe coder's testing, all 7 price and stock questions
matched the database, including sold-out sizes and a two-item question.

---

## Problem 7: Chat search that updates the page

**Prompt**

> Problem 7: chat search that updates the page. Now we will add a feature to the site.
> When a customer asks about a type of item, for example "what hoodies do you have?", the
> agent should search the catalogue and the website should dynamically show those
> matching items as product cards (image, name, price, short info). This is an API
> contract: the agent returns structured product matches and then the front end renders
> them on the website. After the dynamic product cards are loaded by your new feature,
> make sure the same single-item page behavior you built in Problem 3 still works: each
> product card, including the ones the chat just put on the page, should still open that
> detail view (large image + full info) when clicked. Update `prompts/prompt.md` and
> `output/harness.md` so it is clear how search results reach the page.

*Follow-up:* none needed. In testing, the vibe coder noticed the bot quoted a price range
from only the 8 results it could see ("$45 to $68" when the 27 hoodies go up to $88), so
it added the full-set `min_price`/`max_price` to search results.

---

## Problem 8: Customer memory

**Prompt**

> Problem 8: customer memory. When a shopper is logged in, save their chat history in the
> database in an appropriate table and reload it when they return. The agent should know
> who is chatting (name, email). Put that in agent deps (or an equivalent clear pattern)
> and/or tools the agent can call. Also pass enough page context that if someone is on a
> product page and asks "do you have this in pink?", the agent knows which item they
> mean. You can put code into the agent context. Guests can still chat, but history only
> needs to persist for logged-in users. Document in `output/harness.md`: how user chat
> history is stored, what customer fields the agent sees, and how page context is passed.

*Follow-up:* none needed. The vibe coder reused the existing `chat_messages` table
(keeping the seeded rows readable) and verified memory across a page reload and a
logout/login in a real browser.

---

## Problem 9: Usability improvements

**Prompt**

> Problem 9: usability improvements. Now that the core shop works, improve it. Choose and
> implement 2 front-end usability improvements and 2 agent/backend usability
> improvements. Front-end improvements are things that make the site look better and
> make it easier to use. Agent/backend improvements are things that make the agent's
> output better, more accurate, or safer. These could be new agent tools or things that
> make the agent run faster or cheaper. Write `output/usability.md` before or as you
> build. For each improvement, say what you added and why it helps a Campus Customs
> shopper or the business. Then make sure all improvements actually show up in the
> running app. Graders will read the write-up and look for the features.

*Follow-up:* none needed from me. While testing, the vibe coder found that a shopper's
own number ("it's $55, right?") could slip past the first version of the fact-check, so
it tightened the rule to allow shopper numbers only as budgets ("under $50"). It also
found and fixed a crash on the Products page caused by newer Chrome's `scrollTo`
returning a value inside a React effect.

---

## Problem 10: Style the website

**Prompt**

> Problem 10: style the website. Add creative design so the site feels like a real Campus
> Customs storefront: fonts, color, hierarchy, motion, product presentation, and chat
> feel. Make it really innovative and imaginative, with cute Yale-related colors,
> bulldogs, etc. Write `output/design.md`: what you changed and why it should help
> customers stick around and buy. Keep it concrete and short.

*Follow-up:* none needed from me. The vibe coder redrew the bulldog mascot after its first
version looked more like a teddy bear than a bulldog (rose ears, jowls, underbite), and
fixed the spinning fight-song ring text overlapping itself.

---

## Problem 11: Site testing (app check)

**Prompt**

> Problem 11: site testing (app check). Test the live site and document it in
> `output/app_check.html` (a page you can double-click to open). Include clear screenshots
> and short captions for: the chat checking the inventory level of an item (honest stock
> and price from the DB), the dynamic search result cards appearing after a category
> question (e.g. hoodies), and one of the usability features you added in Problem 9. Make
> the HTML easy to grade: a heading for each check, a screenshot, and one or two
> sentences on what the screenshot proves. Put the screenshot image files in
> `output/app_check_images/` and link them from `app_check.html` with relative paths (for
> example `app_check_images/inventory.png`).

*Follow-up:* none needed. The vibe coder retook two screenshots so they were legible (a
close crop of the chat panel, and the chat scrolled so the shopper's question shows),
and opened the page from `file://` to confirm all six images load.

---

## Problem 12: Audit trail, safety, and finishing the harness

**Prompt**

> Problem 12: audit trail, safety, and finishing the harness. Keep an append-only
> `output/audit_trail.json` of agent loop activity (time, tool name, short args/result,
> stop reason). Do not wipe it between runs. Also, think of some safety rules to give the
> agent and put them in `prompts/prompt.md`. Finish `output/harness.md` so it is clear how
> the system works: the model fields in `models.py` and why you chose them, tools and
> abilities, safety rules, and specs (loop limits, result caps, models, how to run the
> front and back end).

*Follow-up:* none needed from me. While testing the safety rules, the vibe coder found
that a crisis message ("I feel really hopeless…") was blocked by the gateway's content
filter and got a generic refusal, so it added a code-level safety rail with 988 and Yale
Mental Health & Counseling (number verified on Yale Health's site). It also stopped Dan
from telling shoppers to "check out" on a site that has no checkout.
