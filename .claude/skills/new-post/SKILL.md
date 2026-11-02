---
name: new-post
description: Create a new Mr. Blue Bison post from photos (Apple Photos album or shared album, photos selected in Photos.app, or a local folder/files) plus pasted/typed context, with the description drafted in Jim's voice. Use when the user wants to add/make a new post, project, or item to the site from pictures.
argument-hint: <album name | "selected" | folder path> [context about the project]
---

# New post from photos

Work from the repo root. Paths below are relative to it. Scripts are uv single-file scripts
(they install Pillow themselves). Use the session scratchpad for staging, never the repo.

## 1. Figure out the source and context

From the arguments/conversation determine:
- **Source** (a path argument means a local folder or files; anything else is an album name):
  - Local folder → `--dir PATH`; specific files → `--files a.jpg b.heic`. Common case: the user
    downloads a curated subset into a folder. Then assume **all photos in it are wanted** (still
    flag obvious duplicates/blurry ones) and add `--sort name` if the filenames look deliberately
    ordered (e.g. `1.jpg`, `2.jpg` or renamed); otherwise photos are ordered by date taken.
  - Photos album or shared iCloud album name → `--album "Name"`. List names with
    `osxphotos albums --json` (shared ones are under `"shared albums"`, e.g. "Things B has Made").
  - "selected" / "the ones I picked in Photos" → `--selected` (user selects photos in Photos.app first).
  - For big albums, narrow with `--from-date/--to-date YYYY-MM-DD` if the user gives a time frame.
- **Context**: what it is, who made it, who it's for, when, pattern/source links.
  The user types or pastes this (often a copied email or note); pasted text may include
  unrelated chatter, so pull out only the relevant facts. Never invent facts. Ask only for
  things that matter and can't be seen in the photos (e.g., the pattern name).

For album/selected sources, `osxphotos` must be installed (`uv tool install osxphotos`). If the terminal lacks Photos access,
tell the user to grant Full Disk Access to their terminal app.

## 2. Gather

```
.claude/skills/new-post/scripts/gather.py --dir ~/Downloads/sweater --out <scratchpad>/post_staging
.claude/skills/new-post/scripts/gather.py --album "Things B has Made" --out <scratchpad>/post_staging
```
For albums this exports originals (downloading iCloud-only shared photos); local files are
read in place, never modified. It, writes metadata-free numbered
previews, `manifest.json`, and numbered contact sheets `sheet_K.jpg`. It prints the sheet paths.

Read the contact sheet(s) with the Read tool. Open individual `preview/NN.jpg` only where you
need a closer look (crop decisions, details for the text). Don't read originals.

## 3. Choose photos

- If the user already specified photos (by number, "the first five", "only the sweater ones",
  or by giving just those files), follow that.
- Otherwise propose: 3–6 photos, best first (the first image is the slideshow's lead), no
  near-duplicates, no blurry shots, plus a thumbnail pick. Prefer photos of the *made thing*;
  avoid photos where it's not visible.
- Every image is cropped to **800×480 (5:3 landscape)**, thumbnails to **200×135**. For portrait
  photos, choose a gravity (`top`, `center`, `bottom`, `left`, `right`) that keeps the subject
  (e.g., `top` keeps a face, `bottom` keeps shoes). A number `0..1` sets the vertical
  position precisely (`7:0.3` = upper third), which is often better than `top` for tall photos. Mention when a portrait photo will lose a lot.
- Tell the user the sheet path so they can open it themselves (`open <path>`) and choose numbers.

## 4. Draft the post

Read `.claude/skills/new-post/voice.md`, then re-read 2–3 of the example posts it lists. Draft:
- `title`: short, Title Case, names the thing ("Owl Diaper", "Moped Print").
- `slug`: lowercase_with_underscores from the title; check `img/<slug>` and `_posts/*-<slug>.md`
  don't already exist.
- `categories`: only from the nav: `baby`, `toddler`, `adult`, `print`, `sewing`, `knitting`
  (plus `shirt`, used as a tag). Pick 1–3. A new category would need a new page + nav link in
  `_layouts/default.html`; only do that if the user asks.
- `date`: default to today (newest-first front page). If the user wants it back-dated to when
  the project was made, use that date.
- Body in Jim's voice per the guide.

**Checkpoint:** show the user the selected photo numbers + gravities, thumbnail, title,
categories, date, and the full text. Wait for approval or edits. This is the one stop.

## 5. Build

```
.claude/skills/new-post/scripts/build.py --staging <scratchpad>/post_staging --slug <slug> \
  --images 4 7:top 2 9:bottom --thumb 7
```
It writes `img/<slug>/<slug>N.jpg` and `img/thumb/<slug>.jpg` (EXIF/GPS stripped) and prints
the `thumb:`/`images:` front matter. Then write `_posts/<YYYY-MM-DD>-<slug>.md`:

```
---
layout: item
title: <Title>
categories:
  - <cat>
thumb: <slug>.jpg
images:
  - <slug>/<slug>1.jpg
---

<body>
```

Read 1–2 of the generated 800×480 images to confirm crops look right; re-run build with
`--force` and different gravities if not.

## 6. Finish

Show `git status`, summarize the files. Commit only when the user asks (branch `gh-pages`
deploys directly to the live site via GitHub Pages, so confirm before pushing).
