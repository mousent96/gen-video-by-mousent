"""Tạo giọng đọc từng cảnh, kèm mốc thời gian từng từ.

  python tts.py productions/<slug> [--provider auto|edge|google|piper] [--voice <tên>] [--force] [--only s01,s03]

Provider (đọc từ script.json voice.provider, mặc định auto):
  edge    Microsoft Edge TTS - giọng tự nhiên nhất, mốc từ chính xác. Cần mạng tới speech.platform.bing.com.
  google  Google Translate TTS qua translate.googleapis.com (thuộc *.googleapis.com, được phép trong cloud session mặc định).
  piper   Offline, model tải 1 lần từ GitHub releases (rhasspy/piper). Tiếng Việt phát âm sai nhiều: chỉ khi không có mạng.
  auto    edge nếu kết nối được, không thì google.

Ghi audio/voice/<id>.mp3|wav và audio/voice/<id>.words.json ([{text,start,end}] giây).
Với google/piper, mốc từ = mốc từng câu (đo chính xác) chia theo độ dài chữ trong câu.
"""
import argparse
import asyncio
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.parse
import urllib.request
import wave
from pathlib import Path

TICKS = 10_000_000  # edge-tts dùng đơn vị 100ns
UA = {"User-Agent": "Mozilla/5.0"}
DEFAULT_VOICES = {
    "edge": {"vi": "vi-VN-HoaiMyNeural", "en": "en-US-AvaMultilingualNeural"},
    "piper": {"vi": "vi-25hours-single-low", "en": "en-us-lessac-medium"},
}
PIPER_RELEASE = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-{name}.tar.gz"
CACHE = Path.home() / ".cache" / "gen-video"


def proxy():
    return os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")


def reachable(url):
    try:
        urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=6)
        return True
    except urllib.error.HTTPError:
        return True  # máy chủ trả lời = mạng thông
    except Exception:  # noqa: BLE001
        return False


def pick_provider(lang):
    if reachable("https://speech.platform.bing.com/"):
        try:
            import edge_tts  # noqa: F401
            return "edge"
        except ImportError:
            print("  edge-tts chưa cài (python -m pip install -U edge-tts), bỏ qua")
    if reachable("https://translate.googleapis.com/"):
        return "google"
    # Piper không vào auto: giọng tiếng Việt của nó phát âm sai nhiều (đo bằng Whisper).
    sys.exit("Không kết nối được edge-tts lẫn Google TTS. Kiểm tra mạng, hoặc chạy --provider piper (offline, chất lượng kém).")


def rate_factor(rate):
    m = re.fullmatch(r"([+-]\d+)%", rate or "+0%")
    return 1 + int(m.group(1)) / 100 if m else 1.0


def split_chunks(text, limit=180):
    """Cắt theo câu / dấu phẩy, mỗi đoạn <= limit ký tự (giới hạn của Google TTS)."""
    parts, cur = [], ""
    for sent in re.split(r"(?<=[.!?…;:,])\s+", text.strip()):
        while len(sent) > limit:
            cut = sent.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            parts.append(sent[:cut].strip())
            sent = sent[cut:].strip()
        if cur and len(cur) + 1 + len(sent) > limit:
            parts.append(cur)
            cur = sent
        else:
            cur = f"{cur} {sent}".strip()
    if cur:
        parts.append(cur)
    return [p for p in parts if p]


def spread_words(chunk, start, end):
    tokens = chunk.split()
    weights = [len(re.sub(r"\W", "", t)) + 1 for t in tokens]
    total, t, out = sum(weights), start, []
    for tok, w in zip(tokens, weights):
        d = (end - start) * w / total
        out.append({"text": tok, "start": round(t, 3), "end": round(t + d, 3)})
        t += d
    return out


def ffprobe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True)
    return float(out.stdout.strip())


def need_ffmpeg():
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("Provider google cần ffmpeg/ffprobe — chạy /video-setup (cloud: bash scripts/cloud-setup.sh)")


# ---------- edge ----------
async def synth_edge(text, voice, rate, pitch, out_base):
    import edge_tts  # noqa: F401 - đã kiểm tra trong main()
    # Dịch vụ trả "No audio was received" khi gửi rate và pitch cùng lúc, hoặc pitch khác 0:
    # chỉ gửi tham số khác mặc định, và ưu tiên rate.
    kw = {"proxy": proxy()} if proxy() else {}
    if rate not in ("", "+0%"):
        kw["rate"] = rate
    elif pitch not in ("", "+0Hz"):
        kw["pitch"] = pitch
    try:
        comm = edge_tts.Communicate(text, voice, boundary="WordBoundary", **kw)
    except TypeError:  # edge-tts < 7 không có tham số boundary, mặc định đã là WordBoundary
        comm = edge_tts.Communicate(text, voice, **kw)
    words, path = [], out_base.with_suffix(".mp3")
    with open(path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                s = chunk["offset"] / TICKS
                words.append({"text": chunk["text"], "start": round(s, 3),
                              "end": round(s + chunk["duration"] / TICKS, 3)})
    return path, words


async def run_edge(text, voice, rate, pitch, out_base, sid):
    # Dịch vụ hay lỗi ngẫu nhiên khi có rate/pitch: thử 3 lần, sau đó đọc ở tốc độ mặc định.
    plan = [(rate, pitch)] * 3 + [("+0%", "+0Hz")] * 2
    for attempt, (r, pt) in enumerate(plan):
        try:
            res = await synth_edge(text, voice, r, pt, out_base)
            if (r, pt) != (rate, pitch):
                print(f"  warn: {sid} đọc ở tốc độ mặc định vì edge-tts từ chối rate={rate} pitch={pitch}")
            return res
        except Exception as exc:  # noqa: BLE001 - dịch vụ thỉnh thoảng lỗi tạm thời
            if attempt == len(plan) - 1:
                raise RuntimeError(f"edge-tts lỗi: {exc}") from exc
            await asyncio.sleep(1.5 * (attempt + 1))
    return None


# ---------- google ----------
def run_google(text, lang, rate, out_base, tmp):
    need_ffmpeg()
    chunks = split_chunks(text)
    parts, words, t = [], [], 0.0
    for i, chunk in enumerate(chunks):
        url = ("https://translate.googleapis.com/translate_tts?ie=UTF-8&client=gtx&tl="
               f"{urllib.parse.quote(lang)}&q={urllib.parse.quote(chunk)}")
        data = None
        for attempt in range(4):
            try:
                data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == 3:
                    raise RuntimeError(f"Google TTS lỗi: {exc}") from exc
                import time
                time.sleep(2 * (attempt + 1))
        part = tmp / f"part{i:03}.mp3"
        part.write_bytes(data)
        parts.append(part)
    factor = rate_factor(rate)
    out = out_base.with_suffix(".mp3")
    # Nối các đoạn, chuẩn hoá về 1 file mp3; đo từng đoạn sau khi đổi tốc độ để mốc từ chính xác.
    fixed_parts = []
    for chunk, part in zip(chunks, parts):
        fixed = part.with_name(part.stem + "-n.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(part), "-af", f"atempo={factor}",
                        "-ar", "24000", "-ac", "1", str(fixed)], check=True)
        d = ffprobe_duration(fixed)
        words += spread_words(chunk, t + 0.05, t + d - 0.08)
        fixed_parts.append(fixed)
        t += d
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in fixed_parts), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:a", "libmp3lame", "-q:a", "3", str(out)], check=True)
    return out, words


# ---------- piper ----------
def piper_model(name):
    model = CACHE / "piper" / name / f"{name}.onnx"
    if model.exists():
        return model
    url = PIPER_RELEASE.format(name=name)
    print(f"  tải model piper {name} (một lần) từ {url}")
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()
    dest = model.parent
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for m in tar.getmembers():
            if m.isfile() and m.name.endswith((".onnx", ".onnx.json")):
                f = tar.extractfile(m)
                suffix = ".onnx.json" if m.name.endswith(".json") else ".onnx"
                (dest / f"{name}{suffix}").write_bytes(f.read())
    return model


def run_piper(text, voice_name, rate, out_base):
    try:
        from piper import PiperVoice
    except ImportError:
        sys.exit("Thiếu piper-tts: python -m pip install piper-tts")
    voice = PiperVoice.load(str(piper_model(voice_name)))
    length_scale = 1 / rate_factor(rate)
    frames, words, t, params = [], [], 0.0, None
    gap = 0.18  # nghỉ giữa các câu
    for chunk in split_chunks(text, limit=400):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            try:
                from piper import SynthesisConfig
                voice.synthesize_wav(chunk, w, syn_config=SynthesisConfig(length_scale=length_scale))
            except ImportError:  # piper-tts < 1.3
                voice.synthesize(chunk, w, length_scale=length_scale)
        buf.seek(0)
        with wave.open(buf, "rb") as r:
            params = r.getparams()
            data = r.readframes(r.getnframes())
            d = r.getnframes() / r.getframerate()
        words += spread_words(chunk, t + 0.03, t + d - 0.05)
        silence = b"\x00" * int(gap * params.framerate) * params.sampwidth * params.nchannels
        frames.append(data + silence)
        t += d + gap
    out = out_base.with_suffix(".wav")
    with wave.open(str(out), "wb") as w:
        w.setparams(params)
        w.writeframes(b"".join(frames))
    return out, words


async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("production")
    p.add_argument("--provider", choices=["auto", "edge", "google", "piper"])
    p.add_argument("--voice", help="ghi đè voice.name trong script.json")
    p.add_argument("--force", action="store_true")
    p.add_argument("--only", default="")
    args = p.parse_args()

    base = Path(args.production)
    script_path = base / "script.json"
    script = json.loads(script_path.read_text(encoding="utf-8"))
    lang = (script.get("lang") or "vi").split("-")[0]
    vcfg = script.setdefault("voice", {})
    provider = args.provider or vcfg.get("provider") or "auto"
    if provider == "auto":
        provider = pick_provider(lang)
        print(f"provider: {provider} (auto)")
    # Tên giọng chỉ đúng với provider đã ghi cùng nó: đổi provider thì về giọng mặc định của provider mới.
    name = args.voice or (vcfg.get("name") if vcfg.get("provider") in (provider, None, "auto") else "") or ""
    if provider == "edge" and not re.match(r"^[a-z]{2}-[A-Z]{2}-", name):
        name = DEFAULT_VOICES["edge"].get(lang, DEFAULT_VOICES["edge"]["en"])
    elif provider == "piper" and (not name or re.match(r"^([a-z]{2}-[A-Z]{2}-|google-)", name)):
        name = DEFAULT_VOICES["piper"].get(lang, DEFAULT_VOICES["piper"]["en"])
    elif provider == "google":
        name = f"google-{lang}"
    rate, pitch = vcfg.get("rate", "+0%"), vcfg.get("pitch", "+0Hz")
    if provider == "edge":
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            sys.exit("Thiếu edge-tts: python -m pip install -U edge-tts (hoặc --provider google)")
    only ={s for s in args.only.split(",") if s}

    out = base / "audio" / "voice"
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / ".tmp"
    cache_path = out / ".tts-cache.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

    made = skipped = 0
    for scene in script["scenes"]:
        sid, text = scene["id"], (scene.get("narration") or "").strip()
        if not text or (only and sid not in only):
            continue
        key = hashlib.sha1(f"{provider}|{name}|{rate}|{pitch}|{text}".encode()).hexdigest()
        existing = [f for f in (out / f"{sid}.mp3", out / f"{sid}.wav") if f.exists()]
        if not args.force and cache.get(sid) == key and existing:
            skipped += 1
            continue
        print(f"tts {sid} ({provider}:{name}): {text[:60]}")
        tmp.mkdir(exist_ok=True)
        try:
            if provider == "edge":
                path, words = await run_edge(text, name, rate, pitch, out / sid, sid)
            elif provider == "google":
                path, words = run_google(text, lang, rate, out / sid, tmp)
            else:
                path, words = run_piper(text, name, rate, out / sid)
        except RuntimeError as exc:
            sys.exit(f"{sid}: {exc}. Thử --provider google hoặc --provider piper.")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        for f in existing:  # bỏ file cũ khác đuôi (mp3 ↔ wav) để timeline không lấy nhầm
            if f != path:
                f.unlink()
        if not words:
            print(f"  warn: {path.name} không có mốc từ; phụ đề sẽ chia đều theo thời lượng")
        (out / f"{sid}.words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
        cache[sid] = key
        cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        made += 1
    if vcfg.get("provider") != provider or vcfg.get("name") != name:
        vcfg.update(provider=provider, name=name)
        script_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"done: {made} tạo mới, {skipped} dùng lại cache -> {out} (provider {provider}, voice {name})")


if __name__ == "__main__":
    asyncio.run(main())
