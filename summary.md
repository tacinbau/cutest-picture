# Cutest picture — method summary

Bounty: make.fun `cutest-picture-01` ($250; prizes 1st $50, 2nd $35, 3rd $25,
4th–10th $10, 11th–20th $7; entries close 2026-11-13 10:00 UTC / 17:00 WIB).
Entry program: `main.py` (Python 3.13, standard library only), writes
`$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output/entry.png`).

## What the picture is

One giant chubby baby kitten face, filling the frame: cream fur, two warm
tan ears with pink inner ears, a little pink bow on the right ear, a 5°
head tilt, two huge amber eyes with double white highlights set low on the
face (baby proportions), a tiny pink nose, a little "w" cat mouth, soft
pink blush cheeks, three smooth whiskers each side, and two paws peeking up
at the bottom edge. Background: a soft peach-to-cream gradient with faint
polka dots that never crowd the subject.

## How it is generated

Pure procedural drawing, no network, no image library, no external assets:

- A small signed-distance-field rasterizer (`Canvas`): circles, ellipses and
  triangles are tested per pixel inside tight bounding boxes and composited
  with `coverage = clamp(0.5 - d / band)`, so every edge is smoothly
  anti-aliased. Curves (mouth, whiskers, toes) are drawn as sampled discs
  along quadratic Beziers.
- A hand-rolled PNG encoder (`zlib` + `struct` + `binascii`): 8-bit RGBA,
  filter 0, IHDR/IDAT/IEND with correct CRC32s.
- Fully deterministic: fixed-seed jitter for the background dots, no time,
  no randomness, no dict-order dependence — two runs write byte-identical
  files.

## Why it should win (judge criteria, in order)

1. **Cute at one glance:** one clear subject — a kitten face that fills the
   frame. Nothing else competes with it.
2. **The subject itself is cute:** soft round shapes everywhere, huge bright
   eyes (the largest shapes after the head), chubby proportions, eyes low
   on the face, a small smiling mouth.
3. **Charm:** head tilt, a tiny pink bow, paws peeking up at the bottom edge.
4. **Craft:** SDF anti-aliasing on every edge, correct anatomy (2 ears, 2
   eyes, 1 nose), no smears, artefacts or text.
5. **Reads small:** a single giant face — at ~300 px across it is still
   unmistakably a kitten face with big eyes.

## Validation

- PNG valid (chunk walk: all CRCs pass, IEND at exactly the file size,
  IDAT decompresses to exactly 1024 × (1 + 1024 × 4) bytes, all rows
  filter 0): 1024 × 1024, 8-bit RGBA.
- Size 80,083 bytes (limit 1,048,576).
- Deterministic: two runs byte-identical (sha256 `15df8c57b067ff06…`).
- Runtime ~1.8 s per run (limit 60 s), 1 CPU, far under 512 MB.
- Default output path verified: with `MAKEFUN_OUTPUT_DIR` unset it writes
  `/output/entry.png`.
- Visually inspected at full size (see `preview.png`): the picture is the
  kitten described above; three render iterations fixed the ears (first
  hidden behind the head, then corner-blob artefacts from over-large
  triangle rounding, then a warm ear colour so the ears read against the
  background).

## Files

- `main.py` — the entry program (draws the picture; the only file the repo
  needs besides LICENSE).
- `preview.png` — reference render of what the program writes (not part of
  the entry; the program draws it at runtime).
- `summary.md`, `work-log.md`, `README.md`, `LICENSE` (MIT).
