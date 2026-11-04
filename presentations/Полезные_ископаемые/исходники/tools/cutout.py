"""Cut white/plain backgrounds from character, mineral and object images.
usage: python3 cutout.py <src_dir_or_files...>  (codes from file names: C1.png, P3.jpg, M5.webp ...)
Writes img/cut/<code>.png: transparent, trimmed, padded to 2:3 (characters) or 1:1 (minerals, objects)."""
import os, sys, glob
os.environ.setdefault("U2NET_HOME", os.path.join(os.path.dirname(__file__), "..", "models"))
from PIL import Image
from rembg import remove, new_session

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "img", "cut")
os.makedirs(OUT, exist_ok=True)
session = new_session("isnet-general-use")

def fit(img, aspect, pad=0.04, bottom=False):
    bbox = img.getbbox()
    img = img.crop(bbox)
    w, h = img.size
    W = max(w, int(h * aspect)) if aspect else w
    H = max(h, int(w / aspect)) if aspect else h
    W, H = int(W * (1 + pad * 2)), int(H * (1 + pad * 2))
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = (W - w) // 2
    y = (H - h - int(H * pad * 0.5)) if bottom else (H - h) // 2
    canvas.paste(img, (x, y), img)
    return canvas

def run(path):
    code = os.path.splitext(os.path.basename(path))[0].upper()
    src = Image.open(path).convert("RGBA")
    if src.getextrema()[3][0] < 250:  # already transparent
        cut = src
    else:
        cut = remove(src, session=session, alpha_matting=False, post_process_mask=True)
    if code.startswith(("C", "P")):
        out = fit(cut, 2 / 3, pad=0.03, bottom=True)
        out.thumbnail((1000, 1500))
    else:
        out = fit(cut, 1.0, pad=0.06)
        out.thumbnail((900, 900))
    out.save(os.path.join(OUT, code + ".png"), optimize=True)
    print("cut", code, out.size)

if __name__ == "__main__":
    files = []
    for a in sys.argv[1:]:
        files += sorted(glob.glob(os.path.join(a, "*"))) if os.path.isdir(a) else [a]
    for f in files:
        run(f)
