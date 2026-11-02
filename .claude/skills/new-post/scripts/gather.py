#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["pillow>=10", "pillow-heif>=0.16"]
# ///
"""Collect candidate photos into a staging folder and build numbered contact sheets.

Sources (pick one):
  --album NAME        Photos album or shared iCloud album (via osxphotos)
  --selected          Whatever is currently selected in Photos.app (via osxphotos)
  --dir PATH          A local folder of images (jpg/jpeg/png/heic)
  --files F [F ...]   Specific image files

Optional filters for Photos sources: --from-date / --to-date (YYYY-MM-DD).

Output in --out:
  originals/          exported or copied originals (untouched)
  preview/NN.jpg      oriented, metadata-free previews (max 1024px) numbered in date order
  sheet_K.jpg         contact sheets with big numbers, 30 photos per sheet
  manifest.json       number -> original path, date taken, size
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
PER_SHEET = 30
COLS = 6
CELL = 300


def export_from_photos(args, dest: Path) -> None:
    osxphotos = shutil.which("osxphotos")
    if not osxphotos:
        sys.exit("osxphotos not found. Install with: uv tool install osxphotos")
    # Shared-album photos are often not downloaded locally; --download-missing
    # with PhotoKit fetches them from iCloud (Photos.app must be able to sync).
    cmd = [osxphotos, "export", str(dest), "--skip-original-if-edited",
           "--only-photos", "--skip-live", "--overwrite",
           "--download-missing", "--use-photokit"]
    if args.album:
        cmd += ["--album", args.album]
    if args.selected:
        cmd += ["--selected"]
    if args.from_date:
        cmd += ["--from-date", args.from_date]
    if args.to_date:
        cmd += ["--to-date", args.to_date]
    print("+", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, check=True, stdout=sys.stderr)


def taken_at(path: Path, img: Image.Image) -> str:
    exif = img.getexif()
    raw = exif.get_ifd(0x8769).get(36867) or exif.get(306)  # DateTimeOriginal / DateTime
    if raw:
        try:
            return datetime.strptime(str(raw).strip(), "%Y:%m:%d %H:%M:%S").isoformat()
        except ValueError:
            pass
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat()


def natural_key(name: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def font(size: int):
    for f in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_sheets(entries, out: Path) -> list[str]:
    label_font = font(44)
    sheets = []
    for s in range(0, len(entries), PER_SHEET):
        chunk = entries[s:s + PER_SHEET]
        rows = (len(chunk) + COLS - 1) // COLS
        sheet = Image.new("RGB", (COLS * CELL, rows * CELL), "white")
        draw = ImageDraw.Draw(sheet)
        for i, e in enumerate(chunk):
            im = Image.open(out / e["preview"])
            im.thumbnail((CELL - 10, CELL - 10))
            x, y = (i % COLS) * CELL, (i // COLS) * CELL
            sheet.paste(im, (x + (CELL - im.width) // 2, y + (CELL - im.height) // 2))
            label = str(e["n"])
            box = draw.textbbox((x + 8, y + 8), label, font=label_font)
            draw.rectangle((box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), fill="black")
            draw.text((x + 8, y + 8), label, font=label_font, fill="yellow")
        name = f"sheet_{s // PER_SHEET + 1}.jpg"
        sheet.save(out / name, quality=80)
        sheets.append(name)
    return sheets


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--album")
    src.add_argument("--selected", action="store_true")
    src.add_argument("--dir", type=Path)
    src.add_argument("--files", nargs="+", type=Path)
    p.add_argument("--from-date")
    p.add_argument("--to-date")
    p.add_argument("--sort", choices=["date", "name"], default="date",
                   help="number photos by date taken (default) or by filename")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    out = args.out
    if out.exists():
        shutil.rmtree(out)
    originals = out / "originals"
    (out / "preview").mkdir(parents=True)
    originals.mkdir()

    if args.album or args.selected:
        export_from_photos(args, originals)
        files = [f for f in originals.iterdir() if f.suffix.lower() in IMAGE_EXTS]
    else:
        if args.dir and not args.dir.expanduser().is_dir():
            sys.exit(f"not a directory: {args.dir}")
        files = args.files or [f for f in args.dir.expanduser().iterdir()
                               if f.suffix.lower() in IMAGE_EXTS and not f.name.startswith(".")]
        for f in files:
            if not f.is_file():
                sys.exit(f"not a file: {f}")
        # reference local files in place; no copy needed

    if not files:
        sys.exit("No images found.")

    records = []
    for f in files:
        try:
            img = Image.open(f)
        except Exception as e:  # noqa: BLE001
            print(f"skip {f.name}: {e}", file=sys.stderr)
            continue
        records.append((taken_at(f, img), f, img))
    if args.sort == "name":
        records.sort(key=lambda r: natural_key(r[1].name))
    else:
        records.sort(key=lambda r: (r[0], r[1].name))

    entries = []
    for n, (when, f, img) in enumerate(records, start=1):
        img = ImageOps.exif_transpose(img).convert("RGB")
        w, h = img.size
        img.thumbnail((1024, 1024))
        prev = f"preview/{n:02d}.jpg"
        img.save(out / prev, quality=85)  # no exif passed -> metadata stripped
        entries.append({"n": n, "source": str(f.resolve()), "preview": prev,
                        "taken": when, "width": w, "height": h})

    sheets = make_sheets(entries, out)
    (out / "manifest.json").write_text(json.dumps(entries, indent=2))
    print(json.dumps({"count": len(entries), "out": str(out.resolve()),
                      "sheets": [str((out / s).resolve()) for s in sheets],
                      "dates": [entries[0]["taken"], entries[-1]["taken"]]}, indent=2))


if __name__ == "__main__":
    main()
