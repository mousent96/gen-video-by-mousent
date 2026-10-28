"""Quản lý thư mục production cho pipeline video.

  python production.py new "<tiêu đề>" [--engine hyperframes|remotion] [--lang vi] [--format 16:9] [--fps 30] [--auto]
  python production.py status [<slug>]
  python production.py done <slug> <step>
"""
import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PRODUCTIONS = ROOT / "productions"
STEPS = ["brief", "script", "voice", "assets", "build", "render"]
STEP_SKILL = {
    "brief": "video-pipeline (điền brief.md)",
    "script": "/video-script",
    "voice": "/video-voice",
    "assets": "/video-assets",
    "build": "/video-build-<engine>",
    "render": "/video-render",
}
FORMATS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}

BRIEF = """# Brief: {title}

- Chủ đề / thông điệp chính:
- Khán giả:
- Mục tiêu (bán hàng / giáo dục / giải trí / thông báo):
- Nền tảng: {platform}
- Độ dài mục tiêu (giây):
- Ngôn ngữ: {lang}
- Giọng đọc (nam/nữ, tốc độ, cảm xúc):
- Phong cách hình ảnh (màu, font, mood):
- Nhạc nền:
- Phụ đề: có
- CTA cuối video:
- Tài liệu nguồn (URL, file, logo):

## Giả định
"""


def slugify(text):
    text = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "video"


def load_state(slug):
    path = PRODUCTIONS / slug / "state.json"
    if not path.exists():
        sys.exit(f"Không thấy production '{slug}' ({path})")
    return path, json.loads(path.read_text(encoding="utf-8"))


def cmd_new(args):
    slug = slugify(args.title)
    base = PRODUCTIONS / slug
    if base.exists():
        sys.exit(f"Đã có {base}. Dùng `status {slug}` để tiếp tục.")
    width, height = FORMATS[args.format]
    for sub in ["audio/voice", "audio/sfx", "images", "video", "output", "source"]:
        (base / sub).mkdir(parents=True, exist_ok=True)
    state = {
        "title": args.title,
        "slug": slug,
        "engine": args.engine,
        "lang": args.lang,
        "format": {"aspect": args.format, "width": width, "height": height, "fps": args.fps},
        "auto": args.auto,
        "created": datetime.now().isoformat(timespec="seconds"),
        "done": [],
    }
    (base / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    platform = {"9:16": "TikTok / Shorts / Reels", "1:1": "Feed vuông", "4:5": "Feed dọc"}.get(args.format, "YouTube")
    (base / "brief.md").write_text(BRIEF.format(title=args.title, lang=args.lang, platform=platform), encoding="utf-8")
    print(f"created productions/{slug}  ({width}x{height}@{args.fps}, engine={args.engine}, lang={args.lang})")
    print("next: điền brief.md rồi chạy `done", slug, "brief`")


def cmd_status(args):
    if not args.slug:
        rows = sorted(PRODUCTIONS.glob("*/state.json")) if PRODUCTIONS.exists() else []
        if not rows:
            print("Chưa có production nào.")
        for path in rows:
            st = json.loads(path.read_text(encoding="utf-8"))
            nxt = next((s for s in STEPS if s not in st["done"]), "xong")
            print(f"{st['slug']:<40} {st['engine']:<12} next={nxt}")
        return
    _, st = load_state(args.slug)
    for step in STEPS:
        mark = "x" if step in st["done"] else " "
        print(f"[{mark}] {step:<7} {STEP_SKILL[step].replace('<engine>', st['engine'])}")
    nxt = next((s for s in STEPS if s not in st["done"]), None)
    print("next:", nxt or "hoàn tất", "| auto" if st.get("auto") else "")


def cmd_done(args):
    if args.step not in STEPS:
        sys.exit(f"step phải là một trong {STEPS}")
    path, st = load_state(args.slug)
    if args.step not in st["done"]:
        st["done"].append(args.step)
    # Làm lại một bước thì các bước sau phải làm lại.
    idx = STEPS.index(args.step)
    st["done"] = [s for s in STEPS if s in st["done"] and (STEPS.index(s) <= idx or not args.reset_after)]
    path.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    nxt = next((s for s in STEPS if s not in st["done"]), None)
    print(f"{args.step} done. next: {nxt or 'hoàn tất'}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("title")
    n.add_argument("--engine", choices=["hyperframes", "remotion"], default="hyperframes")
    n.add_argument("--lang", default="vi")
    n.add_argument("--format", choices=list(FORMATS), default="16:9")
    n.add_argument("--fps", type=int, default=30)
    n.add_argument("--auto", action="store_true")
    s = sub.add_parser("status")
    s.add_argument("slug", nargs="?")
    d = sub.add_parser("done")
    d.add_argument("slug")
    d.add_argument("step")
    d.add_argument("--reset-after", action="store_true", help="bỏ đánh dấu các bước sau (khi làm lại một bước)")
    args = p.parse_args()
    {"new": cmd_new, "status": cmd_status, "done": cmd_done}[args.cmd](args)


if __name__ == "__main__":
    main()
