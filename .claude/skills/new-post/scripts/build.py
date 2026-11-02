#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["pillow>=10", "pillow-heif>=0.16"]
# ///
"""Turn chosen staged photos into site images.

  build.py --staging DIR --slug zia_sweater --images 3 5:top 7:bottom --thumb 5

Each image spec is N[:gravity] where N is the number from the contact sheet and
gravity is center (default), top, bottom, left, right, or a number
0..1 for vertical position (0=top, 0.3=upper third, 1=bottom) — which part of the photo
to keep when cropping to the site's 800x480 slideshow frame.
--thumb takes the same spec and makes the 200x135 thumbnail.

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
GRAVITY = {"center": (0.5, 0.5), "top": (0.5, 0.0), "bottom": (0.5, 1.0),
           "left": (0.0, 0.5), "right": (1.0, 0.5)}


def parse_spec(spec: str):
    n, _, g = spec.partition(":")
    g = g or "center"
    if g in GRAVITY:
        return int(n), GRAVITY[g]
    try:
        y = float(g)  # numeric = vertical position: 0 top .. 1 bottom
    except ValueError:
        y = -1
    if not 0 <= y <= 1:
        sys.exit(f"bad gravity '{g}' in '{spec}' (use {', '.join(GRAVITY)} or 0..1)")
    return int(n), (0.5, y)


def render(src: str, size, gravity: str, dest: Path):
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    out = ImageOps.fit(img, size, method=Image.LANCZOS, centering=gravity)
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest, quality=88, optimize=True, progressive=True)  # no exif -> stripped


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--staging", type=Path, required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--images", nargs="+", required=True)
    p.add_argument("--thumb", required=True)
    p.add_argument("--site", type=Path, default=Path("."))
    p.add_argument("--force", action="store_true", help="overwrite an existing img/<slug>/")
    args = p.parse_args()

    manifest = {e["n"]: e for e in json.loads((args.staging / "manifest.json").read_text())}
    img_dir = args.site / "img" / args.slug
    thumb = args.site / "img" / "thumb" / f"{args.slug}.jpg"
    if (img_dir.exists() or thumb.exists()) and not args.force:
        sys.exit(f"{img_dir} or {thumb} already exists; pass --force to overwrite")

    paths = []
    for i, spec in enumerate(args.images, start=1):
        n, g = parse_spec(spec)
        if n not in manifest:
            sys.exit(f"no photo #{n} in staging")
        rel = f"{args.slug}/{args.slug}{i}.jpg"
        render(manifest[n]["source"], SLIDE, g, args.site / "img" / rel)
        paths.append(rel)

    n, g = parse_spec(args.thumb)
    render(manifest[n]["source"], THUMB, g, thumb)

    print(f"thumb: {args.slug}.jpg")
    print("images:")
    for rel in paths:
        print(f"  - {rel}")


if __name__ == "__main__":
    main()
