---
name: video-build-hyperframes
description: Dựng video bằng HyperFrames (HTML + GSAP) từ timeline.json của pipeline - sinh project, thiết kế từng cảnh, phụ đề, nhạc, kiểm tra bằng check/snapshot và mở preview. Dùng ở bước 5 của /video-pipeline khi engine là hyperframes, hoặc khi người dùng muốn sửa hình/chuyển động của một cảnh trong video HyperFrames.
---

# Dựng bằng HyperFrames

**Đọc trước** (bắt buộc lần đầu trong phiên): `hyperframes/skills/hyperframes/SKILL.md` (render contract — 12 luật) và `hyperframes/skills/hyperframes-cli/SKILL.md`. Khi cần: `references/motion.md`, `references/captions.md`, `references/format.md`, và file theo loại video trong `references/types/` (explainer, launch, vertical, data…) — tất cả nằm trong `hyperframes/skills/hyperframes/`.

Đầu vào: `timeline.json`, `script.json`, `assets.json`. Đầu ra: `productions/<slug>/project/`.

## 1. Sinh khung project

```bash
python .claude/skills/video-pipeline/scripts/scaffold_hyperframes.py productions/<slug>
```

Tạo `project/index.html` (host cho mọi cảnh đặt đúng giây theo giọng đọc, `<audio>` giọng/nhạc/SFX), `compositions/captions.html` (phụ đề từ mốc từ), và `compositions/<sid>.html` cho cảnh chưa có. Chạy lại an toàn khi đổi giọng/timeline: chỉ ghi đè file còn dấu `GENERATED`, không đụng file cảnh đã thiết kế.

Video không cần phụ đề: thêm `--no-captions`.

## 2. Thiết kế từng cảnh

Mở `compositions/<sid>.html`, thay phần stub theo `visual` + `onscreen` của cảnh trong `script.json`:

- Mỗi cảnh: 1 ý chính, 1 điểm nhìn chính. Chữ to (tiêu đề ≥ 7% cạnh ngắn), tương phản cao, nằm trong vùng an toàn 90%; phụ đề đã chiếm 1/5 dưới khung (dọc: khoảng 600–700 px từ đáy) — đừng đặt nội dung chính đè lên.
- Chuyển động bám lời đọc: mốc từ trong `timeline.json` (`scenes[].words`, giây tuyệt đối) → trừ `start` của cảnh để ra thời điểm trong cảnh; cho phần tử xuất hiện đúng lúc từ khoá được đọc.
- Luôn `fromTo`, không `from`; id phần tử có tiền tố cảnh (`#s02-chart`); kết thúc trạng thái trước khi hết `data-duration`.
- Hiệu ứng/chuyển cảnh/kiểu phụ đề có sẵn: tìm trong registry trước (`npx hyperframes catalog --json`, skill `hyperframes/skills/hyperframes-registry/SKILL.md`), rồi `npx hyperframes add <name>`.
- Ảnh/logo: `assets/images/...`; footage: `<video muted>` trong cảnh; font ngoài bộ bundled cần `@font-face` tới `assets/fonts/...` (font phải có dấu tiếng Việt).
- Muốn đổi kiểu phụ đề: sửa `compositions/captions.html` sau khi xoá dòng `GENERATED` (từ đó script sẽ không ghi đè nó nữa).
- Ảnh tĩnh luôn kèm thêm một lớp chuyển động (warp sao, xoay, bay xuyên 3D); chuyển giữa các cấp độ thu phóng bằng một cảnh three.js liên tục thay vì cắt cảnh; đối tượng đích xuất hiện cùng cỡ với vật xung quanh rồi mới zoom tới. Chi tiết và các bẫy three.js (UMD r158 trong `<template>`, nền trong suốt, `setClearAlpha`, `RepeatWrapping`): `.claude/skills/video-pipeline/references/kinh-nghiem.md` mục 1, 2, 5.

## 3. Kiểm tra (bắt buộc trước khi báo xong)

Chạy trong `productions/<slug>/project`:

```bash
npx hyperframes lint
npx hyperframes check --json
npx hyperframes snapshot --at 1,5,10
```

- Sửa mọi lỗi `check`; cân nhắc mọi warning (contrast có `suggestedColor`).
- Snapshot ít nhất 1 khung giữa mỗi cảnh và đọc các PNG trong `.hyperframes/artifacts/snapshots/` — đó là cách duy nhất để "nhìn" video. Chữ tràn, chồng lên phụ đề, cảnh trống, font mất dấu → sửa.
- Video > 15 s: `npx hyperframes snapshot --review` và làm theo `hyperframes/skills/hyperframes/references/review.md`.

## 4. Preview

```bash
npx hyperframes preview --background
```

Đưa người dùng URL preview (mở trong browser pane nếu có), nói họ có thể chỉnh trực tiếp trong HyperFrames desktop app/Studio. Chờ duyệt, trừ khi `state.json` có `"auto": true`.

Sửa theo góp ý: đổi chữ/hình → sửa file cảnh; đổi lời thoại → `/video-voice` rồi chạy lại scaffold; dời/cắt clip → `npx hyperframes timeline …` (xem hyperframes-cli). Xong: `production.py done <slug> build`.
