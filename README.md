# Gen-video

Bộ skill Claude Code tự động làm video từ A→Z — chủ đề → kịch bản → giọng đọc → media → dựng → render MP4 — trên hai engine:

- [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP) — mặc định
- [Remotion](https://github.com/remotion-dev/remotion) (React)

Hai repo trên được gắn làm **git submodule** (ghim commit) để skill đọc tài liệu/skill gốc của chúng. Video được render bằng CLI bản npm (`npx hyperframes`, `npx remotion`), không build source.

## Cấu trúc

```
.claude/skills/
  video-pipeline/        điều phối A→Z + scripts/ (production, TTS, timeline, scaffold, verify)
  video-setup/           kiểm tra & cài môi trường
  video-script/          kịch bản → script.json
  video-voice/           giọng đọc edge-tts (có tiếng Việt) → timeline.json, captions.srt
  video-assets/          nhạc, SFX, logo, icon, ảnh
  video-build-hyperframes/
  video-build-remotion/
  video-render/          render, kiểm tra, thumbnail
.github/
  actions/setup-video-env/   cài ffmpeg, font, edge-tts, Chrome, tải skill upstream
  workflows/generate-video.yml   chạy tay: điền chủ đề → nhận MP4
  workflows/claude.yml           @claude trong issue/PR
scripts/fetch-upstream.sh    tải submodule dạng sparse (chỉ phần skill)
productions/<slug>/          mỗi video một thư mục (MP4 và node_modules không commit)
```

## Chạy trên máy

```bash
git clone --recurse-submodules --shallow-submodules <repo-của-bạn>
# hoặc nhẹ hơn (chỉ phần skill của upstream):
git clone <repo-của-bạn> && cd Gen-video && bash scripts/fetch-upstream.sh
```

Mở thư mục bằng Claude Code, chạy `/video-setup` lần đầu, rồi nói ví dụ: *"làm video TikTok 30 giây về 5 mẹo tiết kiệm tiền"*.

## Chạy trên GitHub

1. Push repo lên GitHub.
2. **Settings → Secrets and variables → Actions**, thêm **một** trong hai:
   - `ANTHROPIC_API_KEY` — API key (tính phí theo API), hoặc
   - `CLAUDE_CODE_OAUTH_TOKEN` — dùng gói Claude Pro/Max, lấy bằng `claude setup-token`.
3. Cài GitHub App của Claude (cần cho `claude.yml`): chạy `/install-github-app` trong Claude Code CLI, hoặc cài tại https://github.com/apps/claude.

**Cách 1 — form:** tab **Actions → Generate video → Run workflow**, điền chủ đề, khung hình, độ dài, engine. Xong, tải MP4 ở mục **Artifacts** của lần chạy. Bật `commit_sources` để lưu brief/script/timeline vào nhánh `video/<slug>`.

**Cách 2 — issue:** tạo issue hoặc comment `@claude làm video 16:9 dài 60 giây giải thích lãi kép`. Claude trả lời trong issue; video nằm ở Artifacts của workflow run.

Trên GitHub Actions pipeline chạy chế độ tự động: không dừng chờ duyệt, chỉ dùng công cụ miễn phí (edge-tts, SFX có sẵn). Mỗi video mất khoảng 10–30 phút runner.

## Cập nhật upstream

```bash
git submodule update --remote hyperframes remotion
git add hyperframes remotion && git commit -m "chore: bump upstream"
```

## Lưu ý

- Remotion miễn phí cho cá nhân và công ty ≤ 3 người; lớn hơn cần [license](https://www.remotion.pro/license).
- edge-tts dùng dịch vụ đọc của Microsoft Edge (cần mạng, không chính thức) — đủ cho làm nội dung, nhưng có thể đổi sang provider khác trong `/video-voice`.

## Dùng từ app Claude trên điện thoại

1. Push repo lên GitHub, cài Claude GitHub App cho repo (https://github.com/apps/claude).
2. Trên claude.ai/code → Cloud environment → **Network access**: chọn **Custom**, tick *Also include default list*, thêm:
   ```
   speech.platform.bing.com
   cdn.jsdelivr.net
   ```
   (hoặc chọn **Full**). Không có 2 domain này thì giọng đọc edge-tts và HyperFrames sẽ lỗi.
3. (Tuỳ chọn, cho session khởi động nhanh) dán vào **Setup script** của environment:
   ```bash
   apt-get update && apt-get install -y ffmpeg fonts-noto-core libnss3 libgbm1 libxkbcommon0 libasound2t64
   pip install -U edge-tts
   ```
4. App Claude → tab **Code** → chọn repo → chat: *"làm video 9:16 dài 30 giây về …"*.
   Claude tự chạy `scripts/cloud-setup.sh` nếu thiếu tool, gửi kịch bản để bạn duyệt, rồi push MP4 lên một nhánh và gửi link GitHub để xem trên điện thoại.
