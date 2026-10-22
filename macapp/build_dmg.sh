#!/usr/bin/env bash
# Build Zest.app and Zest-<version>.dmg (ADR-011; US-41). Run with `make dmg` on an Apple-silicon Mac
# that has done `make setup` (Node is needed here only to build the frontend; the app needs no Node).
# Output: macapp/out/. Downloads (pinned, SHA-256 checked) are cached in macapp/.cache/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HERE="$ROOT/macapp"
CACHE="$HERE/.cache"
OUT="$HERE/out"

# Build-time downloads approved 2026-10-22 (build plan §4, C75)
PY_URL="https://github.com/astral-sh/python-build-standalone/releases/download/20261003/cpython-3.12.15%2B20261003-aarch64-apple-darwin-install_only.tar.gz"
PY_SHA="316a463172740e71d8dca1f2730784e325f3f720941137b5d674d5801a632213"
OLLAMA_URL="https://github.com/ollama/ollama/releases/download/v0.40.5/ollama-darwin.tgz"
OLLAMA_SHA="75f9907dafa2fd4c61b5967de2ebb81ccc17eb28da9172edbad0dbc717474dcf"

[ "$(uname -m)" = "arm64" ] || { echo "Build on an Apple-silicon Mac."; exit 1; }
cd "$ROOT"
if [ -n "$(git status --porcelain)" ] && [ "${ZEST_ALLOW_DIRTY:-0}" != "1" ]; then
  echo "Uncommitted changes: commit first so the app matches a commit (or set ZEST_ALLOW_DIRTY=1 for a test build)."
  exit 1
fi
APP_VERSION="$(grep -m1 -E '^## \[[0-9]' CHANGELOG.md | sed -E 's/^## \[([^]]+)\].*/\1/')"
COMMIT="$(git rev-parse --short HEAD)$( [ -n "$(git status --porcelain)" ] && echo -dirty || true)"
VERSION="$APP_VERSION+$COMMIT"
echo "==> Building Zest $VERSION"

fetch() {  # url sha file
  mkdir -p "$CACHE"
  if [ ! -f "$CACHE/$3" ] || [ "$(shasum -a 256 "$CACHE/$3" | cut -d' ' -f1)" != "$2" ]; then
    echo "==> Downloading $3"
    curl -fL --retry 3 -o "$CACHE/$3.part" "$1"
    mv "$CACHE/$3.part" "$CACHE/$3"
  fi
  [ "$(shasum -a 256 "$CACHE/$3" | cut -d' ' -f1)" = "$2" ] || { echo "SHA-256 mismatch for $3"; exit 1; }
}
fetch "$PY_URL" "$PY_SHA" python.tar.gz
fetch "$OLLAMA_URL" "$OLLAMA_SHA" ollama-darwin.tgz

APP="$OUT/Zest.app"
RES="$APP/Contents/Resources"
ZEST="$RES/zest"
rm -rf "$OUT"
mkdir -p "$APP/Contents/MacOS" "$RES/ollama" "$ZEST" "$RES/seed"

echo "==> Python 3.12 runtime"
tar -xzf "$CACHE/python.tar.gz" -C "$RES"   # creates $RES/python
PY="$RES/python/bin/python3"
grep -v -x -E -f "$HERE/runtime-exclude.txt" requirements.lock.txt > "$OUT/requirements.runtime.txt"
"$PY" -m pip install --quiet --no-deps --no-warn-script-location --disable-pip-version-check \
  -r "$OUT/requirements.runtime.txt"
"$PY" -m pip check
# pip's console scripts hard-code this build folder in their first line; the app runs python3 directly
find "$RES/python/bin" -type f ! -name 'python3*' -exec grep -lq "^#!$RES" {} \; -delete

echo "==> Ollama 0.40.5"
tar -xzf "$CACHE/ollama-darwin.tgz" -C "$RES/ollama"

echo "==> Zest code and data"
cp -R src "$ZEST/src"
rm -rf "$ZEST/src/frontend"
find "$ZEST/src" -name __pycache__ -type d -prune -exec rm -rf {} +
mkdir -p "$ZEST/macapp" "$ZEST/mock-data" "$ZEST/assets" "$ZEST/data/models/all-MiniLM-L6-v2"
cp macapp/__init__.py macapp/launcher.py "$ZEST/macapp/"
rsync -a --exclude 'generated/scale_*' --exclude '__pycache__' mock-data/ "$ZEST/mock-data/"
cp -R assets/sample-photos "$ZEST/assets/sample-photos"
cp "$ROOT/.env.example" "$ZEST/.env"
cp LICENSE "$ZEST/LICENSE"
echo "$VERSION" > "$ZEST/VERSION"

echo "==> Frontend build"
npm --prefix src/frontend run build >/dev/null
cp -R src/frontend/dist "$ZEST/frontend"

echo "==> Embedder and vector index"
EMB="$ROOT/data/models/all-MiniLM-L6-v2/onnx"
[ -f "$EMB/model.onnx" ] || .venv/bin/python scripts/index.py   # downloads the embedder into data/models/
cp -R "$EMB" "$ZEST/data/models/all-MiniLM-L6-v2/onnx"
# Built by the bundled Python with the bundle's own .env and embedder path, exactly as the app will load them
(cd "$OUT" && CHROMA_PATH="$RES/seed/chroma" PYTHONPATH="$ZEST/src" PYTHONDONTWRITEBYTECODE=1 "$PY" -s -c '
from backend.catalogue.store import load_store
from backend.config import load_settings
from backend.retrieval.embedder import default_embedder
from backend.retrieval.vector import VectorStore
s = load_settings(); e = default_embedder(s)
VectorStore(s.resolve(s.chroma_path), e).ensure(load_store())
print("    index built with", e.name)')

echo "==> Pre-compiling Python"
"$PY" -m compileall -q -j 0 "$ZEST/src" "$ZEST/macapp" "$RES/python/lib/python3.12" >/dev/null || true

echo "==> App bundle"
# Icon from the owner-supplied artwork (macapp/icon/), placed on the macOS icon grid by make_icon.py
"$PY" -s "$HERE/make_icon.py" "$HERE/icon/zest-icon-source.webp" "$OUT/AppIcon.icns"
cp "$OUT/AppIcon.icns" "$RES/AppIcon.icns"
sed "s/__VERSION__/$APP_VERSION/g; s/__BUILD__/$COMMIT/g" "$HERE/Info.plist" > "$APP/Contents/Info.plist"
# The Dock front end, built for macOS 14+ whatever this Mac runs (swiftc comes with Apple's command-line tools)
swiftc -O -target arm64-apple-macos14.0 -o "$APP/Contents/MacOS/Zest" "$HERE/ZestApp.swift"
cp "$HERE/zest-server.sh" "$RES/zest-server.sh"
chmod +x "$RES/zest-server.sh"
codesign --force --deep --sign - "$APP" 2>/dev/null
codesign --verify --deep "$APP"

echo "==> Smoke check (headless, no model download)"
SMOKE_RT="$(mktemp -d)"
SMOKE_PORT="$("$PY" -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1])')"
ZEST_HEADLESS=1 ZEST_SKIP_PULL=1 ZEST_RUNTIME_DIR="$SMOKE_RT" ZEST_PORT="$SMOKE_PORT" \
  "$RES/zest-server.sh" > "$OUT/smoke.log" 2>&1 &
SMOKE_PID=$!
ok=0
for _ in $(seq 1 120); do
  if curl -fs "http://127.0.0.1:$SMOKE_PORT/launcher/status" >/dev/null 2>&1; then ok=1; break; fi
  sleep 0.5
done
if [ "$ok" = 1 ]; then
  curl -fs "http://127.0.0.1:$SMOKE_PORT/" | grep -q '<div id="root">' || ok=0
  curl -fs "http://127.0.0.1:$SMOKE_PORT/api/v1/health" | grep -q '"components"' || ok=0
  [ -f "$SMOKE_RT/data/chroma/.zest-version" ] || ok=0
fi
kill "$SMOKE_PID" 2>/dev/null || true
wait "$SMOKE_PID" 2>/dev/null || true
rm -rf "$SMOKE_RT"
[ "$ok" = 1 ] || { echo "Smoke check FAILED; see $OUT/smoke.log"; exit 1; }
echo "    smoke check PASS"

echo "==> Disk image"
STAGE="$OUT/dmg"
mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
cp "$HERE/README-first.txt" "$STAGE/Read me first.txt"
cp "$OUT/AppIcon.icns" "$STAGE/.VolumeIcon.icns"
DMG="$OUT/Zest-$APP_VERSION.dmg"
RW="$OUT/rw.dmg"
hdiutil create -quiet -volname "Zest $APP_VERSION" -srcfolder "$STAGE" -fs APFS -format UDRW -ov "$RW"
MNT="$(hdiutil attach -nobrowse -noautoopen "$RW" | tail -1 | awk -F'\t' '{print $NF}')"
SetFile -a C "$MNT"   # the mounted disk shows the Zest icon (.VolumeIcon.icns)
hdiutil detach -quiet "$MNT"
hdiutil convert -quiet "$RW" -format ULMO -ov -o "$DMG"
rm -rf "$STAGE" "$RW"
shasum -a 256 "$DMG" | tee "$DMG.sha256"
du -h "$DMG"
echo "==> Done: $DMG"
