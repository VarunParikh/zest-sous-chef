# Product References and Glossary: Zest AI Sous-Chef

Status: DRAFT v0.1 (awaiting owner approval) · Date: 2026-10-16

## 1. How to use this document
Every other document cites sources by the IDs below (for example, [R3]). "Verified" means the source was opened and read in this session. "From knowledge" means it is cited from the author's background knowledge and **must be checked (title, year, DOI) before the interview submission**.

## 2. References

### 2.1 Process and method
| ID | Source | Used for | Status |
|---|---|---|---|
| R1 | Finny, J. *How I'm building an AI-driven SDLC: a product manager's playbook.* Medium. https://medium.com/@joshua_finny/how-im-building-an-ai-driven-sdlc-a-product-manager-s-playbook-30d52b8f9acb | Document-first method; `core/`, `epics/`, `_templates/` structure; constitution as policy and system prompt; human approval gates | Verified (summarised, not quoted) |
| R2 | Finny, J. *From playbook to pipeline: running a feature through an AI-driven SDLC.* Medium. https://medium.com/@joshua_finny/from-playbook-to-pipeline-running-a-feature-through-an-ai-driven-sdlc-65a9f87e338a | Five-stage feature flow: research, business requirements, product spec, spec analysis (stories and traceability), engineering pickup | Verified |

### 2.2 Platforms
| ID | Source | Used for | Status |
|---|---|---|---|
| R3 | Google AI for Developers. *Gemini API pricing.* https://ai.google.dev/gemini-api/docs/pricing | Free-tier models; free-tier content "used to improve our products" | Verified (first part of page only) |
| R4 | `youtube-transcript-api` on PyPI. https://pypi.org/project/youtube-transcript-api/ | Version 1.2.4 (29 Jan 2026); IP-blocking warning | Verified |

### 2.3 Peer-reviewed and standards references (From knowledge: verify before submission)
| ID | Source | Relevance |
|---|---|---|
| R5 | Greshake, K. et al. (2023). *Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection.* AISec '23. arXiv:2302.12173 | Indirect prompt injection (UJ57); principle P4 |
| R6 | Ji, Z. et al. (2023). *Survey of hallucination in natural language generation.* ACM Computing Surveys 55(12). doi:10.1145/3571730 | Hallucinated SKUs and prices (UJ60); principle P3 |
| R7 | Burke, R. (2002). *Hybrid recommender systems: survey and experiments.* User Modeling and User-Adapted Interaction 12(4), 331–370 | Weighted hybrid scoring behind the lever panel |
| R8 | Mitchell, M. et al. (2019). *Model cards for model reporting.* FAT* '19. doi:10.1145/3287560.3287596 | Responsible-AI note and model documentation |
| R9 | Gebru, T. et al. (2021). *Datasheets for datasets.* Communications of the ACM 64(12), 86–92 | Documenting the mock datasets |
| R10 | Inan, H. et al. (2023). *Llama Guard: LLM-based input-output safeguard for human-AI conversations.* arXiv:2312.06674 | Candidate guard classifier (UJ9) |
| R11 | NIST (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0),* NIST AI 100-1 | Risk register and responsible-AI structure |
| R12 | OWASP. *Top 10 for LLM Applications* (LLM01 prompt injection and related items) | Security and Privacy note |
| R13 | Government of India. *Digital Personal Data Protection Act, 2023* | Photo and personal-data handling (relevant to the P9 decision) |

### 2.4 Project documents
| ID | Document | Role |
|---|---|---|
| D1 | `docs/core/product-vision.md` | Owner's brief |
| D2 | `RecommendationSettingsPanel.md` | Lever names, defaults, ranges |
| D3 | `DESIGN.md` and mockup images (`Mobile_UI.png`, `WebUI.png`) | Look and feel |
| D4 | `UserJourneys.md` | 87 journeys (MVP subset in Strategy) |
| D5 | `docs/core/open-conflicts.md` | Conflict log |

## 3. How this project maps to the playbook [R1, R2]
| Playbook element | Zest equivalent | Note |
|---|---|---|
| Constitution first | `constitution.md` | Principles, guardrails, AI authority matrix |
| Overview, strategy, timeline, platforms, references | `product-strategy.md`, `product-platforms.md`, this file | The vision doubles as the overview; the delivery plan sits in Strategy section 8 |
| `CLAUDE.md` | `CLAUDE.md` | Our addition; the playbook articles do not describe one |
| Feature folder: research, BRD, spec, design, prototyping feedback | Documents 6, 9, 10, 12 to 17, 24 | We treat Zest as one epic |
| Spec analysis: stories and traceability | Document 11 | |
| `_templates/` | To be decided | Optional |

## 4. Glossary

### 4.1 Product terms
| Term | Meaning |
|---|---|
| **Zest** | The AI sous-chef chatbot |
| **Quick commerce (q-commerce)** | Grocery delivery in about 10 to 30 minutes from nearby warehouses |
| **Dark store** | A small local warehouse that serves quick-commerce orders |
| **SKU** | A specific purchasable catalogue item with its own pack size and price |
| **Catalogue** | The mock list of SKUs, prices and stock (the only source of commerce facts) |
| **Dish** | A recipe in the cart; its cost is the sum of its active ingredient lines |
| **Cart line** | One ingredient SKU attached to one dish |
| **Active / inactive line** | When two dishes need the same SKU, the first owns the active (priced) line and the second is dimmed and unpriced; removing the first transfers ownership |
| **Pantry delta** | Ingredients a recipe needs minus ingredients the user already has |
| **Entry method** | How a user starts: YouTube link, text recipe, mood or intent, or photo |
| **Session** | One chat from start to clear or reset; levers apply at session start |
| **Upsell / pairing suggestion** | An optional add-on the bot suggests but never adds by itself |

### 4.2 Recommendation engine terms
| Term | Meaning |
|---|---|
| **Lever** | A control in the left-hand panel |
| **Persona** | The set of hard-constraint settings (gender, diet, faith, specialised diet) |
| **Hard guardrail / eligibility mask (M_elig)** | A zero-tolerance 0/1 filter; a violating item scores 0 and is never offered |
| **Soft weight** | A slider that scales a part of the score (w_p, w_h, w_t, w_g) |
| **S_final** | The final score of a candidate item, combining the four weighted components after the eligibility mask |
| **Culinary pairing (w_p)** | How strongly an item co-occurs with the main dish (for example, Biryani and Raita) |
| **Purchase history (w_h)** | Simulated historical affinity per category (the history sliders) |
| **Market trend / velocity (w_t)** | Time, weather and festive demand multipliers |
| **Persona and gourmet boost (w_g)** | Cohort affinity and gourmet or artisanal preference |
| **Satvik / Jain / Shravan** | Indian dietary and fasting traditions that exclude onion, garlic or root vegetables (Jain and Satvik), or non-satvik foods during the Shravan month |
| **Halal** | Meat prepared according to Islamic law |
| **Keto / Low-GI** | Low-carb, high-fat diet / glycaemic-index-aware diet |

### 4.3 AI and engineering terms
| Term | Meaning |
|---|---|
| **LLM / VLM** | Large language model / vision-language model |
| **Ollama** | A tool that runs open models locally |
| **Catalogue grounding** | Taking SKUs and prices only from the catalogue, never from model output |
| **Hallucination** | A model stating something unsupported, such as an invented SKU or price |
| **Prompt injection (direct / indirect)** | Instructions placed in user input (direct) or in content the bot reads, such as a transcript (indirect) |
| **Guard classifier** | A separate check that screens input for off-topic, hostile or hazardous requests |
| **Schema-validated output** | Model output parsed against a fixed structure; invalid output is retried once, then handled by a fallback |
| **Fixture** | A saved sample (for example, a transcript) used so a demo does not depend on a live service |
| **EXIF** | Metadata in photos, including GPS location; stripped on upload |
| **Idempotency key** | A token that makes repeated identical requests create only one order |
| **Bandit** | A learning approach that balances trying new suggestions against repeating known ones |
| **ADR** | Architecture Decision Record |
| **BRD / PRD** | Business Requirements Document / Product Requirements Document (spec) |
| **UJ# / B#** | A user journey from `UserJourneys.md` / a brief-defined capability |
| **Must / Should / Could / Deferred** | Scope tiers (see Strategy section 6.2) |
