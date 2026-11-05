"""Clean INNOVATION chevron decals (TASK-1.28), orange #e5663a, transparent background.
chevron_large: 1.5 x 2.1 m, chevron_innovation: 1.3 x 1.8 m with black INNOVATION text in the notch."""
import os
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORANGE = (229, 102, 58, 255)
PPM = 400
SS = 2

def chev(w_m, h_m, text=None):
    w, h = int(w_m * PPM), int(h_m * PPM)
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    pts = [(0, 0), (0.40 * W, 0), (W, 0.5 * H), (0.40 * W, H), (0, H), (0.60 * W, 0.5 * H)]
    d.polygon([(x, y) for x, y in pts], fill=ORANGE)
    if text:
        f = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(0.062 * PPM * SS), index=1)
        tw = d.textlength(text, font=f)
        d.text((0.07 * W + 0.0 * tw, 0.5 * H), text, font=f, fill=(20, 20, 20, 255), anchor="lm")
    return im.resize((w, h), Image.LANCZOS)

for name, args in (("chevron_large", (1.5, 2.1)), ("chevron_innovation", (1.3, 1.8, "INNOVATION"))):
    p = os.path.join(ROOT, "assets/decals", name + ".png")
    chev(*args).save(p); print("saved", p)
