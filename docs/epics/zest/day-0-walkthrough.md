# Day 0 Walkthrough: from this zip to Claude Code running on your Mac

Audience: the owner, new to the terminal. Time: about 60 to 90 minutes. Commands were written for macOS on Apple silicon. Install commands change; where I could not verify one, the step says "copy it from the official page". Nothing here has been run on your Mac.

**Report back after each step** (key, tools, repo, first prompt), as you asked: send me a one-line "done" or the exact error text.

**Rules for the whole day:** never paste a key into chat, code, a document or a commit. If a command asks "Are you sure?", read it before saying yes. If anything prints a red error, stop and paste the error to me, with the command you ran.

## Terminal basics (2 minutes)
- Open Terminal: press Cmd+Space, type `Terminal`, press Enter.
- A command is a line you type and run with Enter. `cd folder` moves into a folder, `ls` lists files, `pwd` shows where you are.
- To paste, use Cmd+V. A `#` starts a comment; you do not type those.

## Step 1: What you need before you start
| Need | Check |
|---|---|
| A Claude Pro, Max, Team or Enterprise plan (you have Pro) | https://code.claude.com/docs/en/desktop-quickstart |
| A GitHub account | https://github.com |
| A Google account for the Gemini key | https://aistudio.google.com |
| About 10 GB free disk space (local model, tools) | Apple menu, About This Mac, Storage |

## Step 2: Rotate the Gemini key (5 minutes)
1. Open Google AI Studio, go to API keys.
2. Delete the old key that was pasted in chat. Create a new one.
3. Save the new key in a password manager or a private note. Do not paste it anywhere else yet.
Also read the free-tier limits and data-use terms on https://ai.google.dev/gemini-api/docs/pricing.

## Step 3: Install the tools
1. **Homebrew** (the Mac package installer): go to https://brew.sh, copy the one-line install command shown there and run it in Terminal. At the end it prints "Next steps" with two lines to run. Run them, then close and reopen Terminal.
2. Install the rest: `brew install git python@3.12 node gh ollama`
   (If a name is not found, tell me the exact message.)
3. Check each tool prints a version: `git --version`, `python3.12 --version`, `node --version`, `gh --version`, `ollama --version`.
4. Ollama may also need to run as a background app; if `ollama list` fails, open the Ollama app once and retry.
Do not download any language model yet. Day 1 block 1.5 benchmarks two or three candidates and records the choice.

## Step 4: Create the GitHub repository
1. Sign in: `gh auth login` (choose GitHub.com, HTTPS, and log in through the browser).
2. On github.com click New repository. Name it `zest-sous-chef`. Choose **Public**. Do **not** add a README, licence or .gitignore (the project already has them). Create it and copy its URL.

## Step 5: Put the project on your Mac
1. Download `zest-sous-chef.zip` from the chat and move it to a folder you will remember, for example `~/Projects` (create the folder in Finder if needed).
2. Double-click the zip to unzip it. You should see a folder `zest-sous-chef`.
3. In Terminal: `cd ~/Projects/zest-sous-chef` then `git status`. It should say "nothing to commit" (a clean copy).
4. Connect it to GitHub: `git remote add origin <your repo URL>`.
5. **Secret check before the first push:** run `git log -p | grep -c "AIza"`. It must print `0`. (Google API keys begin with AIza.) Also run `git status --ignored` and confirm `.env` is not listed as tracked.
6. Push: `git push -u origin main`. Everything pushed is public, including `docs/inputs/` (you approved that) and the licensed reference photos in `assets/sample-photos/` (you stated they are licensed; I could not verify that).

## Step 6: Install the Claude desktop app and open the Code tab
Decided 2026-10-17: you will use the desktop app. Your Claude Pro plan qualifies: the docs say Claude Code requires a Pro, Max, Team or Enterprise subscription (https://code.claude.com/docs/en/desktop-quickstart).
1. Download the macOS installer from the docs page above (universal build for Intel and Apple silicon), run it, launch Claude from Applications and sign in.
2. Click the **Code** tab at the top centre. If it asks you to upgrade or sign in, follow the prompt. If you see a 403 error, see https://code.claude.com/docs/en/desktop#403-or-authentication-errors-in-the-code-tab.
3. Choose **Local**, click **Select folder**, and pick `~/Projects/zest-sous-chef`. The app includes Claude Code, so you do not need to install Node or the CLI for this.
4. Pick a model from the dropdown next to the send button.
5. **Permission mode (next to the send button):** use **Plan** for the first prompt, then **Manual** for Day 1 so you see a diff and Accept or Reject buttons for every change. Do not use **Auto** until Day-1 gates have passed.

## Step 7: First session
1. In the Code tab, with the project folder selected, paste the prompt below into the prompt box (it is also in `docs/epics/zest/build-plan.md` section 7). Claude Code reads `CLAUDE.md` automatically.
2. It proposes a plan first. Read it, then approve. It will ask before installing packages: approve only those on the list in build-plan section 4, and say no to anything else.
3. You can interrupt at any time with the stop button, or type a correction and press Enter.
4. After it creates `.env.example`, open the Terminal app, `cd ~/Projects/zest-sous-chef`, run `cp .env.example .env`, then `open -e .env` and paste the **new** Gemini key. Save. Check with `git status` that `.env` does not appear.

```
You are building Zest, a web-based AI sous-chef prototype. Read CLAUDE.md first, then follow
docs/epics/zest/build-plan.md sections 5 and 6. Work in plan mode. Start with Day 1 block 1.1.
Rules: no implementation without an approved spec section; tests before code; mock data only;
guardrails in code after retrieval; never write the Gemini key anywhere except the local .env;
use only the dependencies in build-plan section 4 and ask before adding any other; log any
document conflict in docs/core/open-conflicts.md instead of resolving it silently; commit after
each story with a conventional commit and a CHANGELOG line. After each block, run the tests for
that block and report real results (PASS, FAIL, BLOCKED, NOT RUN) before moving on. Stop and ask
me if a Day-1 gate fails.
```

## Step 8: What to do each day
- After each block, read the test results Claude Code reports. Real statuses only: PASS, FAIL, BLOCKED, NOT RUN. If it says "all green" without commands and output, ask for them.
- Each evening: 10-minute checkpoint (build-plan section 9).
- Come back to this chat for: a failed gate, a document conflict, the release documents, and the final consistency check.

## Common problems
| Symptom | First thing to try |
|---|---|
| `command not found: brew` after installing | Run the two "Next steps" lines Homebrew printed, reopen Terminal |
| The Code tab asks you to upgrade or shows a 403 error | Sign in again and restart the app; see the desktop troubleshooting link in Step 6 |
| `git push` asks for a password | Run `gh auth login` again and choose HTTPS |
| `ollama list` cannot connect | Open the Ollama app once, retry |
| Disk full during install | Free space first; local models are several GB |

## Checklist
- [ ] New Gemini key created, old one deleted
- [ ] Tools installed and version-checked
- [ ] GitHub repo created, secret check printed 0, first push done
- [ ] Claude Code installed and logged in
- [ ] First prompt pasted, `.env` created with the new key, not tracked by git

Sources: Claude Code overview and install: https://code.claude.com/docs/en/overview · Homebrew: https://brew.sh · Gemini pricing and terms: https://ai.google.dev/gemini-api/docs/pricing · GitHub CLI: https://cli.github.com
