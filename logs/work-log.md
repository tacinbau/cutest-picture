# Work log — make.fun cutest-picture-01 entry

Bounty: https://make.fun/bounty/cutest-picture-01 ($250, entries close
2026-11-13 10:00 UTC / 17:00 WIB). Work dir:
~/workspace/make-fun-cutest-picture/. Build only — no sign-in, no repo,
no push, no submission (parent agent handles those).

## 2026-11-13 ~06:40 WIB — kit & spec
- Fetched kit tarball from https://make.fun/c/cutest-picture-01/kit
  (4,545,828 bytes) and unpacked it. Read RULES.txt (337 lines, authoritative)
  and kit.json.
- Key facts:
  - Program: Node 22 main.ts OR Python 3.13 main.py at repo root, stdlib
    only, nothing installed. Runs in a fresh container, no network,
    read-only /bot, writable /output, 1 CPU, 512 MB, 60 s.
  - Output: /output/entry.png, PNG or JPEG by magic bytes, ≤1 MiB,
    ≤1024×1024 px, whole image. Program runs twice; both runs must write
    the same bytes.
  - Judge: AI model, pairwise, no tie; criteria in order: cute at one
    glance (clear cute subject) > subject cute (soft round shapes, big
    bright eyes, chubby proportions, expression/pose) > charm (head tilt,
    tiny accessory, clumsy paws, two friends cuddling) > craft (clean,
    right limb/eye/ear counts, no smears/artefacts/garbled text) >
    reads small (~300 px).
  - Prizes: 1st $50, 2nd $35, 3rd $25, 4th–10th $10, 11th–20th $7.
  - Transcript gate: thinking_reproduces ≥30% counted lines, entrypoint
    ≥1 authored line; thinking_revised ≥2 assistant messages writing/
    editing some file. min_authored_coverage 0.
  - Starter is a pixel-art chick (main.ts copies entry.png) — a starting
    point, not a winner; a different subject was chosen.
- Decision: Python 3.13 main.py, stdlib only. Subject: one giant chubby
  baby kitten face (distinct from the starter chick; hits every judge
  criterion). Procedural SDF drawing + hand-rolled PNG encoder, since
  stdlib has no image library.

## 2026-11-13 ~06:43 WIB — first build (main.py, write #1)
- Wrote main.py (~13.9 KB): Canvas class (per-pixel blend, fill_circle /
  fill_ellipse / fill_triangle with SDF coverage, stroke_curve /
  disc_along for Bezier curves), scene (gradient background + jittered
  polka dots with fixed seed, ground shadow, head group rotated 5°,
  ears, head, tuft, bow, blush, huge amber eyes with double highlights,
  pink nose, "w" mouth, whiskers, paws), PNG writer (zlib level 9,
  IHDR/IDAT/IEND + CRC32), main() reading MAKEFUN_OUTPUT_DIR (default
  /output).
- Ran twice: 76,417 bytes, 1024×1024 RGBA, byte-identical sha256
  700b5de1f531efea, ~1.7 s per run.

## 2026-11-13 ~06:45 WIB — visual inspection #1, issues found
- Viewed out/entry.png. Cute overall (eyes, nose, mouth, blush, whiskers,
  paws all read), but: (1) ears mostly hidden behind the head circle
  (drawn before it) — only pink tips peeked out; the bow floated above
  the head; (2) whiskers looked dotted (too few Bezier samples).

## 2026-11-13 ~06:47 WIB — revision #1 (main.py, edit #1 + #2)
- Moved ear drawing to after the head (same cream, invisible seam) with a
  soft shade outline so ears read against the background; inner ear kept
  short so it stays above the head's silhouette edge; bow tightened;
  tuft enlarged slightly.
- Smoothed curves: whisker samples 16→30, mouth 12→20, toes 8→14.
- Re-ran twice: 85,323 bytes, deterministic (sha256 ac17315392b06bb5).

## 2026-11-13 ~06:49 WIB — visual inspection #2, issue found
- Whiskers now smooth, but the ears looked like wireframe triangles with
  blobs at the corners: triangle rounding values (26–30) were far too
  large relative to the small ear triangles, ballooning each corner into
  a circle.

## 2026-11-13 ~06:50 WIB — revision #2 (rounding patch)
- Reduced all triangle corner rounding: ears 30/26→12/10, inner ear
  18→7, tuft 14→8, bow 10/8→6/5, nose 12→8.
- Re-ran twice: 80,477 bytes, deterministic (sha256 cc5b855952829192).

## 2026-11-13 ~06:51 WIB — visual inspection #3, issue found
- Corner blobs smaller but ears still read as wireframes: the cream ear
  fill is nearly the same colour as the head and the background, so only
  the tan outline, the corner dots and the pink inner ear were visible.

## 2026-11-13 ~06:52 WIB — revision #3 (main.py, edits)
- Added warm ear colour EAR (255, 226, 190), distinct from fur and
  background; outline triangle now scaled 1.09× around its centroid for
  a real border; nose rounding 8→4 (removed its corner dots).
- Re-ran twice: 80,083 bytes, deterministic (sha256 15df8c57b067ff06).

## 2026-11-13 ~06:53 WIB — visual inspection #4, final validation
- Viewed out/entry.png: ears now read as proper ears (warm tan triangles
  with pink inner ears, bow sitting on the right ear), nose a clean pink
  triangle, everything else as before. Picture accepted as final.
- Strict PNG validation (chunk walk): all CRCs pass, IEND at exactly the
  file size, IDAT decompresses to exactly 4,195,328 bytes, all rows
  filter 0. 1024×1024, 8-bit RGBA, 80,083 bytes (limit 1,048,576).
- Determinism: two runs byte-identical.
- Runtime ~1.8 s per run (limit 60 s).
- Default output path verified: with MAKEFUN_OUTPUT_DIR unset, writes
  /output/entry.png (created and checked, then removed).
- Deliverables written: main.py, summary.md, work-log.md, README.md,
  LICENSE (MIT), preview.png (reference render).
