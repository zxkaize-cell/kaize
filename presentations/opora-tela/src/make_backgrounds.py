"""Designer backgrounds: soft mesh gradients with film grain, and blurred photo heroes."""
import os
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")
IMG = os.path.join(HERE, "img")
W, H = 1920, 1080
rng = np.random.default_rng(7)


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def mesh(base, blobs):
    """blobs: (cx, cy, radius, colour, strength) in 0..1 slide units."""
    ys, xs = np.mgrid[0:H, 0:W]
    xs, ys = xs / W, ys / H * (H / W)
    img = np.ones((H, W, 3)) * hexc(base)
    for cx, cy, r, col, s in blobs:
        d2 = (xs - cx) ** 2 + (ys - cy * H / W) ** 2
        wgt = np.exp(-d2 / (2 * (r ** 2))) * s
        img = img * (1 - wgt[..., None]) + hexc(col) * wgt[..., None]
    return img


def finish(arr, name, grain=5.0, vignette=0.0):
    if vignette:
        ys, xs = np.mgrid[0:H, 0:W]
        d = np.sqrt(((xs - W / 2) / (W / 2)) ** 2 + ((ys - H / 2) / (H / 2)) ** 2)
        arr = arr * (1 - vignette * np.clip(d - 0.55, 0, 1)[..., None])
    noise = rng.normal(0, grain, (H, W, 1))
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    Image.fromarray(arr).save(os.path.join(OUT, name), quality=93)


finish(mesh("#EEF4FF", [(0.0, 0.0, 0.32, "#B7D6FF", 0.95), (1.0, 0.05, 0.3, "#BDEEDC", 0.9),
                        (1.0, 1.0, 0.34, "#D3C6FF", 0.95), (0.0, 1.0, 0.3, "#FFDCA8", 0.9),
                        (0.55, 0.5, 0.35, "#FFFFFF", 0.35)]), "bg2_sky.jpg")
finish(mesh("#F1ECFF", [(0.0, 0.0, 0.32, "#CBBBFF", 0.95), (1.0, 0.0, 0.3, "#BBDCFF", 0.9),
                        (1.0, 1.0, 0.32, "#FFC9DA", 0.9), (0.05, 1.0, 0.3, "#D5F3EA", 0.7),
                        (0.5, 0.5, 0.35, "#FFFFFF", 0.35)]), "bg2_lilac.jpg")
finish(mesh("#ECFAF4", [(0.0, 0.0, 0.32, "#AEEBD4", 0.95), (1.0, 0.0, 0.3, "#C0E1FF", 0.9),
                        (1.0, 1.0, 0.3, "#FFE7A8", 0.9), (0.0, 1.0, 0.3, "#D9F7EE", 0.7),
                        (0.5, 0.5, 0.35, "#FFFFFF", 0.35)]), "bg2_mint.jpg")
finish(mesh("#FFF4EE", [(0.0, 0.0, 0.32, "#FFC8B6", 0.95), (1.0, 0.0, 0.3, "#FFE09C", 0.9),
                        (1.0, 1.0, 0.32, "#E8CCFF", 0.9), (0.0, 1.0, 0.3, "#FFE3D6", 0.7),
                        (0.5, 0.5, 0.35, "#FFFFFF", 0.35)]), "bg2_peach.jpg")
finish(mesh("#FFF3D2", [(0.0, 0.0, 0.34, "#FFE08C", 0.9), (1.0, 0.0, 0.32, "#FFC9A6", 0.85),
                        (1.0, 1.0, 0.32, "#FFE7B0", 0.85), (0.0, 1.0, 0.3, "#FFD6C2", 0.8),
                        (0.5, 0.5, 0.35, "#FFF9EA", 0.45)]), "bg2_sun.jpg")


def hero(src, name, tint, left_alpha, right_alpha, blur=26, crop=None, brightness=1.0):
    im = Image.open(os.path.join(IMG, src)).convert("RGB")
    if crop:
        im = im.crop(crop)
    ar = W / H
    iw, ih = im.size
    if iw / ih > ar:
        nw = int(ih * ar)
        im = im.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
    else:
        nh = int(iw / ar)
        im = im.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
    im = im.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(blur))
    arr = np.asarray(im).astype(float) * brightness
    xs = np.linspace(0, 1, W)[None, :, None]
    a = left_alpha + (right_alpha - left_alpha) * xs
    arr = arr * (1 - a) + hexc(tint) * a
    finish(arr, name, grain=6.0, vignette=0.25)


hero("museum.jpg", "bg2_hero.jpg", "#1C1650", 0.86, 0.45)
hero("museum.jpg", "bg2_hero_end.jpg", "#241A63", 0.80, 0.55, blur=34)
hero("cinema.jpg", "bg2_cinema.jpg", "#14102E", 0.78, 0.55, blur=30)
print("ok")
