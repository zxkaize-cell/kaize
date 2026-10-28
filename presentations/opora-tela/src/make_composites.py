"""Raster compositions used as pictures in the deck: route tiles, hall tickets, goal card."""
import os
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
OUT = os.path.join(IMG, "comp")
os.makedirs(OUT, exist_ok=True)


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def gradient(w, h, c1, c2, c3=None):
    ys, xs = np.mgrid[0:h, 0:w]
    t = (xs / w * 0.6 + ys / h * 0.4)
    a = hexc(c1)[None, None] * (1 - t[..., None]) + hexc(c2)[None, None] * t[..., None]
    if c3:
        d = np.exp(-(((xs - w * 0.7) / (w * 0.35)) ** 2 + ((ys - h * 0.35) / (h * 0.5)) ** 2))
        a = a * (1 - 0.6 * d[..., None]) + hexc(c3)[None, None] * 0.6 * d[..., None]
    noise = np.random.default_rng(3).normal(0, 3, (h, w, 1))
    return Image.fromarray(np.clip(a + noise, 0, 255).astype(np.uint8)).convert("RGBA")


def cover(im, w, h, focus=(0.5, 0.5)):
    iw, ih = im.size
    sc = max(w / iw, h / ih)
    im = im.resize((int(iw * sc + 0.5), int(ih * sc + 0.5)), Image.LANCZOS)
    iw, ih = im.size
    l = int(min(max(focus[0] * iw - w / 2, 0), iw - w))
    t = int(min(max(focus[1] * ih - h / 2, 0), ih - h))
    return im.crop((l, t, l + w, t + h))


def mascot_tile(key, colors, name, w=1064, h=640, scale=1.5, top=0.06, x=0.5):
    bg = gradient(w, h, *colors)
    m = Image.open(os.path.join(IMG, key + ".png"))
    mh = int(h * scale)
    m = m.resize((int(m.width * mh / m.height), mh), Image.LANCZOS)
    bg.alpha_composite(m, (int(w * x - m.width / 2), int(h * top)))
    bg.convert("RGB").save(os.path.join(OUT, name + ".jpg"), quality=92)


def shade_bottom(im, color="#1C1650", start=0.45, strength=0.85, power=1.3):
    w, h = im.size
    a = np.asarray(im.convert("RGB")).astype(float)
    ys = np.linspace(0, 1, h)[:, None, None]
    k = np.clip((ys - start) / (1 - start), 0, 1) ** power * strength
    a = a * (1 - k) + hexc(color)[None, None] * k
    return Image.fromarray(a.astype(np.uint8))


mascot_tile("mascot_think", ("#CBBBFF", "#F3EEFF", "#FFFFFF"), "tile_games")
mascot_tile("mascot_tablet", ("#AEEBD4", "#E9FBF4", "#FFFFFF"), "tile_online")
mascot_tile("mascot_joy", ("#FFD27A", "#FFF4D6", "#FFFFFF"), "tile_reflect", scale=1.45)
mascot_tile("mascot_shrug", ("#BFE3FF", "#F0F8FF", "#FFFFFF"), "tile_tf", scale=1.5)

goal = cover(Image.open(os.path.join(IMG, "sport.jpg")), 900, 950, focus=(0.62, 0.5))
shade_bottom(goal, start=0.3, strength=0.93, power=0.6).save(os.path.join(OUT, "goal_card.jpg"), quality=92)

TICKETS = [("tent", (0.55, 0.55)), ("skeleton", (0.5, 0.3)), ("mannequin", (0.5, 0.45)), ("arm", (0.5, 0.45)),
           ("posture_good", (0.6, 0.45)), ("records", (0.55, 0.45))]
for i, (key, focus) in enumerate(TICKETS):
    t = cover(Image.open(os.path.join(IMG, key + ".jpg")), 1072, 600, focus=focus)
    shade_bottom(t, start=0.35, strength=0.88).save(os.path.join(OUT, "ticket%d.jpg" % (i + 1)), quality=92)
print("ok")
