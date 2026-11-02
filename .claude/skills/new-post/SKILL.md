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

## 3. Choose photos and order

- **Order is exact and matters**: the first image is the lead slide. If the user gives an order
  (by filename like `IMG_8169`, or by contact-sheet number), use exactly that order and
  exactly those photos. The contact sheets label each photo with its number and filename.
- Otherwise propose: 3–6 photos, best first, no near-duplicates, no blurry shots. Prefer
  photos of the *made thing*. For a curated local folder, propose an order for all of them.
- Every image becomes **800×480 (5:3 landscape)**; thumbnails **200×135**. For each photo pick:
  - a crop position: `center` (default), `top`, `bottom`, `left`, `right`, or a number `0..1`
    for vertical position (`0.3` = upper third), which is often better than `top` for tall photos;
  - or `fit`: no crop, the whole photo centered on white. Use it for tall photos where cropping
    would lose the subject (full-length shots, a pattern envelope, a whole garment laid out).
  Check the previews' proportions (`width`/`height` in `manifest.json`) and say which photos
  will lose a lot to cropping.
- Thumbnail: defaults to the first image, cropped (never `fit`). Pick another with `--thumb`
  when a different photo reads better as a tiny square-ish tile (usually a close, simple shot).
- Tell the user the sheet path so they can open it themselves (`open <path>`).

## 4. Draft the post

Read `.claude/skills/new-post/voice.md`, then re-read 2–3 of the example posts it lists. Draft:
- `title`: short, Title Case, names the thing ("Owl Diaper", "Moped Print").
- `slug`: lowercase_with_underscores from the title; check `img/<slug>` and `_posts/*-<slug>.md`
  don't already exist.
- `categories`: from `nav_categories` in `_config.yml` (currently `baby`, `toddler`, `adult`,
  `print`, `sewing`, `knitting`), plus `shirt` as an unlinked tag. Pick 1–3; they show as tags
  on the post and highlight in the nav. A new category needs adding to `nav_categories` plus a
  page like `baby.html`; only do that if the user asks.
- `maker`: who made it, from `makers` in `_config.yml`: `jim` (shown as "Jimmy") or `bethany`
  (shown as "B"); a list `[jim, bethany]` for joint work. Infer from the context (first-person
  notes from Bethany → `bethany`); prints are usually Jim's but not always (the Rabbit Shirt
  screenprint is Bethany's). If unclear, ask. Shown as a byline and drives the "by jimmy" /
  "by b" pages.
- `date`: shown on the post page and used to sort the front page. Default to **when the photos
  were taken**: the latest `taken` among the chosen photos in `manifest.json` whose
  `taken_from` is `"photo"` (camera date). `build.py` also prints this as `post_date`. If none of
  the chosen photos has a camera date (`taken_from: "file"` means the date is just when the
  file was saved, e.g. photos sent via Messages), ask the user, defaulting to today. A date
  the user gives always wins.
- Body in Jim's voice per the guide.

**Checkpoint:** show the user the selected photo numbers + gravities, thumbnail, title,
maker, categories, date, and the full text. Wait for approval or edits. This is the one stop.

## 5. Build

```
.claude/skills/new-post/scripts/build.py --staging <scratchpad>/post_staging --slug <slug> \
  --images IMG_8169 IMG_8171:fit IMG_8069 IMG_8067:0.3 --thumb IMG_8169
```
(Contact-sheet numbers work too: `--images 3 4:fit 2 1:0.3`.)
Images are written in exactly the `--images` order. It writes `img/<slug>/<slug>N.jpg` and `img/thumb/<slug>.jpg` (EXIF/GPS stripped) and prints
`post_date` and the `thumb:`/`images:` front matter. Then write `_posts/<post date>-<slug>.md`:

```
---
layout: item
title: <Title>
maker: <jim|bethany>
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
