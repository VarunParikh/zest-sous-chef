# Personas: Zest AI Sous-Chef

Status: DRAFT v0.1 (awaiting owner approval) · Date: 2026-10-16
All personas are **fictional** and built to exercise the guardrails and levers, not to represent real people. Each maps to a concrete lever configuration in `mock-data/personas.json`, so the same file drives demos and automated tests.

## 1. Design rules
- Together they cover every option in the Persona and Specialised Diet dropdowns.
- Each has a "trap": a plausible request that the bot must handle correctly.
- Lever values not listed use the Settings Panel defaults (weights 0.30 / 0.35 / 0.20 / 0.15; gourmet 0.50; organic 0.60; history sliders 0.85 / 0.70 / 0.65 / 0.60 / 0.75; weekend 0.80; cooling 0.65; price cap ₹200; stock filter on).

## 2. Persona summary

| ID | Name | Diet | Faith / culture | Specialised diet | Main entry method | Core test |
|---|---|---|---|---|---|---|
| P1 | Meera Shah | Jain | Jain (Strict Root-Free) | Standard | Text | Root-vegetable and garlic blocking |
| P2 | Rohan Deshmukh | Pure Veg (Strict) | Hindu (Regular) | Standard | YouTube | Non-veg request intercept |
| P3 | Imran Qureshi | Non-Veg / Flexitarian | Muslim (Strict Halal Only) | Standard | Text and photo | Halal-only meat and pairing upsell |
| P4 | Ananya Iyer | Pure Veg (Strict) | Hindu (Shravan / Fasting Active) | Standard | Mood and text | Seasonal restriction |
| P5 | Karan Malhotra | Non-Veg / Flexitarian | None / Secular | Keto Diet + High-Protein | YouTube and photo | High-carb staples masked |
| P6 | Priya Nair | Pure Veg (Strict) | None / Secular | Vegan + Gluten-Free (multi-select) | Photo and text | Stacked hard masks |
| P7 | Alex (Reviewer) | any | any | any | Any | Lever causality demonstration |

## 3. Persona details

### P1. Meera Shah, 58, retired teacher, Mulund (Jain)
- **Goal:** cook everyday and festival meals within strict Jain rules without checking every label.
- **Behaviour:** types dish names, often in mixed Gujarati-English words; shops weekly in larger baskets.
- **Levers:** Gender Female · Diet Jain · Faith Jain (Strict Root-Free) · Dairy 0.85 · Desserts 0.80 · Kebabs 0.05.
- **Trap:** "I want to make Garlic Bread" or "kandha and batata" (UJ7, UJ23, UJ29-lite, UJ73).
- **Success:** no onion, garlic or root vegetable ever reaches the cart or an upsell; a Jain-friendly alternative is offered.

### P2. Rohan Deshmukh, 27, software engineer, Pune (Pure Veg)
- **Goal:** turn cooking videos into a ready cart after work.
- **Behaviour:** pastes YouTube links, sometimes several in a row; quick, terse messages.
- **Levers:** Gender Male · Diet Pure Veg (Strict) · Faith Hindu (Regular) · Bakery 0.90 · Cooling Drinks 0.80.
- **Trap:** pastes a Chicken Tikka Masala video, or a recipe with hidden animal ingredients such as Worcestershire sauce (UJ21, UJ28).
- **Success:** the bot flags the mismatch, offers a veg swap, and asks before changing anything.

### P3. Imran Qureshi, 41, small-business owner, Mumbai (Non-Veg, Halal)
- **Goal:** cook for family gatherings and use up fridge items.
- **Behaviour:** uploads fridge photos; plans biryani and kebabs.
- **Levers:** Gender Male · Diet Non-Veg / Flexitarian · Faith Muslim (Strict Halal Only) · Kebabs 0.90 · Dairy 0.80 · Weekend Indulgence 0.90.
- **Trap:** a recipe with non-halal meat or alcohol-containing ingredients (UJ59 in spirit).
- **Success:** only halal-tagged meat SKUs; after a biryani cart the bot suggests raita but does not add it (UJ11, UJ12).

### P4. Ananya Iyer, 34, product manager, Bengaluru (Pure Veg, Shravan)
- **Goal:** find fasting-friendly meals during the Shravan month.
- **Behaviour:** vague mood requests ("something light and simple").
- **Levers:** Gender Female · Diet Pure Veg (Strict) · Faith Hindu (Shravan Month / Fasting Active) · Salads 0.80 · Cooling Drinks 0.75.
- **Trap:** asks for a dish containing non-satvik ingredients (onion, garlic).
- **Success:** the bot suggests permitted dishes and explains each removal (UJ6).

### P5. Karan Malhotra, 30, fitness coach, Mumbai (Keto, high protein)
- **Goal:** low-carb, high-protein meals.
- **Behaviour:** watches video recipes and photographs his fridge.
- **Levers:** Gender Male · Diet Non-Veg / Flexitarian · Faith None / Secular · Specialised Keto Diet + High-Protein Fitness · Bakery 0.10 · Kebabs 0.95 · Gourmet 0.60.
- **Trap:** "I want to make Dal Chawal" or a pasta recipe (high-carb staples).
- **Success:** the bot flags the conflict, proposes low-carb swaps, and does not silently add rice or pasta.

### P6. Priya Nair, 24, graduate student, Chennai (Vegan, Gluten-Free)
- **Goal:** meals that are both vegan and gluten-free on a student budget.
- **Behaviour:** photo-led, low price cap, multi-message edits.
- **Levers:** Gender Female · Diet Pure Veg (Strict) · Faith None / Secular · Specialised Vegan + Gluten-Free · Price cap ₹120 · Gourmet 0.20 · Organic 0.70.
- **Trap:** a mushroom risotto flow that asks for regular arborio, butter and parmesan (UJ27 style).
- **Success:** dairy and wheat are blocked together; gluten-free substitutes are offered; the cap holds.

### P7. Alex, 35, interviewer and reviewer (secondary user)
- **Goal:** see that moving a lever changes what the bot suggests.
- **Behaviour:** changes one lever, starts a new chat, repeats the same prompt, and compares.
- **Levers:** any; always sets them before a new session (C4).
- **Trap:** changes a lever mid-chat and expects it to apply immediately. The UI must say it applies from the next session.
- **Success:** the before and after suggestions differ visibly and the score breakdown explains why.

## 4. Coverage matrix

| Need | Covered by |
|---|---|
| Every Diet option | P1 Jain, P2 and P4 and P6 Pure Veg, P3 and P5 Non-Veg |
| Every Faith option | P1, P2, P3, P4, P5 (Hindu Regular, Jain, Muslim, Shravan, Secular) |
| Specialised diets | P5 Keto and High-Protein, P6 Vegan and Gluten-Free (Intermittent Fasting / Low-GI not covered; add if wanted) |
| Gender lever | P1, P4, P6 Female; P2, P3, P5 Male; Unisex / Neutral to be added to the test set |
| Entry methods | P2 YouTube, P3 and P6 photo, P4 mood, P1 text |
| Price cap | P6 low cap; others default |

## 5. Anti-goals
No persona represents a real individual, and none is inferred from user behaviour. Persona fields are set by the user in the lever panel and never guessed by the bot.

## 6. Sources
Persona structure follows common practice; Indian dietary rules (Jain, Shravan, halal) are described in the glossary in `docs/core/references-and-glossary.md`. The market research file will refine goals and behaviours once it is attached.
