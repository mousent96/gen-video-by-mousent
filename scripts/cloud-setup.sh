#!/usr/bin/env bash
# SessionStart hook: chuẩn bị môi trường video khi chạy Claude Code trên cloud
# (claude.ai/code, app điện thoại). Trên máy local thoát ngay.
# Cần network access của environment cho phép thêm: speech.platform.bing.com, cdn.jsdelivr.net (xem README).
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

# 3. edge-tts
python3 -c "import edge_tts" 2>/dev/null || python3 -m pip install -q -U edge-tts >&2 \
  || python3 -m pip install -q -U --break-system-packages edge-tts >&2 || log "pip install edge-tts lỗi"

# 4. Chrome cho HyperFrames (chạy nền, không chặn session)
if [ ! -f .claude/.hf-browser-ok ]; then
  (npx -y hyperframes telemetry disable >/dev/null 2>&1
   npx -y hyperframes browser ensure >/tmp/hf-browser.log 2>&1 && touch .claude/.hf-browser-ok) &
fi

# 5. Kiểm tra mạng tới edge-tts (thường bị chặn ở mức Trusted)
if ! python3 - <<'EOF' 2>/dev/null
import socket; socket.create_connection(("speech.platform.bing.com", 443), timeout=5)
EOF
then
  echo "CẢNH BÁO: không kết nối được speech.platform.bing.com — giọng đọc edge-tts sẽ lỗi. Đổi network access của cloud environment sang Custom (thêm speech.platform.bing.com, cdn.jsdelivr.net) hoặc Full."
fi
echo "Môi trường video cloud: $(command -v ffprobe >/dev/null && echo ffmpeg OK || echo THIẾU ffmpeg); Chrome HyperFrames đang tải nền (log /tmp/hf-browser.log)."
exit 0
