"""Kiểm tra file render so với timeline.json, xuất thumbnail và .srt.

  python verify_render.py productions/<slug> <video.mp4> [--thumb-at <giây>]
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


TOOLS = {}


def find_tools(base):
    """ffmpeg/ffprobe hệ thống, nếu không có thì dùng bản đi kèm Remotion trong project."""
    for name in ("ffmpeg", "ffprobe"):
        TOOLS[name] = shutil.which(name)
        if not TOOLS[name]:
            hits = sorted(base.glob(f"project/node_modules/@remotion/compositor-*/{name}*"))
            TOOLS[name] = str(hits[0]) if hits else None
    return all(TOOLS.values())


def ff(tool, *args):
    return subprocess.run([TOOLS[tool], *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("production")
    p.add_argument("video")
    p.add_argument("--thumb-at", type=float)
    args = p.parse_args()
    base, video = Path(args.production), Path(args.video)
    if not find_tools(base):
        sys.exit("Thiếu ffmpeg/ffprobe — xem /video-setup")
    if not video.exists() or video.stat().st_size == 0:
        sys.exit(f"FAIL: {video} không tồn tại hoặc rỗng")
    tl = json.loads((base / "timeline.json").read_text(encoding="utf-8"))

    info = json.loads(ff("ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(video)).stdout)
    vstreams = [s for s in info["streams"] if s["codec_type"] == "video"]
    astreams = [s for s in info["streams"] if s["codec_type"] == "audio"]
    duration = float(info["format"]["duration"])
    fails = []

    tol = 1 / tl["fps"] + 0.1
    if abs(duration - tl["total_duration"]) > tol:
        fails.append(f"độ dài {duration:.2f}s khác timeline {tl['total_duration']:.2f}s")
    if vstreams:
        v = vstreams[0]
        num, den = (int(x) for x in v.get("r_frame_rate", "0/1").split("/"))
        fps = num / den if den else 0
        if (v["width"], v["height"]) != (tl["width"], tl["height"]):
            fails.append(f"độ phân giải {v['width']}x{v['height']} khác {tl['width']}x{tl['height']}")
        if abs(fps - tl["fps"]) > 0.01:
            fails.append(f"fps {fps:.2f} khác {tl['fps']}")
    else:
        fails.append("không có video stream")
    has_voice = any(s.get("voice") for s in tl["scenes"])
    if has_voice and not astreams:
        fails.append("không có audio track dù có giọng đọc")

    loud = ""
    if astreams:
        out = ff("ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-").stderr
        i = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
        pk = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", out)
        if i:
            loud = f"{i[-1]} LUFS integrated" + (f", true peak {pk[-1]} dBFS" if pk else "")
            if float(i[-1]) < -30:
                fails.append(f"âm lượng quá nhỏ ({i[-1]} LUFS) — có thể mất tiếng")

    out_dir = video.parent
    first = tl["scenes"][0]
    at = args.thumb_at if args.thumb_at is not None else first["start"] + min(first["duration"] * 0.6, 2.5)
    thumb = out_dir / "thumbnail.png"
    ff("ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-i", str(video), "-frames:v", "1", str(thumb))
    srt = base / "captions.srt"
    if srt.exists() and srt.stat().st_size:
        shutil.copyfile(srt, out_dir / f"{video.stem}.srt")

    size_mb = video.stat().st_size / 1_048_576
    print(f"file      {video} ({size_mb:.1f} MB)")
    print(f"duration  {duration:.2f}s (timeline {tl['total_duration']:.2f}s)")
    if vstreams:
        print(f"video     {vstreams[0]['width']}x{vstreams[0]['height']} {vstreams[0].get('codec_name')} @ {vstreams[0].get('r_frame_rate')}")
    print(f"audio     {'yes ' + loud if astreams else 'none'}")
    print(f"thumbnail {thumb if thumb.exists() else 'không tạo được'}")
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    for s in tl["scenes"]:
        mid = s["start"] + s["duration"] / 2
        ff("ffmpeg", "-y", "-v", "error", "-ss", f"{mid:.3f}", "-i", str(video), "-frames:v", "1",
           "-vf", "scale=540:-2", str(frames_dir / f"{s['id']}.png"))
    print(f"frames    {frames_dir} (khung giữa mỗi cảnh — mở xem trước khi giao)")
    if fails:
        print("FAIL: " + "; ".join(fails))
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
