ZEST 2.0 AI SOUS-CHEF: READ ME FIRST
====================================

Zest is a prototype cooking assistant linked to a MOCK grocery store. All products,
prices and stock are made up. No real orders or payments happen.

WHAT YOU NEED
- A Mac with Apple silicon (M1 or newer) on macOS 14 (Sonoma) or newer
- 16 GB of memory recommended (8 GB works, but slowly)
- About 10 GB of free disk space
- Internet the first time you open Zest (it downloads about 7 GB of local AI models, once)

You do NOT need Python, Node, Homebrew, Ollama or a terminal. Everything is inside Zest 2.0.

INSTALL
1. Drag "Zest 2.0" onto the Applications folder in this window.
2. Open Zest 2.0 from Applications.

THE FIRST TIME: macOS will block Zest
Zest is not signed with a paid Apple developer certificate, so macOS says it
"could not verify" Zest. This happens once:
1. Click "Done" in that message. Do not choose "Move to Trash".
2. Open System Settings > Privacy & Security.
3. Scroll down to Security. Next to "Zest was blocked", click "Open Anyway".
4. Confirm with "Open Anyway", and your password or Touch ID if asked.

WHAT HAPPENS NEXT
- Your browser opens a "Getting Zest ready" page. The first time, it downloads
  the three models with a progress bar (about 10 minutes on a fast connection).
- When the download is done, the page opens Zest. Later launches skip the download.
- Zest stays in the Dock while it runs. Click its Dock icon to reopen Zest in the browser.
  Quit it like any app (Cmd-Q, or right-click the Dock icon > Quit) to free the memory
  its models use.

RUNNING NEXT TO ZEST 1.0
Zest 2.0 can run at the same time as Zest 1.0: 1.0 opens on port 8000 and 2.0 on port 8100,
each with its own Dock icon (2.0's has a "2.0" badge). On a 16 GB Mac, start Ollama yourself
(for example: brew services start ollama) so both share one copy of the models in memory.

IF YOU ALREADY USE OLLAMA
If Ollama is running on this Mac with llama3.2:3b, llama-guard3:1b and
qwen3-vl:4b-instruct, Zest uses it and downloads nothing. Otherwise Zest runs its
own private copy and never changes yours.

WHERE ZEST KEEPS ITS FILES
~/Library/Application Support/Zest 2.0  (the search index and logs; models are shared
with Zest 1.0 when it is installed, so they are not downloaded twice)

To uninstall, delete Zest 2.0 from Applications and delete that folder.

TROUBLESHOOTING
- A download drops: Zest retries it by itself up to 3 times. If it still fails, check the
  internet connection and press "Try again"; downloads resume where they stopped.
  If only the photo model is missing, "Open Zest without photo analysis" lets you start
  now; photos then use the labelled sample photos.
- Nothing opens: look in ~/Library/Application Support/Zest 2.0/logs/launcher.log.
- Optional photo analysis with Google Gemini: create zest.env in the Zest folder above
  with VISION_PROVIDER=gemini, VISION_MODEL=gemini-3.5-flash-lite and your own
  GEMINI_API_KEY. Photos are then sent to Google. Without it, photos stay on this Mac.

Source code, documentation and evidence: https://github.com/VarunParikh/zest-sous-chef
