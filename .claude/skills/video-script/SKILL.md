---
name: video-script
description: Viết kịch bản video dạng bảng cảnh (lời thoại + chữ trên màn hình + mô tả hình) và xuất script.json cho pipeline. Dùng ở bước 2 của /video-pipeline, hoặc khi người dùng nhờ "viết kịch bản video", "lên kịch bản", "storyboard", "sửa lời thoại".
---

# Kịch bản → `script.json`

Đầu vào: `productions/<slug>/brief.md`, `state.json`, tài liệu trong `source/`. Đầu ra: `productions/<slug>/script.json`.

## Cách viết

1. **Đọc nguồn trước**: URL thì đọc trang; file thì đọc file. Số liệu, tên sản phẩm, giá… lấy từ nguồn, không bịa. Không có nguồn mà cần số liệu thì nói rõ là ví dụ minh hoạ.
2. **Cấu trúc**:
   - **Hook (0–3 s)**: một câu gây tò mò / nêu vấn đề / con số bất ngờ. Không mở đầu bằng "Xin chào các bạn".
   - **Thân**: 3–7 ý, mỗi ý 1 cảnh. Mỗi cảnh một ý duy nhất.
   - **Kết + CTA**: câu chốt và lời kêu gọi theo brief.
3. **Nhịp đọc**: tiếng Việt ~ 3.5–4 âm tiết/giây (≈ 150–170 từ/phút tiếng Anh). Ước lượng độ dài để khớp mục tiêu trong brief; mỗi cảnh 3–8 s cho video ngắn dọc, 5–15 s cho video ngang giải thích.
4. **Viết cho tai nghe**: câu ngắn, không viết tắt, số viết thành chữ khi cần đọc đúng ("2024" → "hai không hai bốn" chỉ khi TTS đọc sai; thử trước). Không đưa ký hiệu/emoji vào `narration`.
5. **Chữ trên màn hình** (`onscreen`) ngắn hơn lời đọc: tiêu đề 2–6 từ, không chép nguyên câu thoại (phụ đề đã làm việc đó).
6. **Hình** (`visual`): mô tả cụ thể cái gì xuất hiện và chuyển động thế nào — "biểu đồ cột 3 cột tăng dần, cột cuối đỏ nổi bật", không phải "hình minh hoạ đẹp". Ghi nguồn hình trong `assets` (ảnh người dùng, logo, icon, ảnh cần tìm, hay vẽ bằng code).
7. Video không có giọng đọc (chỉ nhạc + chữ): để `narration` rỗng và đặt `duration` cho từng cảnh.

## Schema

```json
{
  "title": "…",
  "lang": "vi",
  "voice": { "provider": "auto", "name": "vi-VN-HoaiMyNeural", "rate": "+0%" },
  "style": {
    "palette": ["#0B1020", "#F5F7FF", "#FF5A36"],
    "font": "Be Vietnam Pro",
    "mood": "năng động, hiện đại",
    "music": "lofi nhẹ, 90 bpm"
  },
  "scenes": [
    {
      "id": "s01",
      "narration": "Câu đọc của cảnh này.",
      "onscreen": "Tiêu đề ngắn",
      "visual": "Mô tả hình và chuyển động.",
      "assets": ["logo: source/logo.svg", "icon: rocket"],
      "sfx": ["whoosh"],
      "transition": "cut",
      "duration": null
    }
  ]
}
```

- `id` dạng `s01`, `s02`… — dùng làm tên file giọng và id cảnh khi dựng.
- `duration`: để `null` khi có giọng đọc (bước voice tự tính); điền số giây khi cảnh không có lời.
- `voice.provider`: để `auto` (bước voice tự chọn edge → google → piper theo mạng). `voice.name` là giọng edge; provider khác tự dùng giọng mặc định của nó.
- `voice` mặc định theo ngôn ngữ: `vi` → edge `vi-VN-HoaiMyNeural` (nữ) / `vi-VN-NamMinhNeural` (nam); `en` → edge `en-US-AndrewMultilingualNeural` / `en-US-AvaMultilingualNeural`. Provider khác xem `/video-voice`.
- Font tiếng Việt phải có đủ dấu: Be Vietnam Pro, Inter, Montserrat, Roboto, Noto Sans (đều có trên Google Fonts — tải file về project khi dựng).

## Duyệt

Gửi người dùng bảng tóm tắt: `# | lời thoại | chữ trên màn hình | hình`, kèm tổng thời lượng ước tính. Chờ duyệt trừ khi `state.json` có `"auto": true`. Xong: `production.py done <slug> script`.
