---
name: video-pipeline
description: Tự động làm video từ A→Z trong workspace Gen-video (HyperFrames hoặc Remotion) - từ chủ đề/ý tưởng → kịch bản → giọng đọc → ảnh/nhạc → dựng → kiểm tra → render MP4. Dùng khi người dùng nói "làm video", "gen video", "tạo video về...", "make a video", "tiếp tục video", hoặc gọi /video-pipeline. Đây là skill điều phối, các bước chi tiết nằm ở các skill video-*.
---

# Video pipeline A→Z

Workspace có 2 engine, mỗi engine kèm bộ skill gốc của nó (đọc khi cần chi tiết):

| Engine | Khi nào chọn | Skill gốc (đường dẫn từ gốc workspace) |
| --- | --- | --- |
| **HyperFrames** (mặc định) | HTML + GSAP, CLI có sẵn check/snapshot/tts/transcribe/media, hợp agent tự chạy | `hyperframes/skills/hyperframes/SKILL.md`, `hyperframes/skills/hyperframes-cli/SKILL.md`, `hyperframes/skills/media-use/SKILL.md` |
| **Remotion** | Người dùng muốn React/TSX, cần component React, hoặc dự án đã là Remotion | `remotion/packages/skills/skills/remotion-best-practices/SKILL.md` và các thư mục `remotion-*` cạnh nó |

Hai thư mục `hyperframes/` và `remotion/` là **source repo** — không sửa, không build chúng. Video được làm trong `productions/<slug>/`, chạy CLI bản npm (`npx hyperframes`, `npx remotion`).

## Các bước

| # | Bước | Skill | Đầu ra (trong `productions/<slug>/`) |
| --- | --- | --- | --- |
| 0 | Môi trường | `/video-setup` | (chỉ chạy lần đầu hoặc khi lệnh báo thiếu tool) |
| 1 | Brief | skill này | `brief.md`, `state.json` |
| 2 | Kịch bản | `/video-script` | `script.json` |
| 3 | Giọng đọc + timeline | `/video-voice` | `audio/voice/*.mp3`, `timeline.json`, `captions.srt` |
| 4 | Media (ảnh, nhạc, SFX, logo) | `/video-assets` | `audio/bgm.*`, `audio/sfx/*`, `images/*`, `assets.json` |
| 5 | Dựng | `/video-build-hyperframes` hoặc `/video-build-remotion` | `project/` |
| 6 | Render + giao | `/video-render` | `output/*.mp4`, `output/thumbnail.png` |

## Cách chạy

1. **Bắt đầu mới**: tạo thư mục production

   ```bash
   python .claude/skills/video-pipeline/scripts/production.py new "<tiêu đề>" --engine hyperframes --lang vi --format 16:9
   ```

   `--format`: `16:9` (1920×1080, YouTube), `9:16` (1080×1920, TikTok/Shorts/Reels), `1:1` (1080×1080). Mặc định ngôn ngữ theo người dùng (tiếng Việt → `vi`).

2. **Brief** — điền `brief.md`: chủ đề, khán giả, mục tiêu (bán hàng / giáo dục / giải trí), độ dài mục tiêu, nền tảng, giọng (nam/nữ, tốc độ), phong cách hình ảnh, CTA, tài liệu nguồn (URL, file). Thiếu thông tin thì tự chọn giá trị hợp lý và ghi rõ trong brief là "giả định"; chỉ hỏi khi một lựa chọn thay đổi hẳn sản phẩm (ví dụ: không rõ là video quảng cáo hay giáo dục).

3. **Chạy lần lượt bước 2→6**, mỗi bước đọc SKILL.md tương ứng rồi làm theo. Sau mỗi bước:

   ```bash
   python .claude/skills/video-pipeline/scripts/production.py done <slug> <bước>
   ```

   (`brief`, `script`, `voice`, `assets`, `build`, `render`)

4. **Tiếp tục video dở**: `python .claude/skills/video-pipeline/scripts/production.py status [<slug>]` cho biết bước tiếp theo.

## Điểm dừng (checkpoint)

Mặc định dừng lại cho người dùng duyệt ở **2 chỗ**:
- sau **kịch bản** (gửi bảng cảnh: lời thoại + hình), vì sửa kịch bản sau khi đã có giọng/dựng rất tốn;
- sau **dựng**, mở preview (HyperFrames Studio / Remotion Studio) trước khi render bản cuối.

Nếu người dùng nói "tự làm hết", "không cần hỏi", "auto" → ghi `"auto": true` vào `state.json` (lệnh `production.py new ... --auto`) và chạy thẳng đến file MP4, vẫn tự kiểm tra ở bước dựng và render.

## Quy tắc chung

- Mọi đường dẫn file media trong project là tương đối, nằm trong project; render không được tải gì từ mạng.
- Độ dài video do giọng đọc quyết định: `timeline.json` (bước 3) là nguồn sự thật cho thời điểm bắt đầu/độ dài từng cảnh. Đổi lời thoại → chạy lại bước 3 rồi cập nhật bước 5.
- Lỗi lệnh: đọc dòng `Fix:` / thông báo lỗi, sửa rồi chạy lại; thiếu tool → `/video-setup`.
- Chi phí: HeyGen/ElevenLabs/Gemini là dịch vụ trả phí hoặc cần tài khoản — chỉ dùng khi người dùng yêu cầu hoặc đồng ý. Đường miễn phí mặc định: edge-tts (giọng), Openverse/SFX có sẵn (âm thanh), ảnh tự vẽ bằng HTML/SVG hoặc ảnh người dùng cung cấp.
- Kết thúc: báo đường dẫn MP4, độ dài, độ phân giải, và những gì đã giả định.
