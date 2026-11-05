"""Window view plate (TASK-1.28): hazy city outside the window wall -> assets/decals/window_backdrop.jpg.
Sky gradient + procedural hazy towers + tree band + parked-car lot tiled from photo 08 (2) (left window pane).
Plate covers game x -30..42 (72 m), y -14..31 (45 m) at z=-30 (see blender/materials.py)."""
import random, os, math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PH = os.path.join(ROOT, "references/img/photos/WhatsApp Image 2026-11-05 at 15.25.08 (2).jpeg")
W, H = 2304, 1440          # 32 px/m
PPM = W / 72.0
rng = random.Random(5)
img = Image.new("RGB", (W, H))
d = ImageDraw.Draw(img)

def row(y_m):  # world y (m) -> pixel row
    return int(H - (y_m + 14) * PPM)

# sky: blue at the top, pale haze at the horizon (y ~ 8 m)
for y in range(H):
    t = min(1.0, max(0.0, (row(8) - y) / (row(8) - 0)))
    c = [int(a + (b - a) * t) for a, b in zip((222, 232, 238), (126, 172, 222))]
    d.line([(0, y), (W, y)], fill=tuple(c))

# hazy towers
for _ in range(46):
    w = rng.uniform(5, 12); h = rng.uniform(10, 38)
    x = rng.uniform(0, 72 - w)
    hz = rng.uniform(0.35, 0.75)  # haze: farther = closer to the sky colour
    base = rng.choice([(176, 178, 182), (196, 184, 168), (160, 168, 180), (214, 210, 200), (150, 154, 160)])
    col = tuple(int(c * (1 - hz) + s * hz) for c, s in zip(base, (214, 226, 236)))
    x0, x1, y0, y1 = int(x * PPM), int((x + w) * PPM), row(-4 + h), row(-4)
    d.rectangle([x0, y0, x1, y1], fill=col)
    win = tuple(int(c * 0.93) for c in col)
    lit = tuple(min(255, int(c * 1.03)) for c in col)
    for yy in range(y0 + 10, y1 - 8, 22):
        d.line([(x0, yy), (x1, yy)], fill=lit, width=3)
        for xx in range(x0 + 8, x1 - 10, 20):
            d.rectangle([xx, yy + 5, xx + 11, yy + 16], fill=win)
img = img.filter(ImageFilter.GaussianBlur(3.2)); d = ImageDraw.Draw(img)

# tree band, y -6 .. 6 m
d.rectangle([0, row(3), W, row(-6)], fill=(70, 92, 56))
for _ in range(2600):
    cx = rng.uniform(0, W); cy = row(rng.uniform(-6, 5.5)); r = rng.uniform(7, 20)
    g = rng.randint(78, 120)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(g - 18, g + rng.randint(2, 18), g - 34))
img = img.filter(ImageFilter.GaussianBlur(2.4)); d = ImageDraw.Draw(img)

# ground behind the cars (dusty lot), y -14 .. -3
d.rectangle([0, row(-3.5), W, H], fill=(150, 138, 120))

# parked cars: tile the clean left pane of the window photo, alternate mirroring, jitter brightness
src = Image.open(PH)
k = src.size[0] / 900
pane = src.crop((int(2 * k), int(378 * k), int(88 * k), int(560 * k)))   # cars through the first window
pane = ImageEnhance.Contrast(pane).enhance(1.1)
th = row(-3.5) - 0
th = H - row(-3.5)
th = int(th)
pane = pane.resize((int(pane.width * th / pane.height), th), Image.LANCZOS)
x = -rng.randint(0, pane.width)
flip = False
while x < W:
    p = pane
    p = ImageEnhance.Brightness(p).enhance(rng.uniform(0.9, 1.08))
    img.paste(p, (x, H - th))
    x += pane.width - rng.randint(10, 40)
img = img.filter(ImageFilter.GaussianBlur(0.8))
img = ImageEnhance.Brightness(img).enhance(1.05)
out = os.path.join(ROOT, "assets/decals/window_backdrop.jpg")
img.save(out, quality=86)
print("saved", out, img.size)
