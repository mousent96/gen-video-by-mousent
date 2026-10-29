---
name: video-voice
description: Tạo giọng đọc (TTS) cho từng cảnh từ script.json, đo thời lượng, dựng timeline.json và phụ đề captions.srt có mốc từng từ. Tiếng Việt miễn phí qua edge-tts, Google TTS hoặc Piper offline (tự chọn theo mạng), Kokoro (tiếng Anh), HeyGen/ElevenLabs (trả phí), hoặc file thu âm sẵn. Dùng ở bước 3 của /video-pipeline hoặc khi người dùng nhờ "tạo giọng đọc", "voiceover", "lồng tiếng", "đổi giọng", "làm phụ đề".
---

# Giọng đọc + timeline

Đầu vào: `script.json`. Đầu ra: `audio/voice/<scene>.mp3`, `audio/voice/<scene>.words.json`, `timeline.json`, `captions.srt`.

## 1. Tạo giọng

```bash
python .claude/skills/video-pipeline/scripts/tts.py productions/<slug> [--provider auto|edge|google|piper]
```

Ba provider miễn phí có tiếng Việt; `auto` (mặc định) chọn edge, không được thì google:

| Provider | Chất lượng | Cần | Mốc từ |
| --- | --- | --- | --- |
| `edge` | tự nhiên nhất (giọng Neural HoaiMy/NamMinh), Whisper nghe lại gần đúng hết | mạng tới `speech.platform.bing.com` — **bị chặn** trong cloud session mạng mặc định | chính xác từng từ |
| `google` | rõ, hơi máy; Whisper nghe lại đúng từng chữ | mạng tới `translate.googleapis.com` (được phép trong cloud mặc định), ffmpeg | chính xác từng câu, chia trong câu theo độ dài chữ |
| `piper` (không vào auto) | **phát âm sai nhiều** ("video ngắn" → "bên yêu nắng"), 16 kHz — chỉ khi hoàn toàn không có mạng | `pip install piper-tts`; model tải 1 lần từ GitHub releases (~58 MB) | như google |

- Script ghi provider/giọng thực tế vào `script.json`; báo người dùng provider nào đã dùng. Khi `auto` không chọn được edge (cloud), nói rõ giọng đang là Google và edge cần mở mạng `speech.platform.bing.com`.
- Đọc `voice.name`, `voice.rate` từ `script.json`; chỉ tạo lại cảnh có lời thoại đổi (cache theo hash). `--force` để tạo lại hết, `--only s03,s05` cho vài cảnh. `rate` (ví dụ `+10%`) dùng được cho cả 3 provider.
- Dịch vụ edge-tts hay từ chối ngẫu nhiên khi có `rate`/`pitch` ("No audio was received"): script thử lại 3 lần rồi đọc ở tốc độ mặc định và in `warn`. Chỉ dùng `rate` (ví dụ `+10%`), tránh `pitch`. Thấy `warn` thì báo người dùng.
- Liệt kê giọng: `python -m edge_tts --list-voices | findstr vi-VN` (PowerShell) hoặc `| grep vi-VN`.
- Nghe thử 1 câu trước khi chạy cả kịch bản nếu người dùng kén giọng.
- Đọc sai từ (tên riêng, viết tắt, số): sửa chính tả trong `narration` theo cách đọc (ví dụ "AI" → "Ây Ai"), chạy lại cảnh đó.

**Provider khác** (tạo file `audio/voice/<scene>.mp3|wav` cho mỗi cảnh, rồi lấy mốc từ bằng transcribe):

| Provider | Lệnh | Ghi chú |
| --- | --- | --- |
| Kokoro (offline, EN/ES/FR/JA/ZH… — **không có tiếng Việt**) | `npx hyperframes tts "<câu>" -o audio/voice/s01.wav` | cần `kokoro-onnx` |
| HeyGen (trả phí, có mốc từ) | xem `hyperframes/skills/media-use/audio/references/tts.md` | hỏi trước khi dùng |
| ElevenLabs (trả phí) | `hyperframes/skills/media-use/audio/references/tts.md`, hoặc package `remotion/packages/elevenlabs` | cần `ELEVENLABS_API_KEY` |
| Thu âm của người dùng | đặt file theo tên cảnh, hoặc 1 file dài rồi cắt | |

Lấy mốc từ cho file không có sẵn (bắt buộc ghi `--model` và `--language`, model `.en` sẽ dịch sang tiếng Anh):

```bash
npx hyperframes transcribe productions/<slug>/audio/voice/s01.mp3 --model small --language vi
```

Đổi kết quả sang `s01.words.json` dạng `[{"text": "...", "start": 0.12, "end": 0.40}, …]` (giây, tương đối trong file).

## 2. Dựng timeline

```bash
python .claude/skills/video-pipeline/scripts/build_timeline.py productions/<slug> --lead 0.3 --tail 0.5
```

- Mỗi cảnh = `lead` + độ dài giọng (ffprobe) + `tail`; cảnh không lời dùng `duration` trong script.
- Ghi `timeline.json`: `fps`, `width`, `height`, `total_duration`, `total_frames`, và mỗi cảnh `start`, `duration`, `start_frame`, `duration_frames`, `voice` (đường dẫn), `voice_offset` (giây trong cảnh), `words` (mốc tuyệt đối); cộng mảng `captions` (cụm 3–7 từ, ngắt theo dấu câu) và `captions.srt`.
- `--max-words N` / `--max-chars N` chỉnh độ dài mỗi cụm phụ đề (video dọc nên ngắn: `--max-chars 28`).

## 3. Kiểm tra

- In ra tổng thời lượng; so với mục tiêu trong brief. Lệch > 20% → báo người dùng, đề xuất cắt/thêm câu, hoặc đổi `rate` (ví dụ `+10%`).
- Nghe ít nhất cảnh đầu và cảnh có tên riêng (mở file mp3 cho người dùng nếu cần duyệt).

Xong: `production.py done <slug> voice`. Đổi lời thoại sau này → chạy lại cả mục 1 và 2, rồi cập nhật bản dựng.
