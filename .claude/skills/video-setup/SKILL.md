---
name: video-setup
description: Kiểm tra và cài môi trường cho pipeline video trên Windows (Node, FFmpeg, Python, edge-tts, Chrome cho HyperFrames, whisper). Dùng lần đầu dùng /video-pipeline, khi lệnh báo thiếu ffmpeg/ffprobe/Chrome/edge-tts, hoặc khi người dùng nói "cài đặt", "setup môi trường", "kiểm tra máy".
---

# Setup môi trường

Chạy kiểm tra:

```bash
python .claude/skills/video-pipeline/scripts/check_env.py
```

Mỗi dòng `MISSING` kèm lệnh cài. Bảng đầy đủ:

| Tool | Cần cho | Cài trên Windows |
| --- | --- | --- |
| Node.js 22+ | cả 2 engine | `winget install OpenJS.NodeJS.LTS` |
| FFmpeg + ffprobe | HyperFrames render/tts/transcribe, đo độ dài audio | `winget install Gyan.FFmpeg` rồi **mở terminal mới** để PATH cập nhật |
| Python 3.10+ | script của pipeline, edge-tts | `winget install Python.Python.3.12` |
| VieNeu-TTS | giọng đọc tiếng Việt mặc định, chạy local | `python -m pip install --no-deps vieneu==3.8.3` rồi `python -m pip install -r scripts/requirements-vieneu.txt` (model ~580 MB tự tải lần đầu) |
| edge-tts | giọng dự phòng (có tiếng Việt), kèm mốc thời gian từng từ | `python -m pip install -U edge-tts` |
| Chrome headless (HyperFrames) | render HyperFrames | `npx hyperframes browser ensure` |
| kokoro-onnx (tuỳ chọn) | giọng offline tiếng Anh qua `npx hyperframes tts` | `python -m pip install kokoro-onnx soundfile` |
| heygen CLI (tuỳ chọn, trả phí) | avatar, giọng HeyGen, nhạc catalog | xem `hyperframes/skills/media-use/references/setup-providers.md` |

Remotion tự tải Chrome Headless Shell và có ffmpeg đi kèm, không cần cài thêm.

## Repo upstream (submodule)

`hyperframes/` và `remotion/` là git submodule, ghim commit. Thư mục rỗng (clone mới, CI, Claude Code cloud) →

```bash
bash scripts/fetch-upstream.sh        # chỉ tải phần skill, ~20 s
git submodule update --init           # bản đầy đủ (remotion > 4 GB), chỉ khi cần đọc source
```

Cập nhật lên bản upstream mới: `git submodule update --remote <tên>` rồi commit con trỏ submodule; đọc lại SKILL.md upstream xem có đổi lệnh CLI không.

## Linux / GitHub Actions / Claude Code cloud

```bash
sudo apt-get install -y ffmpeg fonts-noto-core
python -m pip install -U edge-tts
npx hyperframes browser ensure
```

Trên GitHub Actions, composite action `.github/actions/setup-video-env` đã làm hết các bước trên — không cần chạy skill này.

## Quy tắc

- Cài bằng `winget`/`pip` cần người dùng đồng ý nếu chế độ quyền yêu cầu; nói rõ đang cài gì.
- Sau khi cài FFmpeg bằng winget mà `ffprobe` vẫn không thấy: tìm `ffprobe.exe` trong `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\**\bin` và thêm thư mục đó vào PATH của phiên hiện tại (`$env:Path += ";<dir>"`) — không sửa PATH hệ thống khi chưa hỏi.
- HyperFrames: `npx hyperframes doctor --json` (luôn exit 0, xem trường `.ok`).
- Không build 2 repo source `hyperframes/` và `remotion/`; dùng CLI bản npm.
- Chạy lại `check_env.py` đến khi các mục bắt buộc đều `OK`.
