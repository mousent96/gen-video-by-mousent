---
name: video-assets
description: Gom media cho video theo script.json - nhạc nền, hiệu ứng âm thanh, ảnh, icon, logo, footage, ảnh chụp website - tải về thư mục production và ghi assets.json. Dùng ở bước 4 của /video-pipeline hoặc khi người dùng nhờ "tìm nhạc nền", "thêm sfx", "tìm ảnh", "lấy logo" cho video.
---

# Media cho video

Đầu vào: `script.json` (trường `assets`, `sfx`, `style.music`), `source/`. Đầu ra: file trong `audio/`, `images/`, `video/` và `assets.json`.

Công cụ chính là resolver của HyperFrames (dùng được cho cả 2 engine vì nó chỉ tải file về). Đọc `hyperframes/skills/media-use/SKILL.md` và `hyperframes/skills/media-use/references/resolve.md` trước khi dùng lần đầu.

```bash
npx hyperframes media-use resolve --doctor                       # xem provider nào dùng được
npx hyperframes media-use resolve --type <type> --intent "<mô tả>" --project productions/<slug>
```

`<type>`: `bgm`, `sfx`, `image`, `icon`, `logo`, `voice`, `video`. Lệnh in `resolved <id> → <path>`; file nằm trong `productions/<slug>/assets/` — chuyển/sao chép vào đúng thư mục (`audio/`, `images/`, `video/`).

## Theo loại

| Cần | Thứ tự ưu tiên |
| --- | --- |
| **Ảnh/logo/footage của người dùng** | luôn ưu tiên — có trong `source/` hoặc người dùng gửi |
| **Logo thương hiệu** | `resolve --type logo` (theSVG, GitHub avatar, favicon); không tự vẽ lại logo |
| **Website / sản phẩm thật** | `npx hyperframes capture <url> --json` (ảnh chụp + màu + font của trang) |
| **Icon** | `resolve --type icon`; hoặc SVG từ bộ icon mở (Lucide, Tabler) tải về `images/icons/`; không dùng emoji thay icon |
| **Nhạc nền** | `resolve --type bgm` (HeyGen catalog nếu đã đăng nhập; MusicGen nếu đã cài); nếu không có thì hỏi người dùng gửi file nhạc có bản quyền, hoặc làm không nhạc |
| **SFX** (whoosh, pop, click…) | `resolve --type sfx` (21 SFX có sẵn offline + Openverse) |
| **Ảnh minh hoạ chung** | ưu tiên vẽ bằng HTML/SVG/CSS ngay trong bản dựng (biểu đồ, sơ đồ, chữ động, hình khối); ảnh stock/AI chỉ khi người dùng muốn và có provider |
| **Avatar người dẫn / giọng HeyGen** | trả phí — hỏi trước; công thức trong `hyperframes/skills/media-use/references/operations.md` |

**Cloud session mạng mặc định** (`CLAUDE_CODE_REMOTE=true`): theSVG (jsdelivr), Openverse và HeyGen bị chặn. Dùng 21 SFX có sẵn offline (`resolve --type sfx --local-only`), logo từ GitHub avatar / favicon hoặc file người dùng commit vào `productions/<slug>/source/`, icon SVG lấy từ npm (`npm pack lucide-static` rồi lấy file trong `icons/`). Không có nhạc nền thì làm không nhạc và nói rõ.

## `assets.json`

```json
{
  "bgm": { "path": "audio/bgm.mp3", "license": "…", "credit": "…", "gain_db": -18 },
  "sfx": [{ "scene": "s02", "name": "whoosh", "path": "audio/sfx/whoosh.wav", "at": 0.0 }],
  "images": [{ "scene": "s01", "role": "logo", "path": "images/logo.svg" }],
  "fonts": [{ "family": "Be Vietnam Pro", "path": "fonts/BeVietnamPro-Bold.ttf" }]
}
```

`at` là giây tính từ đầu cảnh. Ghi license/credit cho mọi file CC BY để đưa vào mô tả video.

## Quy tắc

- Mọi file phải nằm local trong production; bản dựng không được load URL ngoài.
- Font: tải `.ttf`/`.woff2` (Google Fonts) về `fonts/` — font phải có đủ dấu tiếng Việt.
- Nhạc nền nằm dưới giọng đọc: khoảng −18 đến −24 dB so với giọng, hoặc duck khi có lời (`hyperframes/skills/media-use/references/mixing.md`).
- Thiếu media quan trọng (logo, ảnh sản phẩm) → hỏi người dùng một lần, liệt kê đúng thứ cần; không có thì làm bản thay thế bằng chữ/hình khối và ghi vào brief phần "Giả định".

Xong: `production.py done <slug> assets`.
