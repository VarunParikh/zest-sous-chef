# ADR-005: Use embedded Chroma as the vector store; embedder to be measured
- **Status:** Accepted for the store (owner decision, 2026-10-17); Proposed for the embedder (to be measured Day 1)
- **Date:** 2026-10-17
- **Decision owner:** VJP (product owner); drafted by Claude
- **Authorisation:** Owner decided to use a local vector database such as Chroma. The embedder is not decided.

## Context
A local vector store is needed for 35 dish documents now (at least 127 under ADR-004 v2, whose add-on neighbours use the same `zest_dishes` collection; count refresh only, decision unchanged) and at least 1,000 variant documents (5,000 for the scale test) with no separate service, on a 16 GB laptop beside the text model.

## Decision drivers
- Runs inside the Python process
- Persistent local folder
- Built-in local embedder (no API key)
- Simple API for a 3-day build
- Memory and index build time within budget

## Options considered
| Option | Pros | Cons |
|---|---|---|
| Chroma embedded (persistent client) | Python-native, local, default ONNX embedder, Ollama embedder supported (per its documentation) | Version churn; I have not measured its memory here |
| FAISS | Fast, mature | Lower-level: no built-in persistence of metadata or embedders; more code |
| SQLite-based vector extension | Single file with the catalogue | Extension setup on macOS adds risk |
| Qdrant or similar local server | Feature-rich | A separate service to run; against the one-command goal |

## Decision
Use Chroma in embedded, persistent mode. Embedder: start with Chroma's default local ONNX embedder (all-MiniLM-L6-v2, per the Chroma documentation); compare it with an Ollama embedding model on Day 1 and record the choice.

## Rationale
The embedded store removes operations work and fits the one-command setup. Quality of Hindi and Marathi names in particular depends on the embedder, hence the comparison.

## Consequences
- **Positive:** No service to operate; fast to build; Chroma returns IDs and distances that fit the Retriever interface.
- **Negative:** Dependency on Chroma's API stability; embedder quality unknown for regional names until measured.
- **Neutral:** None identified.

## Risks and mitigations
- Memory pressure with the text model (R23): measure on Day 1, lexical fallback
- Version drift: pin versions; store model name and catalogue hash in collection metadata and rebuild on mismatch (NFR-12)

## Implementation and rollout
- `scripts/index.py` builds collections `zest_dishes` and `zest_variants`
- Cosine distance
- Store folder `data/chroma/` is git-ignored

## Validation / rollback
Rollback: lexical-only mode; swapping the store requires only the `Retriever` implementation.

## Evidence to be measured on Day 1
| Measure | Method |
|---|---|
| Index build time and peak memory | 1,000 and 5,000 variants with each embedder |
| Retrieval recall | Same evaluation set as ADR-004, per embedder (default vs Ollama embedder) |
| Regional-name behaviour | Hindi and Marathi query subset |
Results go in `verify/benchmarks/retrieval.md`.

## Related documents
Data Model section 7; PRD NFR-12, 13; Risk R23.
