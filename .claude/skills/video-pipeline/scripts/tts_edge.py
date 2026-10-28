"""Tạo giọng đọc từng cảnh bằng edge-tts, kèm mốc thời gian từng từ.

  python tts_edge.py productions/<slug> [--force] [--only s01,s03] [--voice vi-VN-NamMinhNeural]

Ghi audio/voice/<id>.mp3 và audio/voice/<id>.words.json ([{text,start,end}] tính bằng giây).
"""
import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    sys.exit("Thiếu edge-tts: python -m pip install -U edge-tts")

TICKS = 10_000_000  # edge-tts dùng đơn vị 100ns


def communicate(text, voice, rate, pitch):
    # Dịch vụ trả "No audio was received" khi gửi rate và pitch cùng lúc, hoặc pitch khác 0:
    # chỉ gửi tham số khác mặc định, và ưu tiên rate.
    kw = {}
    if rate not in ("", "+0%"):
        kw["rate"] = rate
    elif pitch not in ("", "+0Hz"):
        kw["pitch"] = pitch
    try:
        return edge_tts.Communicate(text, voice, boundary="WordBoundary", **kw)
    except TypeError:  # edge-tts < 7 không có tham số boundary, mặc định đã là WordBoundary
        return edge_tts.Communicate(text, voice, **kw)


async def synth(text, voice, rate, pitch, mp3_path):
    words = []
    with open(mp3_path, "wb") as f:
        async for chunk in communicate(text, voice, rate, pitch).stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / TICKS
                words.append({"text": chunk["text"], "start": round(start, 3),
                              "end": round(start + chunk["duration"] / TICKS, 3)})
    if not words:
        print(f"  warn: {mp3_path.name} không có WordBoundary; phụ đề sẽ chia đều theo thời lượng")
    return words


async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("production")
    p.add_argument("--force", action="store_true")
    p.add_argument("--only", default="")
    p.add_argument("--voice", help="ghi đè voice.name trong script.json")
    args = p.parse_args()

    base = Path(args.production)
    script = json.loads((base / "script.json").read_text(encoding="utf-8"))
    vcfg = script.get("voice", {})
    voice = args.voice or vcfg.get("name") or "vi-VN-HoaiMyNeural"
    rate, pitch = vcfg.get("rate", "+0%"), vcfg.get("pitch", "+0Hz")
    only = {s for s in args.only.split(",") if s}

    out = base / "audio" / "voice"
    out.mkdir(parents=True, exist_ok=True)
    cache_path = out / ".tts-cache.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

    made = skipped = 0
    for scene in script["scenes"]:
        sid, text = scene["id"], (scene.get("narration") or "").strip()
        if not text or (only and sid not in only):
            continue
        key = hashlib.sha1(f"{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()
        mp3 = out / f"{sid}.mp3"
        if not args.force and cache.get(sid) == key and mp3.exists():
            skipped += 1
            continue
        print(f"tts {sid} ({voice}): {text[:60]}")
        # Dịch vụ hay lỗi ngẫu nhiên khi có rate/pitch: thử 3 lần, sau đó đọc ở tốc độ mặc định.
        plan = [(rate, pitch)] * 3 + [("+0%", "+0Hz")] * 2
        for attempt, (r, pt) in enumerate(plan):
            try:
                words = await synth(text, voice, r, pt, mp3)
                if (r, pt) != (rate, pitch):
                    print(f"  warn: {sid} đọc ở tốc độ mặc định vì edge-tts từ chối rate={rate} pitch={pitch}")
                break
            except Exception as exc:  # noqa: BLE001 - dịch vụ thỉnh thoảng lỗi tạm thời
                if attempt == len(plan) - 1:
                    sys.exit(f"edge-tts lỗi ở {sid}: {exc}. Kiểm tra mạng hoặc đổi giọng.")
                await asyncio.sleep(1.5 * (attempt + 1))
        (out / f"{sid}.words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
        cache[sid] = key
        cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        made += 1
    print(f"done: {made} tạo mới, {skipped} dùng lại cache -> {out}")


if __name__ == "__main__":
    asyncio.run(main())
