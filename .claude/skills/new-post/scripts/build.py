#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["pillow>=10", "pillow-heif>=0.16"]
# ///
"""Turn chosen staged photos into site images.

  build.py --staging DIR --slug zia_sweater --images 3 5:top 7:bottom --thumb 5
  build.py --staging DIR --slug new_pants --images IMG_8169 IMG_8171:0.3 IMG_8069

Images appear on the post in exactly the order given; the first is the lead.
Each image spec is ID[:gravity] where ID is the number from the contact sheet or
the photo's filename (with or without extension, case-insensitive), and
gravity is center (default), top, bottom, left, right, fit (no crop: whole photo
centered on white, good for tall photos), or a number
0..1 for vertical position (0=top, 0.3=upper third, 1=bottom) — which part of the photo
to keep when cropping to the site's 800x480 slideshow frame.
--thumb takes the same spec and makes the 200x135 thumbnail (default: the first image).
Also prints the suggested post date: the latest camera date among the chosen photos.

Writes img/<slug>/<slug>1.jpg ... and img/thumb/<slug>.jpg relative to --site
(default: current directory), with all metadata (incl. GPS) stripped, then prints
the front-matter lines for the post.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()

SLIDE = (800, 480)
THUMB = (200, 135)
FIT = "fit"  # no crop: whole photo centered on white
GRAVITY = {"fit": FIT, "center": (0.5, 0.5), "top": (0.5, 0.0), "bottom": (0.5, 1.0),
           "left": (0.0, 0.5), "right": (1.0, 0.5)}


def parse_spec(spec: str):
    n, _, g = spec.partition(":")
    g = g or "center"
    if g in GRAVITY:
        return n, GRAVITY[g]
    try:
        y = float(g)  # numeric = vertical position: 0 top .. 1 bottom
    except ValueError:
        y = -1
    if not 0 <= y <= 1:
        sys.exit(f"bad gravity '{g}' in '{spec}' (use {', '.join(GRAVITY)} or 0..1)")
    return n, (0.5, y)


def lookup(ident: str, entries: list[dict]) -> dict:
    """Find a staged photo by contact-sheet number or by filename."""
    if ident.isdigit():
        for e in entries:
            if e["n"] == int(ident):
                return e
    key = ident.lower()
    for e in entries:
        name = e.get("name") or Path(e["source"]).name
        if key in (name.lower(), Path(name).stem.lower()):
            return e
    sys.exit(f"no staged photo matches '{ident}' (use a contact-sheet number or filename)")


def render(src: str, size, gravity: str, dest: Path):
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if gravity == FIT:
        img.thumbnail(size, Image.LANCZOS)
        out = Image.new("RGB", size, "white")
        out.paste(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
    else:
        out = ImageOps.fit(img, size, method=Image.LANCZOS, centering=gravity)
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest, quality=88, optimize=True, progressive=True)  # no exif -> stripped


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--staging", type=Path, required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--images", nargs="+", required=True)
    p.add_argument("--thumb", help="spec for the thumbnail (default: first image)")
    p.add_argument("--site", type=Path, default=Path("."))
    p.add_argument("--force", action="store_true", help="overwrite an existing img/<slug>/")
    args = p.parse_args()

    entries = json.loads((args.staging / "manifest.json").read_text())
    img_dir = args.site / "img" / args.slug
    thumb = args.site / "img" / "thumb" / f"{args.slug}.jpg"
    if (img_dir.exists() or thumb.exists()) and not args.force:
        sys.exit(f"{img_dir} or {thumb} already exists; pass --force to overwrite")

    chosen = [(lookup(ident, entries), g) for ident, g in map(parse_spec, args.images)]
    names = [e["source"] for e, _ in chosen]
    if len(set(names)) != len(names):
        sys.exit("the same photo is listed twice in --images")

    paths = []
    for i, (e, g) in enumerate(chosen, start=1):
        rel = f"{args.slug}/{args.slug}{i}.jpg"
        render(e["source"], SLIDE, g, args.site / "img" / rel)
        paths.append(rel)

    ident, g = parse_spec(args.thumb or args.images[0])
    if g == FIT and not args.thumb:
        g = GRAVITY["center"]  # a letterboxed thumb looks tiny in the grid; crop instead
    render(lookup(ident, entries)["source"], THUMB, g, thumb)

    dated = [e["taken"] for e, _ in chosen if e.get("taken_from", "photo") == "photo"]
    if dated:
        print(f"post_date: {max(dated)[:10]}  # latest camera date of chosen photos")
    else:
        print("post_date: none  # no camera dates on chosen photos; ask or use today")
    print(f"thumb: {args.slug}.jpg")
    print("images:")
    for rel in paths:
        print(f"  - {rel}")


if __name__ == "__main__":
    main()
