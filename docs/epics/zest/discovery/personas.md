# Personas: Zest AI Sous-Chef

Status: APPROVED v0.2 (owner, 2026-10-23): the eight personas shown in Zest 2.0 set their own four weights and a few more levers (C84). v0.1 was APPROVED (owner, 2026-10-17) · Date: 2026-10-16
All personas are **fictional** and built to exercise the guardrails and levers, not to represent real people. Each maps to a concrete lever configuration in `mock-data/personas.json`, so the same file drives demos and automated tests.

## 1. Design rules
- Together they cover every option in the Persona and Specialised Diet dropdowns.
- Each has a "trap": a plausible request that the bot must handle correctly.
- Each persona shown in the app (all but P7, P9 and P11) sets its own four weights (Pairing / History / Trend / Persona & Gourmet), listed first on its Levers line (C84, owner 2026-10-23). P9 stays the all-defaults control.
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
| P8 | Lakshmi Pillai | Pure Veg (Strict) | Hindu (Regular) | Intermittent Fasting / Low-GI | Text | High-glycaemic items flagged |
| P9 | Jordan Fernandes | Non-Veg / Flexitarian (default) | None / Secular | Standard / Balanced | Mood and text | Baseline control, Unisex / Neutral |
| P10 | Rahul Verma | Non-Veg / Flexitarian | None / Secular | Standard / Balanced | Text | Cost-effective only; no gourmet items |
| P11 | Vikram Rao | Non-Veg / Flexitarian | None / Secular | High-Protein Fitness | Mood and text | Protein-first suggestions |

## 3. Persona details

### P1. Meera Shah, 58, retired teacher, Mulund (Jain)
- **Goal:** cook everyday and festival meals within strict Jain rules without checking every label.
- **Behaviour:** types dish names, often in mixed Gujarati-English words; shops weekly in larger baskets.
- **Levers:** Gender Female · Diet Jain · Faith Jain (Strict Root-Free) · Dairy 0.85 · Desserts 0.80 · Kebabs 0.05 · Weights 0.30 / 0.45 / 0.10 / 0.15 · Weekend 0.85 · Gourmet 0.30.
- **Trap:** "I want to make Garlic Bread" or "kandha and batata" (UJ7, UJ23, UJ29-lite, UJ73).
- **Success:** no onion, garlic or root vegetable ever reaches the cart or an upsell; a Jain-friendly alternative is offered.

### P2. Rohan Deshmukh, 27, software engineer, Pune (Pure Veg)
- **Goal:** turn cooking videos into a ready cart after work.
- **Behaviour:** pastes YouTube links, sometimes several in a row; quick, terse messages.
- **Levers:** Gender Male · Diet Pure Veg (Strict) · Faith Hindu (Regular) · Bakery 0.90 · Cooling Drinks 0.80 · Weights 0.40 / 0.20 / 0.30 / 0.10 · Gourmet 0.40 · Weekend 0.60.
- **Trap:** pastes a Chicken Tikka Masala video, or a recipe with hidden animal ingredients such as Worcestershire sauce (UJ21, UJ28).
- **Success:** the bot flags the mismatch, offers a veg swap, and asks before changing anything.

### P3. Imran Qureshi, 41, small-business owner, Mumbai (Non-Veg, Halal)
- **Goal:** cook for family gatherings and use up fridge items.
- **Behaviour:** uploads fridge photos; plans biryani and kebabs.
- **Levers:** Gender Male · Diet Non-Veg / Flexitarian · Faith Muslim (Strict Halal Only) · Kebabs 0.90 · Dairy 0.80 · Weekend Indulgence 0.90 · Weights 0.40 / 0.30 / 0.15 / 0.15 · Price cap ₹250.
- **Trap:** a recipe with non-halal meat or alcohol-containing ingredients (UJ59 in spirit).
- **Success:** only halal-tagged meat SKUs; after a biryani cart the bot suggests raita but does not add it (UJ11, UJ12).

### P4. Ananya Iyer, 34, product manager, Bengaluru (Pure Veg, Shravan)
- **Goal:** find fasting-friendly meals during the Shravan month.
- **Behaviour:** vague mood requests ("something light and simple").
- **Levers:** Gender Female · Diet Pure Veg (Strict) · Faith Hindu (Shravan Month / Fasting Active) · Salads 0.80 · Cooling Drinks 0.75 · Weights 0.35 / 0.25 / 0.25 / 0.15 · Organic 0.70 · Gourmet 0.40 · Weekend 0.40.
- **Trap:** asks for a dish containing non-satvik ingredients (onion, garlic).
- **Success:** the bot suggests permitted dishes and explains each removal (UJ6).

### P5. Karan Malhotra, 30, fitness coach, Mumbai (Keto, high protein)
- **Goal:** low-carb, high-protein meals.
- **Behaviour:** watches video recipes and photographs his fridge.
- **Levers:** Gender Male · Diet Non-Veg / Flexitarian · Faith None / Secular · Specialised Keto Diet + High-Protein Fitness · Bakery 0.10 · Kebabs 0.95 · Gourmet 0.60 · Weights 0.30 / 0.25 / 0.15 / 0.30 · Organic 0.70.
- **Trap:** "I want to make Dal Chawal" or a pasta recipe (high-carb staples).
- **Success:** the bot flags the conflict, proposes low-carb swaps, and does not silently add rice or pasta.

### P6. Priya Nair, 24, graduate student, Chennai (Vegan, Gluten-Free)
- **Goal:** meals that are both vegan and gluten-free on a student budget.
- **Behaviour:** photo-led, low price cap, multi-message edits.
- **Levers:** Gender Female · Diet Pure Veg (Strict) · Faith None / Secular · Specialised Vegan + Gluten-Free · Price cap ₹120 · Gourmet 0.20 · Organic 0.70 · Weights 0.35 / 0.30 / 0.25 / 0.10 · Weekend 0.50.
- **Trap:** a mushroom risotto flow that asks for regular arborio, butter and parmesan (UJ27 style).
- **Success:** dairy and wheat are blocked together; gluten-free substitutes are offered; the cap holds.

### P7. Alex, 35, interviewer and reviewer (secondary user)
- **Goal:** see that moving a lever changes what the bot suggests.
- **Behaviour:** changes one lever, starts a new chat, repeats the same prompt, and compares.
- **Levers:** any; always sets them before a new session (C4).
- **Trap:** changes a lever mid-chat and expects it to apply immediately. The UI must say it applies from the next session.
- **Success:** the before and after suggestions differ visibly and the score breakdown explains why.

### P8. Lakshmi Pillai, 52, bank manager, Kochi (Low-GI)
- **Goal:** meals that keep blood-sugar spikes low, with simple recipes.
- **Behaviour:** types dish names; reads the bot's explanations carefully.
- **Levers:** Gender Female · Diet Pure Veg (Strict) · Faith Hindu (Regular) · Specialised Intermittent Fasting / Low-GI · Desserts 0.15 · Salads 0.80 · Weights 0.30 / 0.45 / 0.10 / 0.15 · Gourmet 0.30 · Organic 0.65 · Weekend 0.40.
- **Trap:** "Make gulab jamun and white rice."
- **Success:** the bot flags high-glycaemic items and offers lower-GI swaps. The glycaemic tags in the mock catalogue are our own simplified labels, and the bot never presents them as medical advice.

### P9. Jordan Fernandes, 29, designer, Mumbai (Unisex / Neutral, baseline)
- **Goal:** inspiration for easy dinners; no strong preferences.
- **Behaviour:** vague mood prompts such as "I am feeling indulgent."
- **Levers:** Gender Unisex / Neutral · everything else at defaults.
- **Role:** the **control persona**. Lever-causality tests compare every other persona's suggestions against Jordan's for the same prompt.
- **Success:** a sensible mixed set of suggestions with no demographic skew.

### P10. Rahul Verma, 20, engineering student, Nagpur (cost-conscious)
- **Goal:** cheap, filling meals on a tight allowance.
- **Behaviour:** short text messages; accepts only mass-market products; abandons the cart if it feels expensive.
- **Levers:** Gender Male · Diet Non-Veg / Flexitarian · Faith None / Secular · Price cap ₹80 (the minimum) · Gourmet 0.00 · Organic 0.10 · Weights 0.30 / 0.35 / 0.30 / 0.05 · Weekend 0.60 · Cooling 0.50.
- **Trap:** a pasta request whose default recipe includes imported parmesan and truffle oil.
- **Success:** no gourmet or imported item is suggested; every pairing suggestion costs ₹80 or less; the bot explains trade-offs plainly.
- **Gap noted:** the Settings Panel has an add-on price cap but no whole-cart budget lever. The "keep the cart under ₹350" journey (UJ17) stays in the Could tier.

### P11. Vikram Rao, 26, gym enthusiast, Hyderabad (high protein)
- **Goal:** protein-forward meals at every opportunity.
- **Behaviour:** short mood or goal prompts; likes quick grill-and-eat dishes.
- **Levers:** Gender Male · Diet Non-Veg / Flexitarian · Faith None / Secular · Specialised High-Protein Fitness (no Keto) · Kebabs 1.00 · Dairy 0.90 · Bakery 0.15 · Desserts 0.15.
- **Trap:** "I am feeling indulgent." The bot should lead with protein-rich indulgent options, not desserts, so the same prompt gives a different answer than for Jordan (P9).
- **Success:** protein-rich items rank first; the suggestions differ clearly from Jordan's.

## 4. Coverage matrix

| Need | Covered by |
|---|---|
| Every Diet option | P1 Jain, P2 and P4 and P6 Pure Veg, P3 and P5 Non-Veg |
| Every Faith option | P1, P2, P3, P4, P5 (Hindu Regular, Jain, Muslim, Shravan, Secular) |
| Specialised diets (all six) | Standard: P9 · Keto: P5 · Intermittent Fasting / Low-GI: P8 · Vegan and Gluten-Free: P6 · High-Protein Fitness: P5, P11 |
| Gender lever (all three) | Female: P1, P4, P6, P8 · Male: P2, P3, P5, P10, P11 · Unisex / Neutral: P9 |
| Entry methods | P2 YouTube, P3 and P6 photo, P4 and P9 and P11 mood, P1 and P8 and P10 text |
| Price cap and gourmet levers | P10 (₹80 cap, gourmet 0), P6 (₹120 cap) |
| Control for lever causality | P9 (all defaults) |

## 5. Anti-goals
No persona represents a real individual, and none is inferred from user behaviour. Persona fields are set by the user in the lever panel and never guessed by the bot.

## 6. Sources
Persona structure follows common practice; Indian dietary rules (Jain, Shravan, halal) are described in the glossary in `docs/core/references-and-glossary.md`. The market research file will refine goals and behaviours once it is attached.
