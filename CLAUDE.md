# Gen-video workspace

- `hyperframes/` và `remotion/` là git submodule (source tham khảo: skill + docs) — không sửa, không build. Video dùng CLI bản npm: `npx hyperframes`, `npx remotion`. Thư mục submodule rỗng → `bash scripts/fetch-upstream.sh`.
- Làm video: skill `/video-pipeline` (điều phối A→Z) → `/video-script` → `/video-voice` → `/video-assets` → `/video-build-hyperframes` hoặc `/video-build-remotion` → `/video-render`. Lần đầu / thiếu tool: `/video-setup`.
- Mỗi video nằm trong `productions/<slug>/` (brief, script.json, audio, timeline.json, project/, output/). Trạng thái: `python .claude/skills/video-pipeline/scripts/production.py status`.
- Mặc định: tiếng Việt, giọng `tts.py --provider auto` (edge-tts `vi-VN-HoaiMyNeural`; cloud mạng mặc định → Google TTS), engine HyperFrames, 30 fps.
- Cloud session (`CLAUDE_CODE_REMOTE=true`, ví dụ từ app Claude trên điện thoại): trước khi làm video, nếu `hyperframes/skills` rỗng hoặc thiếu `ffprobe`/edge-tts → `bash scripts/cloud-setup.sh`. Giao video bằng cách commit + push MP4 lên nhánh và gửi link GitHub (chi tiết trong `/video-pipeline`).
- Chạy không có người (GitHub Actions, `--auto`): không hỏi, không dùng dịch vụ trả phí, ghi lựa chọn vào phần "Giả định" của brief.md, render và chạy `verify_render.py` đến khi PASS.
