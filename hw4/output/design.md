# Design: "Varsity shop" restyle

**Goal:** the site should feel like walking into a cheerful Yale shop on Broadway, not a
template. Shoppers should notice what's in stock in their size and ask Dan the bulldog
for help.

Screenshots: `app_check_images/design_home.png`, `design_product_page.png`,
`design_chat.png`, `design_signup.png`, `design_mobile.png`.

## What changed, and why it helps people stay and buy

| Area | What I changed | Why it helps |
|---|---|---|
| **Color** | Yale navy `#00356b` on warm ivory "pennant paper" `#fbf7ef`, with sky blue `#bcd4f0`, a gold accent `#f2c94c` for calls to action and price tags, blush pink on the mascot, and crimson used only for urgency ("Few sizes left", "Going fast"). A faint paw-print wallpaper sits behind every page. | It reads instantly as Yale, but warmer and friendlier than plain white. Gold is reserved for "buy" actions, so the eye goes to Shop and prices. Crimson only means "act soon". |
| **Fonts** | **Fraunces** (soft serif) for headings, with italic sky-blue accent words ("worn *every day*", "Shop by *category*"). **Graduate** (varsity block letters) for the brand, prices, sizes, ticker, and chat name. **Nunito Sans** for body text. | The type looks like a letterman jacket and a college press, so the store feels like the real campus brand. Prices in varsity letters stand out without shouting. |
| **Mascot** | **Dan**, a hand-drawn SVG bulldog (`Bulldog.tsx`) with rose ears, jowls, an underbite, blush, and a collar with a Y tag. He has 3 moods: happy, wink, and sleepy. He appears in the nav logo, the favicon, the hero, the chat launcher, the chat avatar, every reply bubble, the product page, sign-up, the footer, and the 404 page. | One friendly character ties the shop and the chatbot together. A cute face on the chat button makes asking for help feel low-pressure, which is where sales questions (size, color) get answered. |
| **Hierarchy** | Hero: a big "Bulldog pride, *worn every day.*", then a gold **Shop the collection** button and an outline **Ask Dan for help** button. Sections go categories → favorites → trust strip (licensed / 57 Broadway / 30-day returns). Product pages add breadcrumbs. | One obvious primary action per screen. Trust facts sit just above the footer, where hesitant shoppers look before leaving. |
| **Motion** | Pennants flutter along the top of the hero. The "Bulldog! Bulldog! Bow wow wow!" ring rotates slowly around a bobbing Dan. A gold cheer ticker scrolls under the hero. Cards rise in with a slight stagger and lift on hover while the photo zooms. Buttons have a pressable "3D" edge. The chat panel pops open, the launcher dog wiggles, and typing shows **walking paw prints** ("Dan is sniffing around…"). All motion is turned off for `prefers-reduced-motion`. | Small motion makes the site feel alive and rewards exploring. The paw-print typing indicator makes the AI's wait feel playful instead of slow. Reduced-motion support keeps it comfortable for everyone. |
| **Product presentation** | Cards: a gold **pennant price tag** on the photo, the garment type, 2 lines of description, and **size dots XS–XXL**, with sold-out sizes struck through and a crimson "Few sizes left" badge when 3 or fewer sizes remain. Category tiles show a real product photo in a circle plus a style count ("Hoodies · 27 styles"). | Shoppers see price and *their size's* availability before clicking, so fewer dead ends. The badge creates honest urgency from real stock. Photo tiles make browsing visual. |
| **Product page** | The photo sits in a navy frame with an offset sky shadow and a rotated gold **"Officially licensed" sticker**. Colors show as **real swatches** ("Navy Blue" gets a navy dot). Stock is shown as **size tiles**: green "In stock", amber "Only 5 left", and dashed/struck "Sold out". A crimson **"Going fast: only 2 left in XL"** line appears when sizes run low. An "Ask about this item" card features winking Dan. | Every buying question (price, color, my size, how many left) is answered at a glance. The sticker builds trust. The urgency line and the help card push hesitant shoppers toward checkout or the chat. |
| **Chat feel** | Header: Dan's avatar with a green **online dot** and "Dan · Campus Customs". Bubbles: ivory chat background, white assistant bubbles with a sky border and a mini Dan, navy shopper bubbles. Rounded product cards slide on hover. Greetings and the prompt give Dan a light personality ("Woof! I'm Dan, the Campus Customs shop pup…"), and the backend prompt keeps answers first and puns rare. | It feels like texting a friendly shop employee, not a form. Consistent persona plus accurate answers builds trust, and trust is what turns chat into purchases. |
| **Small moments** | The 404 page and missing products show a sleepy Dan ("Ruh-roh, page not found") with a button home. Sign-up becomes **"Join the pack"**. The footer has a scalloped pennant edge, Dan winking, and the fight-song line. | Dead ends become on-brand and point shoppers back to shopping. A playful sign-up headline makes creating an account feel like joining the community. |

## Kept working

Mobile layout: the hero stacks, the badge shrinks, and size tiles drop to 3 per row. Every
Problem 3–9 feature was re-tested in Chrome after the restyle: chat search on the page, card
→ product page, chips, sort and filter, and similar items. The restyle also surfaced one
bug, which is now fixed: quickly changing size and then sort could drop the size filter.
