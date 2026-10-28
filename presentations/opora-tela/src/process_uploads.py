"""Turn the user's uploaded Higgsfield images into deck-ready files:
remove the «HIGGSFIELD AI» watermark, chroma-key the mascot poses."""
import os, sys
import cv2
import numpy as np
from PIL import Image, ImageFilter

SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
MAP = {
    "0bc59ecd": "tent", "0f505d00": "mascot_tablet", "14f59f9a": "jelly", "21933851": "food", "2fc314d7": "mannequin",
    "3076caef": "mascot_posture", "36d4c70d": "posture_bad", "3befafcb": "skeleton", "44b02b8d": "posture_good",
    "67459724": "museum", "6cf56efb": "mascot_flex", "769e4175": "mascot_think", "853538cc": "mascot_shrug",
    "8c91a187": "mascot_joy", "94f400d3": "mascot_popcorn", "98e5eeca": "mascot_point", "ad3f6dad": "records",
    "ae1da9d3": "mascot_wave", "bbd6e799": "cinema", "c246d920": "arm", "fc9ee70f": "sport",
}


def watermark_box(a):
    """Find the yellow-green «AI» badge in the bottom-right corner and return the whole logo box."""
    H, W = a.shape[:2]
    y0, x0 = int(H * 0.85), int(W * 0.55)
    reg = a[y0:, x0:].astype(int)
    r, g, b = reg[..., 0], reg[..., 1], reg[..., 2]
    m = (r > 150) & (r < 245) & (g > 215) & (b < 110) & (g - r > 15)
    ys, xs = np.nonzero(m)
    if len(xs) < 50:
        raise RuntimeError("badge not found")
    bx1, bx2 = xs.min() + x0, xs.max() + x0
    by1, by2 = ys.min() + y0, ys.max() + y0
    bw, bh = bx2 - bx1, by2 - by1
    return (int(bx1 - 5.3 * bw), int(by1 - 0.35 * bh), int(bx2 + 0.35 * bw), int(by2 + 0.45 * bh))


def key_green(a, box):
    a = a.copy()
    x1, y1, x2, y2 = box
    a[y1:y2, x1:x2] = np.median(a[:40, :40].reshape(-1, 3), axis=0)  # paint logo with the backdrop green
    f = a.astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    green = g - np.maximum(r, b)
    alpha = np.clip(1 - (green - 30) / 70, 0, 1)
    g2 = np.where(green > 0, np.maximum(r, b) + np.clip(green, 0, 10) * (alpha > 0.5), g)
    rgba = np.dstack([r, g2, b, alpha * 255]).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")
    al = img.getchannel("A").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.7))
    img.putalpha(al)
    bbox = img.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    img = img.crop(bbox)
    # soft contact shadow under the feet
    pad = int(img.height * 0.06)
    canvas = Image.new("RGBA", (img.width, img.height + pad), (0, 0, 0, 0))
    sh = Image.new("L", canvas.size, 0)
    from PIL import ImageDraw
    cx, cy = img.width / 2, img.height - pad * 0.15
    ImageDraw.Draw(sh).ellipse([cx - img.width * 0.36, cy - pad * 0.55, cx + img.width * 0.36, cy + pad * 0.55], fill=95)
    sh = sh.filter(ImageFilter.GaussianBlur(pad * 0.45))
    shadow = Image.new("RGBA", canvas.size, (43, 34, 110, 255))
    shadow.putalpha(sh)
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(img, (0, 0))
    return canvas


def clean_scene(a, box):
    x1, y1, x2, y2 = box
    mask = np.zeros(a.shape[:2], np.uint8)
    mask[max(0, y1):y2, max(0, x1):x2] = 255
    bgr = cv2.cvtColor(a, cv2.COLOR_RGB2BGR)
    res = cv2.inpaint(bgr, mask, 11, cv2.INPAINT_TELEA)
    return cv2.cvtColor(res, cv2.COLOR_BGR2RGB)


os.makedirs(OUT, exist_ok=True)
for fn in sorted(os.listdir(SRC)):
    key = MAP.get(fn[:8])
    if not key:
        continue
    a = np.asarray(Image.open(os.path.join(SRC, fn)).convert("RGB"))
    box = watermark_box(a)
    STD = {(768, 1376): (1055, 694, 1361, 757), (1200, 896): (566, 1111, 892, 1177), (1024, 1024): (640, 933, 1019, 1008),
           (896, 1200): (831, 812, 1190, 884)}
    if box[2] - box[0] > 450 and a.shape[:2] in STD:  # badge search fooled by yellow-green scenery
        box = STD[a.shape[:2]]
    if key.startswith("mascot"):
        key_green(a, box).save(os.path.join(OUT, key + ".png"))
    elif key in ("mannequin", "arm", "skeleton"):  # plain backdrop: paint the logo away
        Image.fromarray(clean_scene(a, box)).save(os.path.join(OUT, key + ".jpg"), quality=93)
    else:  # textured scenery: cut off the strip that carries the logo
        Image.fromarray(a[: box[1] - 4]).save(os.path.join(OUT, key + ".jpg"), quality=93)
        np.save(os.path.join(OUT, key + "_wm.npy"), np.array(box))
    print("ok", key, box)
