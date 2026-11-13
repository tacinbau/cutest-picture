#!/usr/bin/env python3
"""Cutest picture entry: a chubby baby kitten, drawn procedurally.

Pure Python 3.13 standard library only (no network, no installed packages).
Writes one 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).

The picture is rendered with signed-distance-field shapes so every edge is
smoothly anti-aliased, and the whole render is deterministic: the same bytes
on every run. A hand-rolled PNG encoder (zlib + struct + binascii) writes the
file; no image library is used or needed.

Subject: one giant kitten face, slightly head-tilted, huge bright eyes, tiny
pink nose, blush cheeks, whiskers, a little pink bow on one ear and two paws
peeking up at the bottom edge -- cute at one glance, clean, and readable at
300 px across.
"""

import binascii
import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- colors
CREAM = (255, 247, 234)      # kitten fur
CREAM_SHADE = (245, 220, 185)  # fur shading
EAR = (255, 226, 190)         # ears: warm cream, distinct from fur and background
PINK_INNER = (255, 182, 201)  # inner ear
PINK_NOSE = (255, 143, 163)   # nose
PINK_BOW = (255, 127, 168)    # bow
PINK_BOW_DARK = (230, 95, 140)
BLUSH = (255, 179, 193)
EYE_DARK = (61, 35, 20)       # iris / pupil
EYE_AMBER = (201, 138, 58)    # iris ring
WHITE = (255, 255, 255)
LINE = (122, 90, 70)          # mouth / whiskers / toes
SHADOW = (232, 201, 168)      # ground shadow
BG_TOP = (255, 233, 214)      # background gradient top
BG_BOT = (255, 249, 240)      # background gradient bottom
DOT = (255, 216, 190)         # background polka dots


def clamp01(x):
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def coverage(d, band=1.0):
    """Anti-aliased coverage of a signed distance: 1 inside, 0 outside."""
    return clamp01(0.5 - d / band)


def sd_circle(px, py, cx, cy, r):
    return math.hypot(px - cx, py - cy) - r


def sd_ellipse(px, py, cx, cy, rx, ry):
    # Approximate SDF for an ellipse (scaled-circle distance, good for AA).
    dx = (px - cx) / rx
    dy = (py - cy) / ry
    return (math.hypot(dx, dy) - 1.0) * min(rx, ry)


def sd_triangle(px, py, ax, ay, bx, by, cx, cy):
    # Signed distance to a triangle (Inigo Quilez).
    pax = px - ax
    pay = py - ay
    bax = bx - ax
    bay = by - ay
    cax = cx - ax
    cay = cy - ay
    pax2 = pax * pax + pay * pay
    v1 = bax * pax + bay * pay
    v2 = cax * pax + cay * pay
    den = (bax * cax + bay * cay) ** 2 - (bax * bax + bay * bay) * (cax * cax + cay * cay)
    if den == 0.0:
        return math.hypot(px - ax, py - ay)
    t = (v1 * (bax * cax + bay * cay) - v2 * (bax * bax + bay * bay)) / den
    s = (v2 * (bax * cax + bay * cay) - v1 * (cax * cax + cay * cay)) / den
    if t >= 0.0 and s >= 0.0 and t + s <= 1.0:
        # Inside: distance to nearest edge (negative).
        d1 = abs((bx - ax) * pay - (by - ay) * pax) / math.hypot(bx - ax, by - ay)
        d2 = abs((cx - bx) * (py - by) - (cy - by) * (px - bx)) / math.hypot(cx - bx, cy - by)
        d3 = abs((ax - cx) * (py - cy) - (ay - cy) * (px - cx)) / math.hypot(ax - cx, ay - cy)
        return -min(d1, d2, d3)
    # Outside: distance to nearest vertex.
    d = min(
        math.hypot(px - ax, py - ay),
        math.hypot(px - bx, py - by),
        math.hypot(px - cx, py - cy),
    )
    return d


def sd_round_box(px, py, cx, cy, hx, hy, r):
    qx = abs(px - cx) - hx + r
    qy = abs(py - cy) - hy + r
    ox = qx if qx > 0 else 0.0
    oy = qy if qy > 0 else 0.0
    return math.hypot(ox, oy) + (qx if qx < qy else qy) - r


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 4)

    def set(self, x, y, r, g, b, a=255):
        i = (y * self.w + x) * 4
        self.px[i] = r
        self.px[i + 1] = g
        self.px[i + 2] = b
        self.px[i + 3] = a

    def blend(self, x, y, r, g, b, alpha):
        """Blend colour over the pixel with the given coverage*opacity (0..1)."""
        if alpha <= 0.0:
            return
        i = (y * self.w + x) * 4
        if alpha >= 1.0:
            self.px[i] = r
            self.px[i + 1] = g
            self.px[i + 2] = b
            self.px[i + 3] = 255
            return
        inv = 1.0 - alpha
        self.px[i] = int(r * alpha + self.px[i] * inv + 0.5)
        self.px[i + 1] = int(g * alpha + self.px[i + 1] * inv + 0.5)
        self.px[i + 2] = int(b * alpha + self.px[i + 2] * inv + 0.5)
        self.px[i + 3] = 255

    def fill_circle(self, cx, cy, r, color, alpha=1.0, band=1.0):
        x0 = max(0, int(cx - r - band - 1))
        x1 = min(self.w - 1, int(cx + r + band + 1))
        y0 = max(0, int(cy - r - band - 1))
        y1 = min(self.h - 1, int(cy + r + band + 1))
        cr, cg, cb = color
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                d = sd_circle(x + 0.5, y + 0.5, cx, cy, r)
                c = coverage(d, band)
                if c > 0.0:
                    self.blend(x, y, cr, cg, cb, c * alpha)

    def fill_ellipse(self, cx, cy, rx, ry, color, alpha=1.0, band=1.0):
        x0 = max(0, int(cx - rx - band - 1))
        x1 = min(self.w - 1, int(cx + rx + band + 1))
        y0 = max(0, int(cy - ry - band - 1))
        y1 = min(self.h - 1, int(cy + ry + band + 1))
        cr, cg, cb = color
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                d = sd_ellipse(x + 0.5, y + 0.5, cx, cy, rx, ry)
                c = coverage(d, band)
                if c > 0.0:
                    self.blend(x, y, cr, cg, cb, c * alpha)

    def fill_triangle(self, a, b, c, color, alpha=1.0, band=1.0, rounding=0.0):
        xs = (a[0], b[0], c[0])
        ys = (a[1], b[1], c[1])
        x0 = max(0, int(min(xs) - band - rounding - 1))
        x1 = min(self.w - 1, int(max(xs) + band + rounding + 1))
        y0 = max(0, int(min(ys) - band - rounding - 1))
        y1 = min(self.h - 1, int(max(ys) + band + rounding + 1))
        cr, cg, cb = color
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                d = sd_triangle(x + 0.5, y + 0.5, a[0], a[1], b[0], b[1], c[0], c[1]) - rounding
                cov = coverage(d, band)
                if cov > 0.0:
                    self.blend(x, y, cr, cg, cb, cov * alpha)

    def stroke_curve(self, pts, radius, color, alpha=1.0):
        """Draw a thick polyline through pts (list of (x, y)) as discs."""
        cr, cg, cb = color
        for (x, y) in pts:
            self.fill_circle(x, y, radius, (cr, cg, cb), alpha, band=1.0)

    def disc_along(self, p0, p1, p2, n, radius, color, alpha=1.0):
        """Quadratic Bezier p0->p1->p2 sampled with n discs."""
        pts = []
        for i in range(n + 1):
            t = i / n
            u = 1.0 - t
            x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
            y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
            pts.append((x, y))
        self.stroke_curve(pts, radius, color, alpha)


# ---------------------------------------------------------------- scene
TILT = math.radians(5.0)          # head tilt (charm)
HCX, HCY = 512.0, 545.0           # head centre
HEAD_R = 330.0


def rot(px, py):
    """Rotate a point around the head centre by -TILT (head frame)."""
    dx = px - HCX
    dy = py - HCY
    c = math.cos(-TILT)
    s = math.sin(-TILT)
    return (HCX + dx * c - dy * s, HCY + dx * s + dy * c)


def draw(c):
    # --- background: vertical gradient ---
    for y in range(H):
        t = y / (H - 1)
        r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t + 0.5)
        g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t + 0.5)
        b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t + 0.5)
        base = y * W * 4
        for x in range(W):
            i = base + x * 4
            c.px[i] = r
            c.px[i + 1] = g
            c.px[i + 2] = b
            c.px[i + 3] = 255

    # --- background polka dots (deterministic jittered grid, very soft) ---
    seed = 1234567

    def rnd():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        return seed / 0x7FFFFFFF

    for gy in range(0, H + 128, 128):
        for gx in range(0, W + 128, 128):
            jx = (rnd() - 0.5) * 60
            jy = (rnd() - 0.5) * 60
            # keep dots away from the face so nothing crowds the subject
            dx = gx + jx - HCX
            dy = gy + jy - HCY
            if dx * dx + dy * dy < 400.0 * 400.0:
                continue
            c.fill_circle(gx + jx, gy + jy, 13.0, DOT, alpha=0.55, band=1.0)

    # --- ground shadow ---
    c.fill_ellipse(512, 972, 370, 42, SHADOW, alpha=0.55, band=10.0)

    # --- head group (rotated frame) ---
    # head first, then ears on top of it: same cream, so the seam is invisible,
    # and a soft shade outline keeps the ears readable against the background.
    c.fill_circle(HCX, HCY, HEAD_R, CREAM, alpha=1.0, band=1.0)
    # soft warm shading on the lower-right of the head
    c.fill_ellipse(HCX + 150, HCY + 190, 240, 170, CREAM_SHADE, alpha=0.35, band=24.0)
    # forehead tuft
    tip = rot(HCX + 6, HCY - HEAD_R - 26)
    bl = rot(HCX - 40, HCY - HEAD_R + 36)
    br = rot(HCX + 50, HCY - HEAD_R + 32)
    c.fill_triangle(tip, bl, br, CREAM, alpha=1.0, band=1.0, rounding=8.0)

    # ears: rounded triangles, shade outline (scaled up), warm ear, pink inner
    def expand(tri, f):
        cx = sum(p[0] for p in tri) / 3.0
        cy = sum(p[1] for p in tri) / 3.0
        return [(cx + (p[0] - cx) * f, cy + (p[1] - cy) * f) for p in tri]

    for sgn in (-1.0, 1.0):
        ex = HCX + sgn * 195.0
        ey = HCY - 268.0
        tri = [rot(ex + sgn * 26.0, ey - 98.0),
               rot(ex - 72.0, ey + 58.0),
               rot(ex + 72.0, ey + 58.0)]
        out = expand(tri, 1.09)
        c.fill_triangle(out[0], out[1], out[2], CREAM_SHADE, alpha=1.0, band=1.0, rounding=10.0)
        c.fill_triangle(tri[0], tri[1], tri[2], EAR, alpha=1.0, band=1.0, rounding=8.0)
        # inner ear kept short so it stays above the head's silhouette edge
        tip2 = rot(ex + sgn * 22.0, ey - 62.0)
        base_l2 = rot(ex - 46.0, ey + 8.0)
        base_r2 = rot(ex + 46.0, ey + 8.0)
        c.fill_triangle(tip2, base_l2, base_r2, PINK_INNER, alpha=1.0, band=1.0, rounding=7.0)

    # --- bow on the right ear (head frame) ---
    bx, by = rot(HCX + 238.0, HCY - 300.0)
    c.fill_triangle((bx - 72, by - 30), (bx - 72, by + 30), (bx - 8, by), PINK_BOW_DARK,
                    alpha=1.0, band=1.0, rounding=6.0)
    c.fill_triangle((bx + 72, by - 30), (bx + 72, by + 30), (bx + 8, by), PINK_BOW_DARK,
                    alpha=1.0, band=1.0, rounding=6.0)
    c.fill_triangle((bx - 64, by - 24), (bx - 64, by + 24), (bx - 6, by), PINK_BOW,
                    alpha=1.0, band=1.0, rounding=5.0)
    c.fill_triangle((bx + 64, by - 24), (bx + 64, by + 24), (bx + 6, by), PINK_BOW,
                    alpha=1.0, band=1.0, rounding=5.0)
    c.fill_circle(bx, by, 21, PINK_BOW_DARK, alpha=1.0, band=1.0)
    c.fill_circle(bx, by, 15, PINK_BOW, alpha=1.0, band=1.0)

    # --- blush (soft, wide AA band) ---
    for sgn in (-1.0, 1.0):
        bx, by = rot(HCX + sgn * 252.0, HCY + 148.0)
        c.fill_ellipse(bx, by, 66, 42, BLUSH, alpha=0.5, band=8.0)

    # --- eyes: huge, bright, low on the face (baby proportions) ---
    for sgn in (-1.0, 1.0):
        ex, ey = rot(HCX + sgn * 148.0, HCY + 42.0)
        c.fill_circle(ex, ey, 96, EYE_DARK, alpha=1.0, band=1.0)
        c.fill_circle(ex, ey, 80, EYE_AMBER, alpha=1.0, band=1.0)
        c.fill_circle(ex, ey, 52, EYE_DARK, alpha=1.0, band=1.0)
        # big white highlight, top-left; small one, bottom-right
        c.fill_circle(ex - 30, ey - 34, 30, WHITE, alpha=1.0, band=1.0)
        c.fill_circle(ex + 26, ey + 30, 13, WHITE, alpha=1.0, band=1.0)

    # --- nose: tiny rounded triangle, pointing down ---
    nx, ny = rot(HCX, HCY + 168.0)
    c.fill_triangle((nx - 36, ny - 24), (nx + 36, ny - 24), (nx, ny + 34),
                    PINK_NOSE, alpha=1.0, band=1.0, rounding=4.0)

    # --- mouth: little "w" cat mouth under the nose ---
    mx, my = rot(HCX, HCY + 208.0)
    c.disc_along((mx, my), (mx - 26, my + 26), (mx - 56, my + 2), 20, 5.0, LINE, alpha=0.85)
    c.disc_along((mx, my), (mx + 26, my + 26), (mx + 56, my + 2), 20, 5.0, LINE, alpha=0.85)

    # --- whiskers: three soft curves each side ---
    for sgn in (-1.0, 1.0):
        wx, wy = rot(HCX + sgn * 300.0, HCY + 150.0)
        c.disc_along((wx, wy), (wx + sgn * 60, wy - 26), (wx + sgn * 132, wy - 34), 30, 3.0, LINE, alpha=0.55)
        c.disc_along((wx, wy + 22), (wx + sgn * 62, wy + 22), (wx + sgn * 136, wy + 22), 30, 3.0, LINE, alpha=0.55)
        c.disc_along((wx, wy + 44), (wx + sgn * 60, wy + 70), (wx + sgn * 132, wy + 82), 30, 3.0, LINE, alpha=0.55)

    # --- paws peeking up at the bottom edge ---
    for sgn in (-1.0, 1.0):
        px = 512 + sgn * 118.0
        c.fill_ellipse(px, 992, 112, 62, CREAM, alpha=1.0, band=1.0)
        c.fill_ellipse(px, 992, 112, 62, CREAM_SHADE, alpha=0.18, band=1.0)
        # two tiny toe lines on each paw
        c.disc_along((px - 34, 968), (px - 30, 984), (px - 34, 1000), 14, 3.5, LINE, alpha=0.6)
        c.disc_along((px + 34, 968), (px + 30, 984), (px + 34, 1000), 14, 3.5, LINE, alpha=0.6)


# ---------------------------------------------------------------- PNG writer
def png_chunk(kind, data):
    chunk = struct.pack(">I", len(data)) + kind + data
    chunk += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return chunk


def write_png(c, path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += c.px[y * W * 4:(y + 1) * W * 4]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += png_chunk(b"IHDR", ihdr)
    data += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += png_chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    canvas = Canvas(W, H)
    draw(canvas)
    size = write_png(canvas, os.path.join(out_dir, "entry.png"))
    print(f"wrote {os.path.join(out_dir, 'entry.png')} ({size} bytes)")


if __name__ == "__main__":
    main()
