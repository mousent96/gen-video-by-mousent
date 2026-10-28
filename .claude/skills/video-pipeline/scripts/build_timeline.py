"""Dựng timeline.json + captions.srt từ script.json và file giọng từng cảnh.

  python build_timeline.py productions/<slug> [--lead 0.3] [--tail 0.5] [--max-words 7] [--max-chars 42]
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

AUDIO_EXT = (".mp3", ".wav", ".m4a")
PUNCT = ".,!?;:…"


def probe_duration(path):
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    out = subprocess.run([exe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return None


def even_words(text, duration):
    tokens = text.split()
    step = duration / max(len(tokens), 1)
    return [{"text": t, "start": round(i * step, 3), "end": round((i + 1) * step, 3)} for i, t in enumerate(tokens)]


def restore_punctuation(words, text):
    """TTS/transcribe thường bỏ dấu câu: lấy lại chữ gốc (kèm dấu) từ lời thoại theo thứ tự."""
    def norm(s):
        return "".join(ch for ch in s.lower() if ch.isalnum())

    tokens, ptr, out = text.split(), 0, []
    for w in words:
        word = dict(w)
        for j in range(ptr, min(ptr + 4, len(tokens))):
            if norm(tokens[j]) and norm(tokens[j]) == norm(w["text"]):
                word["text"], ptr = tokens[j], j + 1
                break
        out.append(word)
    return out


def group_captions(words, max_words, max_chars, gap=0.35):
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        text = " ".join(x["text"] for x in cur)
        nxt = words[i + 1] if i + 1 < len(words) else None
        pause = nxt is not None and nxt["start"] - w["end"] > gap
        too_long = nxt is not None and len(text) + 1 + len(nxt["text"]) > max_chars
        if nxt is None or pause or w["text"][-1:] in PUNCT or len(cur) >= max_words or too_long:
            # Một từ lẻ cuối câu ("giây?") nhập vào cụm trước cho khỏi đứng một mình.
            if len(cur) == 1 and groups and groups[-1]["text"][-1:] not in PUNCT and cur[0]["start"] - groups[-1]["end"] < gap:
                groups[-1].update(text=groups[-1]["text"] + " " + text, end=cur[0]["end"])
            else:
                groups.append({"text": text, "start": cur[0]["start"], "end": cur[-1]["end"]})
            cur = []
    return groups


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("production")
    p.add_argument("--lead", type=float, default=0.3, help="khoảng lặng trước lời đọc mỗi cảnh (s)")
    p.add_argument("--tail", type=float, default=0.5, help="khoảng lặng sau lời đọc mỗi cảnh (s)")
    p.add_argument("--max-words", type=int, default=7)
    p.add_argument("--max-chars", type=int, default=42)
    args = p.parse_args()

    base = Path(args.production)
    script = json.loads((base / "script.json").read_text(encoding="utf-8"))
    state = json.loads((base / "state.json").read_text(encoding="utf-8"))
    fmt = state["format"]
    fps = fmt["fps"]
    voice_dir = base / "audio" / "voice"

    scenes, captions, t = [], [], 0.0
    warned_probe = False
    for sc in script["scenes"]:
        sid, text = sc["id"], (sc.get("narration") or "").strip()
        entry = {"id": sid, "start": 0.0, "duration": 0.0, "voice": None, "voice_offset": 0.0,
                 "voice_duration": 0.0, "words": []}
        voice = next((voice_dir / f"{sid}{ext}" for ext in AUDIO_EXT if (voice_dir / f"{sid}{ext}").exists()), None)
        if text and voice:
            words_file = voice_dir / f"{sid}.words.json"
            words = json.loads(words_file.read_text(encoding="utf-8")) if words_file.exists() else []
            vdur = probe_duration(voice)
            if vdur is None:
                if not warned_probe:
                    print("warn: không có ffprobe, ước lượng độ dài từ mốc từ (cài FFmpeg để chính xác)")
                    warned_probe = True
                vdur = (words[-1]["end"] + 0.25) if words else 3.0
            words = restore_punctuation(words, text) if words else even_words(text, vdur)
            entry.update(voice=voice.relative_to(base).as_posix(), voice_offset=args.lead,
                         voice_duration=round(vdur, 3))
            dur = args.lead + vdur + args.tail
            if sc.get("duration"):
                dur = max(dur, float(sc["duration"]))
            entry["words"] = [{"text": w["text"], "start": round(t + args.lead + w["start"], 3),
                               "end": round(t + args.lead + w["end"], 3)} for w in words]
        elif text:
            sys.exit(f"Cảnh {sid} có lời thoại nhưng chưa có file giọng trong {voice_dir}. Chạy bước TTS trước.")
        else:
            dur = float(sc.get("duration") or 3.0)
        # Làm tròn lên theo frame để start/duration của mọi cảnh khớp lưới frame.
        frames = math.ceil(round(dur * fps, 6))
        entry["start_frame"] = round(t * fps)
        entry["duration_frames"] = frames
        entry["start"] = round(t, 3)
        entry["duration"] = round(frames / fps, 3)
        captions += group_captions(entry["words"], args.max_words, args.max_chars)
        scenes.append(entry)
        t = round((entry["start_frame"] + frames) / fps, 6)

    timeline = {"fps": fps, "width": fmt["width"], "height": fmt["height"],
                "total_duration": round(t, 3), "total_frames": round(t * fps),
                "scenes": scenes, "captions": captions}
    (base / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1), encoding="utf-8")
    srt = "\n".join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n"
                    for i, c in enumerate(captions, 1))
    (base / "captions.srt").write_text(srt, encoding="utf-8")

    for s in scenes:
        print(f"{s['id']}  {s['start']:7.2f}s  +{s['duration']:5.2f}s  {'voice' if s['voice'] else 'no-voice'}")
    print(f"total {t:.2f}s ({timeline['total_frames']} frames @ {fps}fps), {len(captions)} caption lines")


if __name__ == "__main__":
    main()
