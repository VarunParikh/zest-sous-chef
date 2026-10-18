# Retrieval explained: the vector database, retrieval (RAG) and the levers

A plain-language explanation of how Zest finds and ranks dishes and products. The formal specifications are the ADRs, the data model and the architecture document; this page explains how they fit together. File paths are in backticks.

**Contents**
1. The vector database: how it was created and how it works
2. Retrieval (RAG): how it was built and how it works
3. The levers: how they work and how they affect retrieval

---

## 1. The vector database: how it was created and how it works

### What a vector database does
An embedding model turns a piece of text into a list of numbers (a vector), so that texts with similar meaning get nearby vectors. To search, the query is turned into a vector, and the database returns the stored items whose vectors are closest. This finds "something cooling" even when no dish contains those words.

### What was chosen
**Chroma**, running inside the Python backend and saving to a local folder (`data/chroma/`). The embedding model is `all-MiniLM-L6-v2`, which runs locally with no API key.

Why: there is no server to run, no key is needed, and it fits the one-command setup. It was benchmarked against `nomic-embed-text` and tied on recall.

### What is stored
Two collections, using cosine distance:

| Collection | One document per | Count |
|---|---|---|
| `zest_dishes` | dish | 130 |
| `zest_variants` | product variant, not SKU (pack sizes would create duplicates) | 1,027 |

### What text is embedded
Each document is turned into a sentence from a fixed template.

- **A dish:** its name, course, cuisine, mood and occasion tags, taste, main ingredients, aliases and a description.
- **A variant:** its name, category, a plain-words attribute phrase ("skimmed, low fat"), its ingredients and its alternative names.
- **Excluded on purpose:** price, stock, pack size, brand, diet flags and allergens. Eligibility is checked in code, never by similarity.

### How it was built
1. A seeded generator produces the catalogue from a taxonomy file, so the data is reproducible.
2. Validators check it (for example, every dish ingredient resolves to a product).
3. `make index` embeds every document and writes the index. The first run downloads the embedding model (about 80 MB). The index records a fingerprint of the catalogue and is rebuilt when the catalogue changes.

### What it costs
The index build took 11 s at 1,000 variants and 54 s at 5,135 variants. Queries take under 15 ms. A bug found during the benchmark, where an interrupted build was treated as current, was fixed.

### If it fails
If the index cannot load, retrieval falls back to keyword-only search and the user sees no error. This is tested in the fault-injection evaluation.

Key files: `docs/epics/zest/design/adr/ADR-005-vector-store-and-embedder.md`, `docs/epics/zest/design/data-model.md` (section 7), `scripts/index.py`.

---

## 2. Retrieval (RAG): how it was built and how it works

### What "RAG" means here
Retrieval-augmented generation usually means: retrieve text, hand it to a model, and let the model write an answer from it. Zest deliberately does less of this.

- **Retrieval returns only IDs** (dish IDs and variant IDs).
- **Code does everything exact:** filtering, scoring and pricing.
- **The model writes one short reason line** from structured facts. It never sees the catalogue, so it cannot invent a price or a SKU.

### The retrieval steps, for a request like "something comforting tonight"
1. **Clean the query:** lowercase, drop filler words, expand synonyms (for example "kothmir" means coriander leaves).
2. **Keyword search (BM25):** the top 20 dishes by word overlap with names, aliases and synonyms.
3. **Vector search:** the top 20 from the dish collection.
4. **Fuse the two lists** with reciprocal rank fusion: each item scores the sum of `1 / (60 + its rank)` across the lists. Items found by both searches rise to the top.
5. **Keep a pool** of 25 dishes (10 variants for ingredient queries).
6. **Guardrails in code** remove anything the persona's diet, faith, allergy or stock rules forbid.
7. **Lever scoring** ranks what is left (see section 3), and the top three are shown.

### Why hybrid
Keyword search is exact but literal. Vector search understands meaning but can drift. In the benchmark, hybrid search found the right dish in all 30 test queries and in all 7 mood queries. Keyword-only found 28 of 30 and 5 of 7.

### Add-ons use the same idea
The suggestions for a dish in the cart come from two lists: curated pairings (weighted 2) and vector neighbours (weighted 1), under a rule that add-ons must be sides, drinks or desserts. No new embedding is computed.

### Two honest points
- The vector part measures similarity of descriptions. It does not know what people buy together, since there is no purchase data.
- Open requests such as "I am hungry" have nothing to search for, so they skip search and rank the whole course by the levers instead.

Key files: `docs/epics/zest/design/adr/ADR-004-retrieval-approach.md`, `docs/epics/zest/design/architecture.md`, `docs/epics/zest/verify/benchmarks/retrieval.md`.

---

## 3. The levers: how they work and how they affect the vector database and retrieval

### The key point
**Levers never touch the vector database.** The index and the embeddings are built once and do not change when a lever moves. Levers act **after** retrieval, on the pool of candidates that retrieval returned. The only exception is open requests, where there is no search and the levers rank the whole course directly.

### Where they act
```
message -> search (BM25 + vectors) -> pool of 25 -> guardrail filters -> lever scoring -> top 3
                                                      ^ hard levers        ^ soft levers
```

### Two kinds of lever

| Kind | Levers | Effect |
|---|---|---|
| **Hard** (filters) | Diet, faith, specialised diets (vegan, gluten-free, keto and others), allergens, stock filter, add-on price cap | Remove candidates from the pool. A removed item is never shown or carted. |
| **Soft** (scores) | Four weights (culinary pairing, purchase history, market trend, persona and gourmet), history sliders per category, two trend sliders, gourmet, organic, a capped gender-cohort boost | Change how the surviving candidates are ordered. |

### Dish ranking
Each surviving dish gets four component scores: pairing, history, trend and gourmet match. They are combined using the four weights. The "effective share" of each is its weight divided by the sum of all four, so the panel can show the real mix. The defaults are 0.30, 0.35, 0.20 and 0.15.

### Choosing the product variant
Once a dish is chosen, each ingredient has several eligible variants. Each is scored by the same levers plus a price term:

`score = (1 - b) x lever score + b x price value`

The price weight `b` is at most 0.20 and shrinks as the gourmet slider rises. A budget user therefore gets the cheaper option, and a gourmet user gets the premium one, with no extra control.

### When the levers apply
The levers are snapshotted when a chat session starts. Changing one shows a banner, and the change applies from the next session (an owner decision). This keeps the comparison between two settings clean.

### How much do they actually move the results?
This was measured in evaluation E6, a "ranking divergence" score where 0.33 means one of the top three dishes changes on average.

- **Hard levers work strongly:** diet 0.40, faith 0.74, specialised diets 0.93, add-on cap 0.73.
- **Most soft levers fall short of the goal:** the four weights score 0.12 to 0.30, the gourmet slider 0.07 at dish level, and the cooling-trend slider 0.05.
- **Soft levers act more visibly on variants:** the gourmet slider changed the chosen variant for all 6 test ingredients, and organic for 5 of 6.

The owner accepted the dish-level result as a known limitation.

Key files: `docs/inputs/RecommendationSettingsPanel.md` (the lever spec), `docs/epics/zest/design/adr/ADR-008-variant-scoring.md`, `docs/epics/zest/design/data-model.md`, `docs/epics/zest/verify/benchmarks/block26.md`.
