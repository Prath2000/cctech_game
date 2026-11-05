#!/usr/bin/env python3
"""Rectify decals from the reference photos (Pillow only) -> assets/decals/*.png (committed).
Quad corners are in a preview scale (long side 700 px) as TL,TR,BR,BL in the photo; they map to the output rectangle.
Run: pnpm build:decals
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PH = os.path.join(ROOT, "references", "img", "photos")
OUT = os.path.join(ROOT, "assets", "decals")
P = lambda s: os.path.join(PH, f"WhatsApp Image 2026-11-05 at {s}.jpeg")

def solve(A, b):
    n = len(b)
    M = [r[:] + [b[i]] for i, r in enumerate(A)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(M[r][i])); M[i], M[p] = M[p], M[i]
        for r in range(n):
            if r != i:
                f = M[r][i] / M[i][i]
                M[r] = [x - f * y for x, y in zip(M[r], M[i])]
    return [M[i][n] / M[i][i] for i in range(n)]

def rectify(im, quad, size):
    """quad (TL,TR,BR,BL) in im pixels -> size (w,h) image (PIL wants the inverse map out->in)."""
    w, h = size
    dst = [(0, 0), (w, 0), (w, h), (0, h)]
    A, b = [], []
    for (x, y), (u, v) in zip(dst, quad):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return im.transform(size, Image.PERSPECTIVE, solve(A, b), Image.BICUBIC)

def feather(im, px):
    """Soft alpha edge so the decal blends into the plaster."""
    w, h = im.size
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rectangle([px, px, w - px, h - px], fill=255)
    im = im.convert("RGBA")
    from PIL import ImageChops
    im.putalpha(ImageChops.multiply(im.getchannel("A"), m.filter(ImageFilter.GaussianBlur(px / 2))))
    return im

def key_wall(im):
    """Make the plaster background transparent: keep saturated (orange) and dark (text) pixels."""
    import colorsys
    px = im.convert("RGB"); out = px.convert("RGBA"); a = out.load(); src = px.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = src[x, y]
            mx, mn = max(r, g, b), min(r, g, b)
            sat = (mx - mn) / max(mx, 1)
            al = max(min(1.0, (sat - 0.12) * 5), min(1.0, max(0.0, (110 - mx) / 50)))
            a[x, y] = (r, g, b, int(255 * al))
    return out

def make(name, photo, quad, size, preview=700, rot=0, edge=0, tweak=None):
    im = Image.open(P(photo)).convert("RGB")
    s = max(im.size) / preview
    q = [(x * s, y * s) for x, y in quad]
    out = rectify(im, q, size)
    if tweak: out = tweak(out)
    out = feather(out, edge) if edge else out
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, name + ".png"), optimize=True)
    print(name, out.size)

if __name__ == "__main__":
    # yellow sticky note on the granite (07, sink photo); square ~10 cm
    make("sticky_note", "15.25.07", [(274, 275), (315, 297), (289, 317), (240, 291)], (256, 256),
         tweak=lambda i: ImageEnhance.Brightness(i).enhance(0.95))
    # B'ONE print on the carton (06 (1)); text runs bottom->top so rotate it upright
    make("bone_sign", "15.25.06 (1)", [(564, 206), (564, 118), (592, 120), (592, 204)], (512, 160),
         tweak=lambda i: ImageEnhance.Contrast(i).enhance(1.2))
    # orange INNOVATION chevron wall (08 (3)): small chevron with text, large chevron
    make("chevron_innovation", "15.25.08 (3)", [(243, 124), (325, 124), (325, 220), (243, 220)], (400, 470), edge=2, tweak=key_wall)
    make("chevron_large", "15.25.08 (3)", [(334, 124), (424, 124), (424, 246), (334, 246)], (440, 610), edge=2, tweak=key_wall)
    # circuit-arrow mural (08); the lower right is hidden behind the vending machine in the photo
    make("mural_circuit_arrow", "15.25.08", [(50, 52), (412, 52), (412, 308), (50, 308)], (1024, 724), edge=10)
