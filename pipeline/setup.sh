#!/bin/bash
# One-time setup in a fresh session: voice model, Python and Node packages, font check.
# usage: bash pipeline/setup.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
KDIR="${KOKORO_DIR:-$HOME/kokoro}"
mkdir -p "$KDIR"
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  if [ ! -s "$KDIR/$f" ]; then
    echo "downloading $f"
    curl -sSL --retry 3 -o "$KDIR/$f.part" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"
    mv "$KDIR/$f.part" "$KDIR/$f"
  fi
done
python3 -c "import kokoro_onnx, soundfile" 2>/dev/null || pip install --break-system-packages -q kokoro-onnx soundfile
if [ ! -f "$HERE/node_modules/three/build/three.module.js" ]; then
  (cd "$HERE" && npm install --silent --no-audit --no-fund --no-save three@0.160.0)
fi
node -e "require('playwright')" 2>/dev/null || { echo "ERROR: playwright is not available"; exit 1; }
fc-list | grep "Inter Display" >/dev/null || echo "WARNING: the Inter Display font is missing; text will fall back to another font"
command -v ffmpeg >/dev/null || { echo "ERROR: ffmpeg missing"; exit 1; }
echo "setup ok"
