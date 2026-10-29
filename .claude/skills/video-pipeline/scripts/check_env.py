"""Kiểm tra các tool cần cho pipeline video. Exit 1 nếu thiếu tool bắt buộc."""
import importlib.util
import re
import shutil
import subprocess
import sys

CHECKS = [
    # name, command, required, install hint
    ("node", ["node", "--version"], True, "winget install OpenJS.NodeJS.LTS"),
    ("npx", ["npx", "--version"], True, "đi kèm Node.js"),
    ("ffmpeg", ["ffmpeg", "-version"], True, "winget install Gyan.FFmpeg (mở terminal mới sau khi cài)"),
    ("ffprobe", ["ffprobe", "-version"], True, "đi kèm FFmpeg"),
    ("git", ["git", "--version"], False, "winget install Git.Git"),
]
PY_MODULES = [
    ("edge_tts", True, "python -m pip install -U edge-tts"),
    ("vieneu", False, "python -m pip install --no-deps vieneu==3.8.3 && python -m pip install -r scripts/requirements-vieneu.txt  (giọng Việt mặc định, local)"),
    ("kokoro_onnx", False, "python -m pip install kokoro-onnx soundfile  (giọng offline tiếng Anh)"),
]


def run(cmd):
    exe = shutil.which(cmd[0])
    if not exe:
        return None
    try:
        out = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=60)
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr) else "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    missing = False
    print(f"{'python':<12} OK       {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        print("  -> cần Python 3.10+")
        missing = True
    for name, cmd, required, hint in CHECKS:
        ver = run(cmd)
        if ver is None:
            print(f"{name:<12} {'MISSING' if required else 'optional'}  -> {hint}")
            missing |= required
            continue
        print(f"{name:<12} OK       {ver[:70]}")
        if name == "node":
            m = re.search(r"v(\d+)", ver)
            if m and int(m.group(1)) < 22:
                print("  -> HyperFrames cần Node 22+")
                missing = True
    for mod, required, hint in PY_MODULES:
        ok = importlib.util.find_spec(mod) is not None
        state = "OK" if ok else ("MISSING" if required else "optional")
        print(f"{mod:<12} {state:<8} {'' if ok else '-> ' + hint}")
        missing |= required and not ok
    print("\nHyperFrames Chrome: chạy `npx hyperframes browser ensure` (và `npx hyperframes doctor --json`).")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
