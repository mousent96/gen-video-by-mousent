# Kinh nghiệm rút ra (video "Giới thiệu về vũ trụ", 12 vòng sửa)

Đọc file này trước khi dựng video khoa học/khám phá, video cần cảm giác "điện ảnh", hoặc khi người dùng gửi video mẫu.

## 1. Người dùng muốn gì khi nói "sống động", "giống video mẫu"

- **Hình thật, không phải hình vẽ.** Chữ to + hình vẽ code (v1) và hạt 3D tự vẽ (v2) đều bị chê "thô". Thứ người dùng chấp nhận là ảnh/tư liệu thật được làm chuyển động.
  - Ảnh vũ trụ: NASA Image Library, không cần key: `https://images-api.nasa.gov/search?q=<từ khoá>&media_type=image` → `https://images-api.nasa.gov/asset/<nasa_id>` → file `~orig.jpg` hoặc `~large.jpg`. Texture Trái Đất: NASA Visible Earth (Blue Marble, Black Marble). Ghi nguồn "NASA, ESA, CSA, STScI" trong mô tả.
  - Không lấy hình từ video mẫu của người khác. Chỉ học phong cách.
- **Ít chữ.** Bỏ phụ đề cháy hình khi người dùng chê nhiều chữ (`--no-captions`, giao `.srt` riêng). Chỉ giữ nhãn ngắn một dòng ("13,8 tỉ năm", "5%") hiện đúng lúc từ khoá được đọc.
- **Ảnh tĩnh phải luôn chuyển động.** Ken Burns (zoom/pan) là chưa đủ; ảnh vẫn bị coi là "tĩnh". Cần thêm ít nhất một lớp chuyển động nữa:
  - vệt sao bay qua (warp) vẽ bằng canvas 2D, có tốc độ theo thời gian;
  - xoay thiên hà/ảnh, nghiêng 3D (CSS `perspective` hoặc three.js);
  - bay xuyên 3D: tách từng đối tượng ra khỏi ảnh (`scipy.ndimage.label` trên ngưỡng độ sáng → cắt ô → atlas JPG nền đen), rồi đặt hàng nghìn sprite ở các độ sâu khác nhau và cho camera bay qua.
- **Vật thể chính phải to, rõ, có chi tiết.** Trái Đất nhỏ bị chê. Dùng texture ≥ 4K, shader ngày/đêm (đèn thành phố), ánh biển, quầng khí quyển, mây trôi, camera áp sát đến khi vật thể chiếm 70–90% chiều cao khung.

## 2. Liên tục và nhất quán

- **Không cắt cảnh giữa các cấp độ thu phóng** (vũ trụ → thiên hà → hệ Mặt Trời → hành tinh). Làm một composition three.js duy nhất, camera đi liên tục kiểu "Powers of Ten":
  - Cùng một thế giới: đặt đối tượng đích sẵn trong cảnh rồi cho camera tiến tới.
  - Khác thang đo: dùng hai scene, render vào hai `WebGLRenderTarget` và trộn bằng một quad (`mix(a,b,k)`) trong lúc **cả hai camera cùng zoom theo một hướng**, với điểm đích nằm giữa khung ở cả hai scene.
  - Khoảng cách camera nội suy theo hàm mũ: `d0 * pow(d1/d0, e)`. Nội suy tuyến tính trông giật ở đầu hoặc cuối.
- **Đối tượng đích lúc xuất hiện phải cùng cỡ với vật xung quanh.** Lỗi người dùng chụp màn hình: Dải Ngân Hà hiện ra to đùng đè lên các thiên hà khác. Cách đúng: đặt sẵn nó, thu nhỏ, lệch khỏi tâm, giữa trường thiên hà; camera dừng cho khán giả nhìn cả trường, rồi mới zoom tới.
- **Với vật thể additive (`depthTest:false`), mọi thứ phía sau đều "xuyên" qua nó.** Không đặt sprite khác phía sau đối tượng chính.
- **Match cut giữa các cảnh rời.** Điểm kết của cảnh trước trùng với điểm bắt đầu của cảnh sau. Ví dụ: zoom vào ngôi sao sáng (transform-origin tại điểm sao, dịch điểm đó về tâm), ngôi sao co lại thành chấm, và chấm đó là điểm phát nổ của cảnh sau.
- **Hiện tượng sau mọc ra từ hiện tượng trước.** Ví dụ: thiên hà "lóe" ra lần lượt ngay giữa làn hạt của vụ nổ. Đừng chèn ảnh không liên quan vào giữa (ảnh tinh vân Carina làm đứt mạch).
- **Kết khép vòng.** Cảnh cuối phản chiếu cảnh đầu (lao vào ngôi sao ↔ lùi ra từ ngôi sao). Đoạn cuối đi ngược hành trình (Trái Đất → hệ Mặt Trời → thiên hà → vũ trụ).

## 3. Kịch bản

- Mỗi câu phải nối ý với câu trước. Khi người dùng thấy "không ăn khớp", thường cần **câu bắc cầu** ("Từ hành tinh nhỏ bé ấy, con người đã nhìn ra tận rìa vũ trụ…"), không chỉ sửa hình.
- Đổi lời một cảnh: `tts.py <prod> --only <sid>`, rồi `build_timeline.py` với **đúng `--lead/--tail` đã dùng lần đầu** (xem `voice_offset` trong `timeline.json` cũ; video này là 0.5/1.0). Dùng tham số mặc định thì mọi mốc thời gian của các cảnh khác bị lệch.
- Sau đó chép wav mới vào `project/assets/audio/voice/`, sửa `data-duration` của thẻ audio, và dời `data-start` của các cảnh/lời đọc phía sau.

## 4. Âm thanh

- SFX phải gắn với khoảnh khắc của nó. Tiếng whoosh đặt ở đầu cảnh mở đầu bị chê "không ăn khớp". Đo đỉnh RMS của file SFX (numpy, cửa sổ 0,1 s) rồi đặt `data-start = mốc − thời điểm đỉnh`. Một tiếng nổ trầm tự tạo bằng `aevalsrc` + brown noise lowpass hợp với "Big Bang".
- Nhạc nền có bản quyền: không tự tải. Nhận file từ người dùng và cảnh báo về Content ID trên YouTube.
- **Chỉ đổi nhạc/âm lượng thì không render lại hình.** Dùng `scripts/remix_audio.py`: đọc thẻ `<audio>` trong `index.html`, lặp nhạc có crossfade, ducking bằng `sidechaincompress` theo lời đọc, ghép bằng `-c:v copy`. Mất vài giây thay vì 25 phút.

## 5. Kỹ thuật HyperFrames + three.js

- three.js: dùng bản UMD `three@0.158.0/build/three.min.js` (từ r160 không còn UMD). Cloud session chặn jsdelivr/unpkg: tải `https://registry.npmjs.org/three/-/three-0.158.0.tgz`, lấy `package/build/three.min.js` vào `assets/vendor/` (giống cách scaffold làm với GSAP). Thẻ `<script>` phải nằm **trong `<template>` của composition**, nếu không lint báo `missing_three_script`.
- `WebGLRenderer({preserveDrawingBuffer:true})`. Vẽ trong `onUpdate` của một tween GSAP trên biến proxy (`tl.to(proxy,{t:D,duration:D,ease:'none',onUpdate:draw})`), không dựa vào `hf-seek`.
- Composition phủ lên trên mà cần nhìn xuyên xuống lớp dưới, cần đủ ba thứ: `#root{background:transparent}` (CSS chung đặt `#root` màu đen), `alpha:true`, và `setClearColor(0,0)`.
  - Khi không còn cần trong suốt, bật lại `setClearAlpha(1)`. Nếu không, các sprite additive (quầng Mặt Trời) bị cắt thành hình vuông.
- Texture có dịch UV (mây trôi) phải đặt `wrapS = RepeatWrapping`, nếu không sẽ thành sọc kéo dài.
- Ảnh nền đen (Mặt Trời SDO, thiên hà): dùng `mix-blend-mode:screen` (DOM) hoặc `AdditiveBlending` (WebGL) để không lộ khung chữ nhật.
- Shader dạng `pow(1.0-dot(n,v), k)`: bọc bằng `clamp(…,0.0,1.0)` (lint `shader_unbounded_cosine_pow`).
- Lớp phủ toàn khung (flash): đặt `opacity:0` trong CSS (lint `gsap_fullscreen_overlay_starts_visible`).
- Lớp sao nền hình chữ nhật đặt xa sẽ hiện thành một khối chữ nhật giữa khung. Rải sao trên **mặt cầu** quanh camera.
- Tìm toạ độ điểm quan tâm trên ảnh (mặt trời, thiên hà cần zoom): vẽ lưới 10×10 lên bản thu nhỏ rồi xem, sau đó mới đặt `transform-origin`.
- Luôn chạy `snapshot --at …` dày ở các điểm chuyển cảnh và xem contact sheet **trước** khi render. Phần lớn lỗi trong video này (khung đen, khối chữ nhật, vật đè nhau) đều thấy được ở snapshot.

## 6. Render trong sandbox chat (1 CPU, mỗi lệnh tối đa khoảng 5 phút)

- Tiến trình chạy nền bị hủy khi lệnh tool kết thúc. Cách chạy ổn định là chạy foreground có `timeout` nhỏ hơn giới hạn tool, chia đoạn và resume, rồi lặp lệnh đến khi `EXIT 0`:

  ```bash
  tail -f /dev/null | HF_SEGMENTED_CAPTURE=true HF_SEGMENT_FRAMES=120 timeout 265 \
    npx hyperframes render --quality standard --resume --output ../output/<slug>.mp4
  ```

  - `tail -f /dev/null |` giữ stdin mở. CLI tự hủy (`render_cancelled_parent_exited`) khi stdin bị đóng (`< /dev/null`).
  - Chọn `HF_SEGMENT_FRAMES` ngay từ đầu. Đổi giá trị này hoặc sửa nội dung đều tạo `planHash` mới, và mọi đoạn phải render lại.
  - Đoạn nào không xong trong một lượt thì không bao giờ xong. Giảm kích thước đoạn hoặc làm nhẹ cảnh: nhiều sprite additive cỡ lớn phủ kín màn hình rất tốn với SwiftShader. Ít sprite to hơn cho hình tương đương mà nhanh gấp nhiều lần.
- Đừng dùng `pgrep -f "hyperframes render"` để kiểm tra, vì nó khớp với chính lệnh shell đang chạy.
- MP4 xuất ra khá nặng (80–100 MB/phút vì nhiều sao/hạt). Nén lại trước khi giao: `ffmpeg -c:v libx264 -preset veryfast -crf 21 -c:a copy -movflags +faststart`.
- Tốc độ tham khảo: khoảng 6 fps với cảnh DOM/ảnh, khoảng 1–2 fps với cảnh WebGL nặng. Một vòng "sửa → snapshot → render 60 s" mất khoảng 25–30 phút, nên **gom nhiều góp ý rồi mới render**.

## 7. Làm việc với người dùng

- Mỗi vòng chỉ sửa đúng điều người dùng nêu. Ghi rõ đã đổi gì và giữ gì.
- Khi tin nhắn bị cắt hoặc mơ hồ, làm phần đã rõ và hỏi lại phần còn thiếu trong cùng lượt.
- Khi phải chọn khổ hình (9:16 hay 16:9), hỏi trước khi dựng lại, vì đổi khổ là dựng lại toàn bộ bố cục.
- Đặt tên bản giao theo phiên bản (`<slug>-v3.mp4`, `-v4`, …) để người dùng so sánh và nói "bản trước tốt hơn ở chỗ X".
