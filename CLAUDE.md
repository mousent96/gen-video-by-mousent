# Gen-video workspace

- `hyperframes/` và `remotion/` là git submodule (source tham khảo: skill + docs) — không sửa, không build. Video dùng CLI bản npm: `npx hyperframes`, `npx remotion`. Thư mục submodule rỗng → `bash scripts/fetch-upstream.sh`.
- Làm video: skill `/video-pipeline` (điều phối A→Z) → `/video-script` → `/video-voice` → `/video-assets` → `/video-build-hyperframes` hoặc `/video-build-remotion` → `/video-render`. Lần đầu / thiếu tool: `/video-setup`.
- Mỗi video nằm trong `productions/<slug>/` (brief, script.json, audio, timeline.json, project/, output/). Trạng thái: `python .claude/skills/video-pipeline/scripts/production.py status`.
- Mặc định: tiếng Việt, giọng edge-tts `vi-VN-HoaiMyNeural`, engine HyperFrames, 30 fps.
- Chạy không có người (GitHub Actions, `--auto`): không hỏi, không dùng dịch vụ trả phí, ghi lựa chọn vào phần "Giả định" của brief.md, render và chạy `verify_render.py` đến khi PASS.
