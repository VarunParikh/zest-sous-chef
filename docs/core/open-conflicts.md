# Open Conflicts Log

Format: ID · conflict · sources · proposed resolution · status. Precedence: Vision > Constitution > Settings Panel > DESIGN.md > User Journeys.

| ID | Conflict | Sources | Proposed resolution | Status |
|---|---|---|---|---|
| C1 | Order-placed window lasts **3 s** vs **10 s with a progress bar** | DESIGN.md vs Vision | Follow Vision: 10 s with progress bar | Proposed |
| C2 | Cart opens via a **"View Cart" chat link** vs a **cart icon top-right of the chat window** (with badge, greyed when empty) | DESIGN.md flows vs Vision | Follow Vision (icon + badge + disabled when empty); the chat link may remain as a shortcut | Proposed |
| C3 | Dietary dropdown has **3 options** vs journeys UJ29 name **5** (Jain, Pure Veg, Eggless, Vegan, Satvik) | Settings Panel vs User Journeys | Keep 3 options in the dropdown; Vegan is covered by Specialized Diet Mode; Eggless and Satvik deferred | Proposed |
| C4 | Levers apply **"before starting a new session"** vs DESIGN.md "immediately update" | Vision vs DESIGN.md Principle 1 | Follow Vision: changes take effect on the next chat session; confirm with owner whether live mid-chat updates are also wanted | **Resolved 2026-10-16:** owner confirmed next-session-only, since chat clear and engine reset are independent of the lever panel |
| C5 | Vision says "JioMart-like" and **no real data**; Journeys mention **real-time stock, dark-store and rider APIs** | Vision vs UJ22, 63, 67, 71 | All simulated by a mock catalogue service with scriptable stock changes | Proposed |
| C6 | Mockup top bar shows **"Active – 10 Min Delivery Connected"** (implies live integration) | Mockups vs P8 | Keep the badge but label the data as mock | Proposed |
| C7 | Settings Panel has **Probable Gender** as a scoring input | Settings Panel vs privacy principle P9 | Keep as an optional, user-set lever (never inferred); document in the Responsible-AI note | Proposed |
| C8 | Gemini free tier uses submitted content to improve Google products, but Constitution P9 says photos are processed locally and deleted after parsing | Google pricing page vs Constitution P9 | Option 1: local vision by default, Gemini opt-in. Option 2: Gemini with demo sample photos only, plus a UI notice. Needs P9 amendment either way | **Resolved 2026-10-16:** owner chose Gemini with user-uploaded photos; P9 amended (EXIF stripping, pre-upload notice, local fallback, testers warned) |
| C9 | Brief says "Live Gemini"; Gemini "Live" models are for real-time streaming audio/video, while photo upload is a still image | Owner message vs Gemini model catalogue | Use a standard Flash or Flash-Lite model for still images; model name configurable in `.env` | Proposed |
