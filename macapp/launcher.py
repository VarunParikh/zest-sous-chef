"""Zest.app launcher (ADR-011; US-41; tests T-111 to T-114).

Started by the Dock app (`macapp/ZestApp.swift`) through `zest-server.sh` with the bundled Python. It checks the Mac, seeds
the writable runtime folder, picks or starts an Ollama server, serves Zest's unchanged API
(`create_app()`) plus the built frontend on one port, fetches missing models with a progress
page, and runs until the Dock app sends SIGTERM (Quit, logout or shutdown). Nothing in `src/backend` changes: the launcher only adds
routes around the app object, after Zest's own routes, so an API route always wins.

Environment switches (development and the build smoke check only):
ZEST_HEADLESS=1 (no dialogs, no browser; stop on SIGTERM), ZEST_SKIP_PULL=1 (never download),
ZEST_PORT, ZEST_RUNTIME_DIR, ZEST_FORCE_PRIVATE_OLLAMA=1, ZEST_OLLAMA_MODELS.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path

MIN_MACOS = (14, 0)
MIN_RAM_GB = 16
MIN_FREE_GB_FOR_MODELS = 9  # three models are about 6.9 GB; Ollama needs headroom while unpacking
DEFAULT_OLLAMA = "http://127.0.0.1:11434"
PRIVATE_OLLAMA_PORT = 11435
PREFERRED_PORT = 8000
STALL_S = 120  # no progress message from Ollama for this long: the pull is dropped and retried (Ollama resumes)
AUTO_RETRIES = 3  # attempts per model before the page asks the user to press Try again
RETRY_BACKOFF_S = 5.0
STAGES = {"pulling manifest": "Starting", "verifying sha256 digest": "Verifying",
          "writing manifest": "Finishing", "removing any unused layers": "Finishing", "success": "Finishing"}

# Bundle layout: Contents/Resources/{python,ollama,zest,seed}; this file is Resources/zest/macapp/launcher.py
RESOURCES = Path(__file__).resolve().parents[2]
ZEST_ROOT = RESOURCES / "zest"


# ---------------------------------------------------------------- pure logic (unit-tested)

def platform_problems(machine: str, macos: str, ram_bytes: int) -> tuple[list[str], list[str]]:
    """Errors stop the launch; warnings are shown once and the launch continues (T-111)."""
    errors, warnings = [], []
    if machine != "arm64":
        errors.append(f"Zest needs a Mac with Apple silicon (M1 or newer). This Mac reports '{machine}'.")
    try:
        version = tuple(int(p) for p in (macos.split(".") + ["0"])[:2])
    except ValueError:
        version = (0, 0)
    if version < MIN_MACOS:
        errors.append(f"Zest needs macOS {MIN_MACOS[0]} (Sonoma) or newer. This Mac runs macOS {macos or 'unknown'}.")
    ram_gb = ram_bytes / 2**30
    if ram_gb < MIN_RAM_GB - 0.5:
        warnings.append(f"This Mac has {ram_gb:.0f} GB of memory; Zest's three local models are tested on {MIN_RAM_GB} GB. "
                        "Replies may be slow. Close other apps for the best result.")
    return errors, warnings


def required_models(settings) -> list[str]:
    """The Ollama models this configuration calls (ADR-002, ADR-006, ADR-003 v3)."""
    models = [settings.llm_model]
    if settings.guard_classifier and settings.guard_model:
        models.append(settings.guard_model)
    if settings.vision_provider == "ollama" and settings.vision_model:
        models.append(settings.vision_model)
    return list(dict.fromkeys(models))


def _same_model(a: str, b: str) -> bool:
    norm = lambda m: m if ":" in m else f"{m}:latest"  # noqa: E731
    return norm(a) == norm(b)


def missing_models(served: list[str] | None, required: list[str]) -> list[str]:
    served = served or []
    return [m for m in required if not any(_same_model(m, s) for s in served)]


def plan_ollama(default_served: list[str] | None, required: list[str], force_private: bool = False) -> str:
    """'reuse' the recipient's Ollama on 11434 only if it already serves every model; else 'private' (T-112)."""
    if not force_private and default_served is not None and not missing_models(default_served, required):
        return "reuse"
    return "private"


def seed_runtime(seed_chroma: Path, runtime: Path, version: str) -> bool:
    """Copy the bundled index into the writable runtime folder on first launch or a new version (T-113).
    Returns True when it copied."""
    target = runtime / "data" / "chroma"
    marker = target / ".zest-version"
    if marker.exists() and marker.read_text().strip() == version:
        return False
    if target.exists():
        shutil.rmtree(target)
    if seed_chroma.is_dir():
        shutil.copytree(seed_chroma, target)
    else:  # no seed: Zest builds the index on the first chat turn (vector.ensure)
        target.mkdir(parents=True)
    marker.write_text(version + "\n")
    return True


def runtime_env(runtime: Path, ollama_url: str) -> dict[str, str]:
    """Absolute paths outside the read-only bundle (T-113)."""
    return {
        "CHROMA_PATH": str(runtime / "data" / "chroma"),
        "TRACE_PATH": str(runtime / "logs" / "trace.jsonl"),
        "OLLAMA_BASE_URL": ollama_url,
    }


def user_overrides(path: Path) -> dict[str, str]:
    """Optional `zest.env` in the runtime folder (for example an opt-in Gemini key). Never inside the bundle."""
    if not path.exists():
        return {}
    from dotenv import dotenv_values

    return {k.upper(): v for k, v in dotenv_values(path).items() if v}


def merge_progress(parts: dict[str, list[int]], msg: dict) -> dict[str, list[int]]:
    """Fold one `/api/pull` stream message into {digest: [completed, total]}."""
    digest, total = msg.get("digest"), msg.get("total")
    if digest and total:
        parts[digest] = [int(msg.get("completed") or 0), int(total)]
    return parts


def percent(parts: dict[str, list[int]]) -> float:
    total = sum(t for _, t in parts.values())
    return round(100 * sum(c for c, _ in parts.values()) / total, 1) if total else 0.0


def stage_label(status: str, pct: float) -> str:
    """What the page shows for a model being fetched; never "Downloading 100%" while Ollama is finishing up."""
    if status in STAGES:
        return STAGES[status]
    if pct >= 100:
        return "Finishing"
    return f"Downloading {pct:.0f}%"


def can_open(models: dict[str, dict], optional: list[str]) -> bool:
    """Zest works without the optional models (the photo model: photos fall back to the sample photos, FR-55)."""
    return bool(models) and all(v.get("status") == "ready" for k, v in models.items() if k not in optional)


def free_port(preferred: int) -> int:
    for port in (preferred, 0):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return s.getsockname()[1]
            except OSError:
                continue
    raise RuntimeError("no free port")


# ---------------------------------------------------------------- setup state and the packaged app

@dataclass
class Setup:
    phase: str = "starting"  # starting | downloading | ready | error
    message: str = "Starting Zest…"
    models: dict[str, dict] = field(default_factory=dict)  # name -> {status, percent}
    warnings: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)  # models Zest can run without (see can_open)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    retry: threading.Event = field(default_factory=threading.Event, repr=False)

    def snapshot(self) -> dict:
        with self.lock:
            models = {k: dict(v) for k, v in self.models.items()}
            return {"phase": self.phase, "message": self.message, "warnings": list(self.warnings), "models": models,
                    "can_open": can_open(models, self.optional), "optional": list(self.optional)}

    def set(self, **kw) -> None:
        with self.lock:
            for k, v in kw.items():
                setattr(self, k, v)

    def model(self, name: str, **kw) -> None:
        with self.lock:
            self.models.setdefault(name, {"status": "waiting", "percent": 0.0}).update(kw)


def build_app(setup: Setup, dist: Path, create=None):
    """Zest's API unchanged, then the setup routes, then the built frontend at `/` (T-114)."""
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles

    if create is None:
        from backend.api.app import create_app as create
    app = create()

    @app.get("/launcher/status", include_in_schema=False)
    async def launcher_status() -> JSONResponse:
        return JSONResponse(setup.snapshot(), headers={"Cache-Control": "no-store"})

    @app.post("/launcher/retry", include_in_schema=False)
    async def launcher_retry() -> dict:
        setup.retry.set()
        return {"ok": True}

    @app.get("/launcher/", include_in_schema=False, response_class=HTMLResponse)
    async def launcher_page() -> str:
        return SETUP_PAGE

    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


# ---------------------------------------------------------------- side effects (process, Ollama, dialogs)

def _served(base: str, timeout: float = 2.0) -> list[str] | None:
    import httpx

    try:
        r = httpx.get(f"{base}/api/tags", timeout=timeout)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None


def _start_private_ollama(runtime: Path) -> tuple[subprocess.Popen, str]:
    binary = RESOURCES / "ollama" / "ollama"
    base = f"http://127.0.0.1:{PRIVATE_OLLAMA_PORT}"
    models_dir = Path(os.environ.get("ZEST_OLLAMA_MODELS") or runtime / "ollama-models")
    models_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "OLLAMA_HOST": f"127.0.0.1:{PRIVATE_OLLAMA_PORT}", "OLLAMA_MODELS": str(models_dir)}
    log = open(runtime / "logs" / "ollama.log", "ab")  # noqa: SIM115  kept open for the child's lifetime
    proc = subprocess.Popen([str(binary), "serve"], env=env, stdout=log, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, start_new_session=True)
    for _ in range(60):
        if _served(base, timeout=1.0) is not None:
            return proc, base
        if proc.poll() is not None:
            break
        time.sleep(0.5)
    raise RuntimeError("The bundled model server did not start (see logs/ollama.log in the Zest folder).")


def _pull(base: str, model: str, setup: Setup) -> None:
    import httpx

    parts: dict[str, list[int]] = {}
    setup.model(model, status="downloading", detail="Starting")
    # The read timeout is the stall watchdog: Ollama streams a message at least every few seconds while it works
    with httpx.stream("POST", f"{base}/api/pull", json={"model": model}, timeout=httpx.Timeout(30, read=STALL_S)) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line.strip():
                continue
            msg = json.loads(line)
            if msg.get("error"):
                raise RuntimeError(msg["error"])
            merge_progress(parts, msg)
            pct = percent(parts)
            setup.model(model, percent=pct, detail=stage_label(msg.get("status", ""), pct))
    setup.model(model, status="ready", percent=100.0, detail="Ready")


def _pull_with_retries(base: str, model: str, setup: Setup) -> None:
    for attempt in range(1, AUTO_RETRIES + 1):
        try:
            _pull(base, model, setup)
            return
        except Exception as e:  # noqa: BLE001  logged in full; the page shows a plain sentence
            print(f"pull {model} attempt {attempt} failed: {e!r}", file=sys.stderr, flush=True)
            if attempt == AUTO_RETRIES:
                setup.model(model, status="failed", detail="Paused")
                raise RuntimeError(f"The connection dropped while downloading {model}, {AUTO_RETRIES} times. Check the "
                                   "internet connection, then press Try again; the download resumes where it stopped.") from e
            setup.model(model, status="downloading",
                        detail=f"Connection dropped, retrying ({attempt + 1} of {AUTO_RETRIES})")
            time.sleep(RETRY_BACKOFF_S * attempt)


def prepare_models(base: str, required: list[str], runtime: Path, setup: Setup, skip_pull: bool) -> None:
    while True:
        served = _served(base)
        missing = missing_models(served, required)
        for m in required:
            setup.model(m, status="waiting" if m in missing else "ready", percent=0.0 if m in missing else 100.0,
                        detail="Waiting" if m in missing else "Ready")
        if not missing or skip_pull:
            setup.set(phase="ready", message="Zest is ready." if not missing else "Model download skipped.")
            return
        try:
            free_gb = shutil.disk_usage(runtime).free / 2**30
            if free_gb < MIN_FREE_GB_FOR_MODELS:
                raise RuntimeError(f"Zest needs about {MIN_FREE_GB_FOR_MODELS} GB free to download its models; "
                                   f"this Mac has {free_gb:.1f} GB free. Free some space, then press Try again.")
            setup.set(phase="downloading",
                      message="First launch: downloading Zest's local AI models (about 7 GB). This happens once.")
            for m in missing:
                _pull_with_retries(base, m, setup)
            setup.set(phase="ready", message="Zest is ready.")
            return
        except Exception as e:  # noqa: BLE001  shown on the setup page; the user can retry
            setup.set(phase="error", message=str(e) or type(e).__name__)
            setup.retry.wait()
            setup.retry.clear()


def alert(title: str, message: str) -> None:
    """A one-off alert for a launch that cannot continue. The text is passed as arguments, never spliced into the script."""
    subprocess.run(["osascript", "-e", "on run argv",
                    "-e", 'display alert (item 1 of argv) message (item 2 of argv) as critical buttons {"OK"}',
                    "-e", "end run", title, message], capture_output=True)


def _ram_bytes() -> int:
    try:
        return int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout.strip())
    except ValueError:
        return 0


def _running_instance(lock: Path) -> str | None:
    try:
        info = json.loads(lock.read_text())
        os.kill(int(info["pid"]), 0)
    except (OSError, ValueError, KeyError):
        return None
    import httpx

    try:
        httpx.get(f"http://127.0.0.1:{info['port']}/launcher/status", timeout=1.0).raise_for_status()
        return f"http://127.0.0.1:{info['port']}"
    except httpx.HTTPError:
        return None


def main() -> int:
    headless = os.environ.get("ZEST_HEADLESS") == "1"
    runtime = Path(os.environ.get("ZEST_RUNTIME_DIR") or Path.home() / "Library" / "Application Support" / "Zest")
    (runtime / "logs").mkdir(parents=True, exist_ok=True)

    errors, warnings = platform_problems(platform.machine(), platform.mac_ver()[0], _ram_bytes())
    if errors:
        if not headless:
            alert("Zest cannot run on this Mac", "\n\n".join(errors))
        print("\n".join(errors), file=sys.stderr)
        return 1

    lock = runtime / "launcher.json"
    existing = _running_instance(lock)
    if existing:  # second double-click: just bring the app back up
        if not headless:
            webbrowser.open(existing + "/")
        return 0

    version = (ZEST_ROOT / "VERSION").read_text().strip() if (ZEST_ROOT / "VERSION").exists() else "dev"
    seed_runtime(RESOURCES / "seed" / "chroma", runtime, version)

    os.environ.update(user_overrides(runtime / "zest.env"))
    from backend.config import load_settings

    settings = load_settings()
    required = required_models(settings)
    optional = [settings.vision_model] if settings.vision_provider == "ollama" else []
    setup = Setup(warnings=warnings, optional=optional)
    ollama_proc = None
    plan = plan_ollama(_served(DEFAULT_OLLAMA), required, os.environ.get("ZEST_FORCE_PRIVATE_OLLAMA") == "1")
    try:
        if plan == "reuse":
            base = DEFAULT_OLLAMA
        else:
            ollama_proc, base = _start_private_ollama(runtime)
    except RuntimeError as e:
        if not headless:
            alert("Zest could not start", str(e))
        print(e, file=sys.stderr)
        return 1
    os.environ.update(runtime_env(runtime, base))

    import uvicorn

    port = free_port(int(os.environ.get("ZEST_PORT") or PREFERRED_PORT))
    url = f"http://127.0.0.1:{port}"
    app = build_app(setup, ZEST_ROOT / "frontend")
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    lock.write_text(json.dumps({"pid": os.getpid(), "port": port}))
    print(f"Zest {version}: {url} (Ollama {plan} at {base})", flush=True)

    threading.Thread(target=prepare_models, args=(base, required, runtime, setup, os.environ.get("ZEST_SKIP_PULL") == "1"),
                     daemon=True).start()

    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, lambda *_: stop.set())
    try:
        while not server.started and server_thread.is_alive():
            time.sleep(0.1)
        if not headless:
            webbrowser.open(url + "/launcher/")
        # Runs until the Dock app (macapp/ZestApp.swift) sends SIGTERM on Quit, logout or shutdown. If the Dock
        # app disappears without that (Force Quit), this process is re-parented to launchd and stops too.
        parent = os.getppid()
        while not stop.wait(0.5) and server_thread.is_alive():
            if parent != 1 and os.getppid() == 1:
                break
    finally:
        server.should_exit = True
        server_thread.join(timeout=10)
        if ollama_proc is not None:
            ollama_proc.terminate()
            try:
                ollama_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                ollama_proc.kill()
        lock.unlink(missing_ok=True)
    return 0


SETUP_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Getting Zest ready</title>
<style>
:root{--bg:#faf8f3;--card:#fff;--ink:#1f2421;--muted:#5f6862;--line:#e4e1d8;--accent:#2f7d4f;--warn:#9a5b00;--err:#b42318}
@media (prefers-color-scheme:dark){:root{--bg:#141715;--card:#1d211f;--ink:#eef1ee;--muted:#a3aca6;--line:#2e3430;--accent:#5cc98a;--warn:#f0b35a;--err:#ff8a7a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:560px;margin:8vh auto;padding:0 16px}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:28px}
h1{font-size:1.5rem;margin:0 0 4px}p{margin:0 0 16px;color:var(--muted)}.row{margin:14px 0}.name{display:flex;justify-content:space-between;font-size:.95rem}
.bar{height:8px;border-radius:4px;background:var(--line);overflow:hidden;margin-top:6px}.fill{height:100%;background:var(--accent);width:0;transition:width .4s}
.warn{color:var(--warn);font-size:.9rem}.err{color:var(--err)}button.alt{background:transparent;color:var(--accent);border:1px solid var(--accent);margin-left:8px}button{margin-top:12px;font:inherit;padding:8px 16px;border-radius:8px;border:0;background:var(--accent);color:#fff;cursor:pointer}
small{color:var(--muted)}
</style></head><body><main><div class="card">
<h1>Getting Zest ready</h1><p id="msg">Starting…</p><div id="models"></div><div id="warn"></div><div id="act"></div>
<small>All store data in Zest is mock. Models run on this Mac.</small></div></main>
<script>
const label={waiting:"Waiting",downloading:"Downloading",ready:"Ready",failed:"Paused"};
async function tick(){
  let s;try{s=await (await fetch("/launcher/status",{cache:"no-store"})).json()}catch(e){return setTimeout(tick,1500)}
  document.getElementById("msg").textContent=s.message;
  document.getElementById("msg").className=s.phase==="error"?"err":"";
  const m=document.getElementById("models");m.replaceChildren();
  for(const [name,v] of Object.entries(s.models)){
    const row=document.createElement("div");row.className="row";
    const n=document.createElement("div");n.className="name";
    const a=document.createElement("span");a.textContent=name;const b=document.createElement("span");
    b.textContent=v.detail||label[v.status]||v.status;
    n.append(a,b);const bar=document.createElement("div");bar.className="bar";const f=document.createElement("div");
    f.className="fill";f.style.width=(v.status==="ready"?100:v.percent)+"%";bar.append(f);row.append(n,bar);m.append(row)}
  const w=document.getElementById("warn");w.replaceChildren();
  for(const t of s.warnings){const p=document.createElement("p");p.className="warn";p.textContent=t;w.append(p)}
  const act=document.getElementById("act");const key=s.phase+"|"+s.can_open+"|"+s.message;
  if(act.dataset.key!==key){act.dataset.key=key;act.replaceChildren();  // rebuilt only on change, so clicks are never lost
  if(s.phase==="error"){const btn=document.createElement("button");btn.textContent="Try again";
    btn.onclick=()=>fetch("/launcher/retry",{method:"POST"});act.append(btn);
    if(s.can_open){const go=document.createElement("button");go.className="alt";
      go.textContent="Open Zest without photo analysis";go.onclick=()=>location.assign("/");act.append(go);
      const n=document.createElement("p");n.className="warn";
      n.textContent="Zest works now. Photos use the labelled sample photos until "+s.optional.join(", ")+" is downloaded; reopen Zest from the Dock to try again.";
      act.append(n)}}}
  if(s.phase==="ready"){location.replace("/");return}
  setTimeout(tick,1000)}
tick();
</script></body></html>
"""

if __name__ == "__main__":
    sys.exit(main())
