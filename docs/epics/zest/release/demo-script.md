# Demo Script: Zest AI Sous-Chef

**Length:** about 8 minutes, plus fallback plays if something goes wrong.

**Audience:** a reviewer who wants to see that the levers really steer the bot, that the guardrails hold, and that the cart is honest.

**Verified:**
- Every step's input was run on 2026-10-19 at commit `b4cd018`, in-process with the real local models (`llama3.2:3b`, `llama-guard3:1b`; sample photos). The message IDs below are what came back.
- The browser path is rehearsed twice in block 3.4 (Test Plan §9).
- Steps 1 and 7 were checked the same way: the greeting came back as MSG-GREET, and the add-on tap as MSG-EDIT-OK with Undo.

**Note on prices:** they come from a mock catalogue, and the expected dishes can shift if the catalogue or levers change. The message IDs and behaviours are what to look for, not the exact dish.

## Before you start (2 minutes, off camera)
1. Close other apps. The models need about 16 GB with nothing else heavy running (E1 and E11 conditions).
2. Run `make app` and open http://localhost:5173. Check that the health page (`/health` on the backend) shows the model loaded and the index ready.
3. Send one throwaway message to warm the models, then refresh the page. A cold first reply took about 4 s in E11; warm mood replies take about 1.2 s.

## The demo
| # | Do this | Persona or lever | You should see | Message IDs (dry run) |
|---|---|---|---|---|
| 1 | Open the page | Default | Split screen: levers on the left, chat on the right; greeting; the cart icon greyed out | MSG-GREET |
| 2 | Pick the **Meera Shah** preset, press **Start new chat**, type `I am feeling indulgent` | Meera Shah (Jain) | A dish is carted (dry run: Butter Naan), with a one-line reason, two swap options, Undo, the ⓘ "Why this?" panel and one add-on offer. Open ⓘ: the biggest factors and the score breakdown | MSG-MOOD-ADD, MSG-ADDON |
| 3 | Tap a **Swap to** option | Meera Shah | The dish is replaced; other cart items are untouched | MSG-MOOD-SWAP |
| 4 | Type `I want to make Garlic Bread` | Meera Shah (Jain) | Blocked by the Jain rule, with an alternative chip (dry run: Moong Dal Halwa). Nothing is carted | MSG-PERSONA-BLOCK |
| 5 | Pick the **Karan Malhotra** preset. Note the banner "Changes apply from your next chat session". Press **Start new chat** and send `I am feeling indulgent` again | Karan Malhotra (Keto, non-veg) | A different dish for the same words (dry run: Mutton Curry). Optional: the **Alex (Reviewer)** preset gives a third (dry run: Lachha Paratha). Open the inspector to show candidates, similarity, eligibility and final score | MSG-MOOD-ADD, MSG-ADDON |
| 6 | Paste the first demo video link from `mock-data/videos.json` (Mysore Rasam) | Alex (Reviewer) | Live transcript if reachable, otherwise the saved copy. The ingredients are carted. The bot then asks which of two similar items you mean; answer it | MSG-YT-FIXTURE (live fetch off in the dry run), MSG-YT-OK, MSG-EDIT-UNCLEAR, MSG-ADDON |
| 7 | Tap **Add** on an add-on offer | any | The companion dish is added with Undo (dry run: Missi Roti); nothing is ever added without a tap (US-19) | MSG-EDIT-OK |
| 8 | Pick a **Sample** photo (RF01) | Alex (Reviewer) | "I think I can see … (estimates). Shall I find a dish with these?" Tap **Yes**: only the missing items are carted | MSG-PHOTO-CONFIRM, then MSG-PHOTO-OK, MSG-ADDON |
| 9 | Open the cart window | any | Lines grouped by dish; a shared ingredient shows as a dimmed, unpriced line; change a quantity; the totals update | (cart API: quantity HTTP 200) |
| 10 | Press **Buy Now**, then press it again | any | "Order is placed, the rider will see you in 10 mins" with a 10-second progress bar, then the window collapses and the cart is empty. The second press does not create a second order | checkout HTTP 200; same order ID on the second press |

## Talking points
- **The levers are code.** The four weights, history and trend sliders, persona filters and business rules are applied after retrieval, to a wide pool. The model never ranks (ADR-004, ADR-008). Hard filters move results strongly; soft sliders less than hoped (E6 FAIL, accepted as C57).
- **Guardrails come after retrieval, in code.** In E7, 0 violations in about 24,800 real-model checks across 11 personas.
- **Prices and SKUs come only from the catalogue.** E8 found 0 mismatches in 200 random carts. The model writes one reason line; everything else is templates.
- **Failures degrade, never crash.** E10: 26 of 26 fault scenarios take their defined fallback.
- **Honest status.** The overall evaluation status is FAIL under our own rule, with four accepted limitations (E2, E3, E4, E6). The evidence report is linked from the README.

## Fallback plays
| If this happens | Do this | What the audience sees |
|---|---|---|
| A reply is slow | Point at the locked input and the progress indicator; wait | Input locked until the reply arrives (E10 F25) |
| The video can't be read | Paste the recipe text instead | MSG-YT-PASTE, then the text flow |
| Photo upload is slow or fails | Use a **Sample** photo | MSG-PHOTO-SAMPLES offers the labelled samples |
| The backend is down | Restart `make app`; the page shows the failure message meanwhile | MSG-SERVER, no fake success (E10 F26) |
| A phrase is redirected as off-topic | Rephrase with a food word ("I want to cook …") | MSG-REDIRECT is a known limitation (see Known Limitations) |

## Left out on purpose
- **Stock-out mid-chat:** the demo stock controls (API endpoints 14 and 15) were cut with UJ22 (C72). Substitution at Buy Now is covered by tests T-058 and T-059.
- **Chat cart edits** ("remove the oil") reply MSG-UNSUPPORTED (FR-78 cut). Edit in the cart window instead.
