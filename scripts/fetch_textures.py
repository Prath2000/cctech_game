#!/usr/bin/env python3
"""Download CC0 PBR textures into assets/raw/<source>/<id>/ (gitignored, idempotent).
Run: pnpm fetch:textures   (uses python3 stdlib only)
Files are normalised to color.jpg, normal.jpg, rough.jpg [, metal.jpg | arm.jpg].
"""
import io, json, os, urllib.request, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "assets", "raw")
UA = {"User-Agent": "cctech-game-fetch/1.0"}

POLYHAVEN = ["large_grey_tiles", "white_plaster_02"]
AMBIENTCG = ["Granite005A", "Metal012", "Metal050A", "OfficeCeiling005", "Plastic013A"]

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()

def polyhaven(tid):
    out = os.path.join(RAW, "polyhaven", tid)
    if os.path.exists(os.path.join(out, "color.jpg")):
        return print("skip", tid)
    os.makedirs(out, exist_ok=True)
    files = json.loads(get(f"https://api.polyhaven.com/files/{tid}"))
    for key, name in (("Diffuse", "color"), ("nor_gl", "normal"), ("Rough", "rough"), ("arm", "arm")):
        if key in files:
            url = files[key]["2k"]["jpg"]["url"]
            open(os.path.join(out, name + ".jpg"), "wb").write(get(url))
    print("got", tid)

def ambientcg(tid):
    out = os.path.join(RAW, "ambientcg", tid)
    if os.path.exists(os.path.join(out, "color.jpg")):
        return print("skip", tid)
    os.makedirs(out, exist_ok=True)
    z = zipfile.ZipFile(io.BytesIO(get(f"https://ambientcg.com/get?file={tid}_2K-JPG.zip")))
    names = {"_Color.jpg": "color", "_NormalGL.jpg": "normal", "_Roughness.jpg": "rough", "_Metalness.jpg": "metal"}
    for n in z.namelist():
        for suf, dst in names.items():
            if n.endswith(suf):
                open(os.path.join(out, dst + ".jpg"), "wb").write(z.read(n))
    print("got", tid)

if __name__ == "__main__":
    for t in POLYHAVEN: polyhaven(t)
    for t in AMBIENTCG: ambientcg(t)
