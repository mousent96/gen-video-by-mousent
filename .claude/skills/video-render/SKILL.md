---
name: video-render
description: Render video cuối của pipeline ra MP4 (HyperFrames hoặc Remotion), kiểm tra file (độ dài, độ phân giải, có tiếng), xuất thumbnail, phụ đề .srt và ghi chú giao hàng. Dùng ở bước 6 của /video-pipeline hoặc khi người dùng nói "render", "xuất video", "export mp4".
---

# Render + giao

Chỉ render bản cuối khi người dùng đã duyệt preview, hoặc họ yêu cầu file, hoặc `state.json` có `"auto": true`. Bản nháp để xem nhanh thì dùng chất lượng draft.

## 1. Render

**HyperFrames** (trong `productions/<slug>/project`):

```bash
npx hyperframes check --json
npx hyperframes render --quality delivery --output ../output/<slug>.mp4
```

`--quality draft` khi đang sửa; video dài hơn timeout của tool → chạy nền theo `hyperframes/skills/hyperframes-cli/SKILL.md` (mục Render where).

**Remotion** (trong `productions/<slug>/project`):

```bash
npx remotion render Main ../output/<slug>.mp4 --codec=h264 --crf=18
```

Video dài: chạy nền (`run_in_background`) rồi chờ thông báo, không poll liên tục. Xem thêm `remotion/packages/skills/skills/remotion-render/SKILL.md`.

## 2. Kiểm tra file

```bash
python .claude/skills/video-pipeline/scripts/verify_render.py productions/<slug> productions/<slug>/output/<slug>.mp4
```

Script so độ dài với `timeline.json` (lệch ≤ 1 frame + 0.1 s), kiểm tra độ phân giải, fps, có track audio, đo loudness (khi ffmpeg có filter `ebur128`), xuất `output/thumbnail.png` (đổi bằng `--thumb-at <giây>`), sao chép `captions.srt` sang `output/<slug>.srt`, và trích khung giữa mỗi cảnh vào `output/frames/<scene>.png`. Máy chưa cài FFmpeg thì script dùng ffmpeg đi kèm Remotion trong `project/node_modules` nếu có. Kết quả `FAIL` → sửa rồi render lại; không giao file lỗi.

Mở các PNG trong `output/frames/` để chắc video không đen/đứng hình, chữ không tràn, phụ đề không đè nội dung.

## 3. Phiên bản khác (tuỳ chọn, khi người dùng cần)

- **Định dạng khác** (16:9 → 9:16): không crop bừa — tạo production mới với `--format 9:16`, chép `script.json` + `audio/` + `assets.json`, chạy lại `build_timeline.py` + scaffold, rồi chỉnh bố cục từng cảnh cho khung dọc.
- **Phụ đề cứng tách riêng**: video đã có phụ đề trong hình; muốn bản không phụ đề thì scaffold với `--no-captions` và render file khác (`<slug>-nosub.mp4`), kèm `.srt` để upload.
- **Nhiều biến thể nội dung** (HyperFrames): `npx hyperframes render --batch rows.json --output "renders/{name}.mp4"`.

## 4. Giao

Trên cloud (`CLAUDE_CODE_REMOTE=true`, ví dụ người dùng dùng app điện thoại): commit + push MP4 lên nhánh hiện tại và gửi link GitHub — xem mục "Chạy trên cloud" trong `/video-pipeline`.

Báo người dùng: đường dẫn MP4 (`productions/<slug>/output/…`), thời lượng, độ phân giải, dung lượng, file `.srt`, thumbnail, credit nhạc/SFX (từ `assets.json`), và mọi "Giả định" trong `brief.md`. Gợi ý tiêu đề + mô tả + hashtag cho nền tảng trong brief nếu hợp. Xong: `production.py done <slug> render`.
