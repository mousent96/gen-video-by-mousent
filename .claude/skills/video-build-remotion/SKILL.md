---
name: video-build-remotion
description: Dựng video bằng Remotion (React/TSX) từ timeline.json của pipeline - tạo project, sinh composition có giọng/nhạc/phụ đề đúng frame, thiết kế từng cảnh, mở Remotion Studio. Dùng ở bước 5 của /video-pipeline khi engine là remotion, hoặc khi người dùng muốn sửa cảnh trong video Remotion của pipeline.
---

# Dựng bằng Remotion

**Đọc trước**: `remotion/packages/skills/skills/remotion-best-practices/SKILL.md` (router), `remotion-create/SKILL.md`, `remotion-create/video-layout.md`, `remotion-markup/SKILL.md`. Khi cần: `remotion-markup/animations` (trong SKILL.md), `transitions.md`, `sequencing.md`, `google-fonts.md`, `local-fonts.md`, `images.md`, `embedding-videos.md`, `remotion-captions/display-captions.md` — tất cả trong `remotion/packages/skills/skills/`.

Đầu vào: `timeline.json`, `script.json`, `assets.json`. Đầu ra: `productions/<slug>/project/`.

## 1. Tạo project (lần đầu)

```bash
npx create-video@latest --yes --blank --no-tailwind productions/<slug>/project
cd productions/<slug>/project
npm i
npx remotion add @remotion/media
```

Thêm khi cần: `npx remotion add @remotion/google-fonts @remotion/transitions`.

## 2. Sinh composition từ timeline

```bash
python .claude/skills/video-pipeline/scripts/scaffold_remotion.py productions/<slug>
```

Sinh `src/pipeline/Pipeline.tsx` (composition `Main`: mỗi cảnh một `<Sequence>` đúng frame, giọng đọc lệch `voice_offset`, nhạc nền, SFX), `src/pipeline/data.ts`, `src/pipeline/Captions.tsx`, `src/scenes/S01.tsx…` (stub — chỉ tạo khi chưa có), thay `Root.tsx` blank. Media được chép vào `public/` và gọi bằng `staticFile()`. Chạy lại an toàn sau khi đổi giọng/timeline.

## 3. Thiết kế từng cảnh

Sửa `src/scenes/<Sxx>.tsx` theo `visual` + `onscreen` của cảnh trong `script.json`:

- Mọi chuyển động dựa trên `useCurrentFrame()` + `interpolate`/`spring` — không dùng CSS transition/animation, `setTimeout`, `Math.random()` không seed.
- `useCurrentFrame()` trong cảnh tính từ đầu cảnh; prop `words` có mốc giây tính từ đầu cảnh → `frame = Math.round(word.start * fps)` để phần tử xuất hiện đúng lúc từ khoá được đọc.
- Font tiếng Việt: `@remotion/google-fonts/<Font>` với `subsets: ['vietnamese', 'latin']`, hoặc file trong `public/fonts` (`local-fonts.md`). Stub chỉ ghi tên font, chưa nạp — chưa nạp thì video rơi về font mặc định của Chrome; nạp font trong `Root.tsx` hoặc từng cảnh, kể cả cho `Captions`.
- Ảnh: `<Img src={staticFile('images/…')} />`; video: `<Video>` từ `@remotion/media`.
- Bố cục theo `remotion-create/video-layout.md`: chữ lớn, vùng an toàn, chừa 1/5 dưới cho phụ đề (dọc: ~600–700 px từ đáy).

## 4. Kiểm tra

```bash
npx tsc --noEmit
npx remotion still Main out/check-s01.png --frame=<giữa cảnh 1>
```

Render still giữa mỗi cảnh (`start_frame + duration_frames/2` trong `timeline.json`) và xem PNG: chữ tràn, đè phụ đề, mất dấu, cảnh trống → sửa.

## 5. Preview

```bash
npx remotion studio --no-open
```

Chạy nền, mở URL in ra (thêm `/Main`) trong browser pane, đưa người dùng link. Chờ duyệt trừ khi `"auto": true`. Đổi lời thoại → `/video-voice` rồi chạy lại bước 2. Xong: `production.py done <slug> build`.
