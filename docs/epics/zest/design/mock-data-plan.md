# Mock Data Plan: Zest AI Sous-Chef

Status: DRAFT v0.1 (awaiting owner approval) · Date: 2026-10-17
The full field-level schema belongs in the Data Model document (document 16). This plan fixes **when** the data is built, **how**, and **what** it contains.

## 1. When
Mock data is built **in parallel with the remaining documents, but after the PRD and Data Model are drafted and before the build starts**.

| Step | Order | Why |
|---|---|---|
| 1 | Requirements (BRD, PRD, stories) | The journeys decide what data must exist (for example, Jain exclusions need diet tags; stock-outs need scriptable stock) |
| 2 | **Data Model** (document 16, brought forward) | The schema must exist before data can be generated or validated |
| 3 | **Generate and validate the mock data** | The Day-1 model benchmark, the engine and the tests all need it |
| 4 | Remaining design documents (conversation, architecture, API, agent, security) | They can reference real files and field names |
| 5 | Build | Starts from validated data |

## 2. How (automated and re-runnable)
1. **Schema first:** Pydantic models, with the same fields documented in the Data Model.
2. **Curated seed:** the dish list and the SKU list are written as CSV or JSON by hand and by Claude, then reviewed by the owner.
3. **Generator script (`mock-data/build.py`):** derives computed fields (pack-size variants, prices within ranges, tags) with a fixed random seed so results are reproducible.
4. **Validators (`mock-data/validate.py`)** fail the build on any of:
   - a diet tag that contradicts the ingredient (for example a "Jain" tag on a root vegetable);
   - a missing allergen or halal field;
   - a dish ingredient with no SKU and no deliberate gap flag;
   - a price outside the category range;
   - an inconsistent stock state.
5. **Coverage report:** every Must journey and every persona can find at least one valid dish and SKU (assumption A4).
6. **Fixtures for tests:** the same files feed the unit tests, the benchmarks and the evaluation sets.

## 3. What is in it

| Dataset | Content | Target size |
|---|---|---|
| Catalogue (SKUs) | id, name, category, variant attributes (fat level, grain, fortification, organic, spice level), ingredient list, brand (generic), pack size, price in ₹, diet tags, allergens, halal flag, glycaemic label (simplified), gourmet and organic scores, stock count, embedding text | **At least 1,000 shipped; a generated 5,000-SKU set for the scale benchmark** |
| Dishes and recipes | name, cuisine, servings, steps summary, ingredient lines (name, quantity, unit), scaling rules, diet compatibility | About 34 (Indian food and beverages plus 2 edge-case dishes) |
| Ingredient synonyms | Marathi, Hindi and common names to catalogue terms (kothmir, kandha, batata, dhaniya, methi) | About 60 |
| Retrieval evaluation set | About 60 queries with expected IDs: ingredient names, regional names, mood phrases, variant requests ("skimmed milk") | 60 |
| Pairings | main dish to companion item with co-occurrence strength | About 60 |
| Trends | time-of-week and weather multipliers per category | About 20 rows |
| Personas | done: `mock-data/personas.json` (11) | 11 |
| Transcript fixtures | saved transcripts for the demo videos | 3 to 4 |
| Default sample photos | fridge and pantry photos with pre-computed expected detections (fallback when live photo analysis fails; labelled as samples) | About 6 |
| Stock scenarios | scripted stock-outs for UJ10 and UJ22 | 3 scenarios |

## 3a. How 1,000 unique SKUs are generated (owner decision, 2026-10-17)
A unique SKU is a distinct product defined by its **ingredient list and variant attributes**, then brand and pack size. Examples: Bread splits into White, Brown, Wheat, Whole Wheat and High-Protein; Milk into Skimmed, Toned, Full Fat and Lactose-Free.
1. **Taxonomy file (curated):** about 250 base products across the categories, each with allowed variant attributes and a rule for the ingredient list (a template per attribute).
2. **Generator:** expands base products by variant, generic brand and pack size with a fixed seed, writing the ingredient list, tags, price within the category range and embedding text. The same taxonomy generates a 5,000-SKU set for the scale test.
3. **Tag integrity:** diet, allergen and halal tags are computed from the ingredient list by rules, not typed by hand. Validators fail the build when a tag contradicts the list (risk R22).
4. **Audit:** a random 10% of shipped SKUs (about 100 rows) is reviewed by the owner; the 5,000 set is checked by validators only.
5. **Dish coverage:** every dish ingredient must resolve to at least one SKU, and several variants where the levers should choose among them (milk, bread, rice, oil, paneer, flour).
6. **Images:** category icons for SKUs (no 1,000 thumbnails); real images only for demo dishes. This closes OQ-7 for SKUs.

## 4. Dish list (Indian food and beverages, per owner direction 2026-10-17)

**Mains and sides (about 18):** Paneer Butter Masala, Kadai Paneer, Shahi Paneer, Palak Paneer, Dal Tadka with Jeera Rice, Dal Makhani, Rajma Chawal, Chole, Chicken Biryani, Veg Biryani, Butter Chicken, Chicken Tikka Masala, Veg Tikka Masala, Egg Curry, Goan Fish Curry, Moong Dal Khichdi, Garlic Butter Naan, Pav Bhaji (with a Jain variant).
**Snacks and breakfast (about 6):** Paneer Tikka, Chicken Seekh Kebab, Sprout Salad, Poha, Masala Dosa, Sabudana Khichdi (fasting-friendly).
**Desserts (about 4):** Gulab Jamun, Gajar Halwa, Kheer, Sabudana Kheer.
**Beverages (about 6):** Masala Chai, Sweet Lassi, Chaas (spiced buttermilk), Jaljeera, Nimbu Pani, Thandai.
**Companions:** Boondi Raita, Jeera Rice, Roti (used for suggestions).

**Two clearly marked international edge-case dishes (recommended, owner may veto):** Sushi (needed by UJ10, where exotic ingredients are unavailable) and Creamy Pasta (needed by the gourmet lever and persona P10, where imported items such as parmesan and truffle oil must be steerable). Without them, the "unavailable ingredient" and "gourmet" levers have nothing to act on.

**Proposed demo set (to confirm):** Paneer Butter Masala (YouTube; matches the mockup), Garlic Butter Naan (shared-butter deduplication), Chicken Biryani with Boondi Raita (non-veg, halal persona, suggest-only pairing), Gajar Halwa (second link, dessert), plus one beverage prompt (for example "something cooling", leading to Sweet Lassi or Chaas) and a photo of paneer and capsicum leading to Kadai Paneer.

## 5. Principles and cautions
- **Clearly mock:** the UI and README say all commerce data is synthetic (Constitution P8).
- **Generic brand names** by default, to avoid implying real brand prices. Owner to confirm (open question).
- **Transcript fixtures:** because the repo is public, write our own recipe narrations in the style of the demo videos rather than redistributing a creator's captions. The live-fetch path can still be shown with a real link.
- **Images:** SKUs use category icons. Dish images and the sample photos for the photo flow still need licensed or self-made images; this remains a gap to resolve before the build.
- **Dietary labels are simplified.** They are for demonstration and not certified or medical.
- Datasheet-style documentation for each dataset (Gebru et al. 2021, [R9]).
