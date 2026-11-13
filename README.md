# Cutest picture — make.fun `cutest-picture-01`

A chubby baby kitten, drawn procedurally in pure Python.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (1024x1024 PNG, ~80 KB, deterministic)
```

`main.py` is Python 3.13 standard library only — no packages, no network.
It writes `$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output/entry.png`).

## The picture

One giant kitten face: cream fur, warm tan ears with pink inner ears, a
little pink bow, a slight head tilt, huge amber eyes with bright
highlights, a tiny pink nose, blush cheeks, whiskers, and two paws peeking
up at the bottom — on a soft peach background with faint polka dots.
See `preview.png` for a reference render.

## Files

- `main.py` — the entry program (the only code file the repo needs).
- `summary.md` — method, why it should win, validation results.
- `work-log.md` — timestamped build log.
- `LICENSE` — MIT.
