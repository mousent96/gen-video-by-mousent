#!/usr/bin/env python3
"""Trộn lại audio của video đã render mà KHÔNG render lại hình.

Đọc các thẻ <audio> trong project/index.html (data-start, data-duration, data-volume),
thay nhạc nền bằng file mới (lặp + crossfade nếu ngắn hơn video), tự hạ nhạc khi có
lời đọc (sidechain), rồi ghép vào MP4 có sẵn bằng -c:v copy.

  python remix_audio.py productions/<slug> --video output/<slug>.mp4 \
      --bgm assets/audio/new.mp3 --bgm-volume 0.24 --out output/<slug>-music.mp4

Thẻ <audio id="bgm..."> cũ bị bỏ qua; thẻ id bắt đầu bằng "vo-" là lời đọc (dùng làm sidechain).
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

def probe(p):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(p)]).decode().strip())

def resolve(p, base):
    """Đường dẫn tuyệt đối, hoặc tương đối theo thư mục hiện tại nếu tồn tại, ngược lại theo production."""
    p = Path(p)
    return p if p.is_absolute() or p.exists() else base / p

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("production"); ap.add_argument("--video", required=True); ap.add_argument("--bgm", required=True)
    ap.add_argument("--bgm-volume", type=float, default=0.24); ap.add_argument("--xfade", type=float, default=2.5)
    ap.add_argument("--fade-in", type=float, default=1.5); ap.add_argument("--fade-out", type=float, default=2.5)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    prod = Path(a.production); proj = prod / "project"
    html = (proj / "index.html").read_text(encoding="utf-8")
    T = json.loads((prod / "timeline.json").read_text(encoding="utf-8"))["total_duration"]
    tags = re.findall(r"<audio\b([^>]*)>", html)
    attr = lambda t, k: (re.search(k + r'="([^"]*)"', t) or [None, None])[1]
    voices, others = [], []
    for t in tags:
        i, src = attr(t, "id") or "", attr(t, "src")
        if not src or i.startswith("bgm"): continue
        e = (proj / src, float(attr(t, "data-start") or 0), float(attr(t, "data-volume") or 1))
        (voices if i.startswith("vo-") else others).append(e)
    if not voices: sys.exit("không thấy thẻ audio lời đọc (id vo-*)")
    bgm = resolve(a.bgm, prod)
    L = probe(bgm); loops = max(1, int((T + a.xfade) // max(L - a.xfade, 0.1)) + 1)
    inputs, fc, n = [], [], 0
    def add(p): nonlocal n; inputs.extend(["-i", str(p)]); n += 1; return n - 1
    vl = []
    for p, s, v in voices:
        k = add(p); fc.append(f"[{k}]volume={v},adelay={int(s*1000)}:all=1[v{k}]"); vl.append(f"[v{k}]")
    fc.append("".join(vl) + f"amix=inputs={len(vl)}:normalize=0,aformat=sample_rates=44100:channel_layouts=stereo,apad,atrim=0:{T},asplit=2[voice][sc]")
    ol = []
    for p, s, v in others:
        k = add(p); fc.append(f"[{k}]volume={v},adelay={int(s*1000)}:all=1,aformat=sample_rates=44100:channel_layouts=stereo[o{k}]"); ol.append(f"[o{k}]")
    ks = [add(bgm) for _ in range(loops)]
    prev = f"[{ks[0]}]"
    for j, k in enumerate(ks[1:]):
        fc.append(f"{prev}[{k}]acrossfade=d={a.xfade}:c1=tri:c2=tri[x{j}]"); prev = f"[x{j}]"
    fc.append(f"{prev}atrim=0:{T},aformat=sample_rates=44100:channel_layouts=stereo,volume={a.bgm_volume},afade=t=in:d={a.fade_in},afade=t=out:st={T-a.fade_out}:d={a.fade_out}[m]")
    fc.append("[m][sc]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=500[md]")
    fc.append("[voice]" + "".join(ol) + f"[md]amix=inputs={2+len(ol)}:normalize=0,alimiter=limit=0.89,atrim=0:{T}[out]")
    mix = prod / "output" / "_remix.wav"
    mix.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg","-y","-v","error",*inputs,"-filter_complex",";".join(fc),"-map","[out]","-ar","44100",str(mix)], check=True)
    vid = resolve(a.video, prod)
    out = Path(a.out) if Path(a.out).is_absolute() else prod / a.out
    subprocess.run(["ffmpeg","-y","-v","error","-i",str(vid),"-i",str(mix),"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(out)], check=True)
    print(f"ok -> {out} ({loops} lượt nhạc, {len(voices)} lời đọc, {len(others)} sfx)")

if __name__ == "__main__":
    main()
