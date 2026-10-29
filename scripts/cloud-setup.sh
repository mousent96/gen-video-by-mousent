#!/usr/bin/env bash
# Chuẩn bị môi trường video khi chạy Claude Code trên cloud (claude.ai/code, app điện thoại).
# Chạy được với network access mặc định (Trusted): mọi thứ tải từ apt Ubuntu, PyPI, npm, GitHub, Google.
# Trên máy local thoát ngay.
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/..}" || exit 0

log() { echo "[cloud-setup] $*" >&2; }
SUDO=""
[ "$(id -u)" = "0" ] || SUDO="sudo"

# 1. Skill của 2 repo upstream (submodule, sparse)
bash scripts/fetch-upstream.sh >&2 || log "không tải được upstream skills"

# 2. FFmpeg, font tiếng Việt, thư viện cho Chrome headless
if ! command -v ffprobe >/dev/null 2>&1; then
  log "cài ffmpeg + fonts + thư viện Chrome"
  export DEBIAN_FRONTEND=noninteractive
  $SUDO apt-get update -qq >&2 && $SUDO apt-get install -y -qq \
    ffmpeg fonts-noto-core fonts-dejavu-core \
    libnss3 libatk-bridge2.0-0 libgbm1 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxrandr2 libpango-1.0-0 libcairo2 libcups2 >&2 || log "apt install lỗi"
  $SUDO apt-get install -y -qq libasound2t64 >&2 2>/dev/null || $SUDO apt-get install -y -qq libasound2 >&2 || true
fi

# 3. TTS: VieNeu (mặc định, local), edge-tts (nếu mạng cho phép). Google TTS (dự phòng) không cần cài gì.
pip_install() { python3 -m pip install -q "$@" >&2 || python3 -m pip install -q --break-system-packages "$@" >&2; }
python3 -c "import edge_tts" 2>/dev/null || pip_install -U edge-tts || log "pip install edge-tts lỗi"
if ! python3 -c "import vieneu" 2>/dev/null; then
  log "cài VieNeu-TTS"
  pip_install --no-deps vieneu==3.8.3 && pip_install -r scripts/requirements-vieneu.txt || log "pip install vieneu lỗi"
fi

# 3b. Model VieNeu: HuggingFace bị chặn ở mạng mặc định -> lấy bản chép trên GitHub Release của repo này
#     (tạo bởi .github/workflows/mirror-vieneu-models.yml).
HF_CACHE="${HF_HUB_CACHE:-${HF_HOME:-$HOME/.cache/huggingface}/hub}"
if ! ls "$HF_CACHE"/models--pnnbao-ump--VieNeu-TTS-v3-Turbo/snapshots/*/onnx_update/vieneu_backbone_shared.data >/dev/null 2>&1; then
  repo=$(git remote get-url origin 2>/dev/null | sed -E 's#\.git$##; s#.*[:/]([^/:]+/[^/]+)$#\1#')
  url="https://github.com/$repo/releases/download/vieneu-models/vieneu-v3turbo-hf-cache.tar.gz"
  log "tải model VieNeu (~580 MB) từ $url"
  mkdir -p "$HF_CACHE"
  if curl -fsSL --retry 3 "$url" -o /tmp/vieneu-models.tar.gz \
     || gh release download vieneu-models -R "$repo" -p vieneu-v3turbo-hf-cache.tar.gz -O /tmp/vieneu-models.tar.gz >&2; then
    tar -xzf /tmp/vieneu-models.tar.gz -C "$HF_CACHE" && rm -f /tmp/vieneu-models.tar.gz
  else
    log "không tải được model VieNeu — chạy workflow 'Mirror VieNeu models' trên GitHub; tạm dùng Google TTS"
  fi
fi

# 4. Chrome cho HyperFrames (chạy nền, không chặn session)
if [ ! -f .claude/.hf-browser-ok ]; then
  (npx -y hyperframes telemetry disable >/dev/null 2>&1
   npx -y hyperframes browser ensure >/tmp/hf-browser.log 2>&1 && touch .claude/.hf-browser-ok) &
fi

# 5. Provider giọng đọc mà tts.py --provider auto sẽ chọn
tts=$(python3 - <<'EOF'
import urllib.request, urllib.error
def ok(u):
    try:
        urllib.request.urlopen(u, timeout=6); return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False
print("edge" if ok("https://speech.platform.bing.com/") else "google" if ok("https://translate.googleapis.com/") else "KHÔNG CÓ (kiểm tra mạng)")
EOF
)
ls "$HF_CACHE"/models--pnnbao-ump--VieNeu-TTS-v3-Turbo/snapshots/*/onnx_update/vieneu_backbone_shared.data >/dev/null 2>&1 \
  && python3 -c "import vieneu" 2>/dev/null && tts="vieneu (dự phòng: $tts)"
echo "Môi trường video cloud: $(command -v ffprobe >/dev/null && echo ffmpeg OK || echo THIẾU ffmpeg); giọng đọc: $tts; Chrome HyperFrames đang tải nền (log /tmp/hf-browser.log)."
exit 0
