"""Generate backgrounds, emoji icons, sounds and QR codes for the deck."""
import math, random, os, wave, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080
FONT_BLACK = os.path.expanduser("~/.fonts/NunitoBlack-Regular.ttf")


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient(c1, c2, angle=90):
    """Linear gradient; angle 90 = top->bottom, 0 = left->right."""
    a = np.radians(angle)
    xs, ys = np.meshgrid(np.linspace(0, 1, W), np.linspace(0, 1, H))
    t = xs * math.cos(a) + ys * math.sin(a)
    t = (t - t.min()) / (t.max() - t.min())
    c1, c2 = np.array(hex2rgb(c1), float), np.array(hex2rgb(c2), float)
    arr = c1[None, None, :] * (1 - t[..., None]) + c2[None, None, :] * t[..., None]
    return Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")


def blob_layer(blobs, blur=160):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for (cx, cy, r, col, alpha) in blobs:
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha)
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
        solid = Image.new("RGBA", (W, H), hex2rgb(col) + (255,))
        solid.putalpha(mask)
        layer.alpha_composite(solid)
    return layer


def bone(draw, cx, cy, length, thick, angle, fill):
    """Draw a cartoon bone (two knobs at each end + shaft)."""
    img = Image.new("RGBA", (int(length * 1.6), int(length * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ox, oy = img.width / 2, img.height / 2
    half = length / 2
    r = thick * 0.9
    d.rounded_rectangle([ox - half, oy - thick / 2, ox + half, oy + thick / 2], radius=thick / 2, fill=fill)
    for sx in (-1, 1):
        for sy in (-1, 1):
            d.ellipse([ox + sx * half - r, oy + sy * thick * 0.55 - r, ox + sx * half + r, oy + sy * thick * 0.55 + r], fill=fill)
    return img.rotate(angle, resample=Image.BICUBIC, expand=False)


def sprinkle(base, items, seed, avoid=None):
    rnd = random.Random(seed)
    for kind, count, cols, alpha, size in items:
        placed = 0
        tries = 0
        while placed < count and tries < 2000:
            tries += 1
            x, y = rnd.uniform(40, W - 40), rnd.uniform(40, H - 40)
            if avoid and avoid[0] < x < avoid[2] and avoid[1] < y < avoid[3]:
                continue
            col = hex2rgb(rnd.choice(cols)) + (alpha,)
            s = rnd.uniform(*size)
            if kind == "bone":
                b = bone(None, 0, 0, s, s * 0.28, rnd.uniform(0, 180), col)
                base.alpha_composite(b, (int(x - b.width / 2), int(y - b.height / 2)))
            elif kind == "dot":
                d = ImageDraw.Draw(base)
                d.ellipse([x - s, y - s, x + s, y + s], fill=col)
            elif kind == "ring":
                d = ImageDraw.Draw(base)
                d.ellipse([x - s, y - s, x + s, y + s], outline=col, width=max(3, int(s / 4)))
            elif kind == "star":
                star = Image.new("RGBA", (int(s * 4), int(s * 4)), (0, 0, 0, 0))
                sd = ImageDraw.Draw(star)
                c = s * 2
                pts = []
                for i in range(8):
                    rr = s * 1.6 if i % 2 == 0 else s * 0.35
                    a = math.pi / 4 * i
                    pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
                sd.polygon(pts, fill=col)
                base.alpha_composite(star, (int(x - c), int(y - c)))
            elif kind == "q":
                f = ImageFont.truetype(FONT_BLACK, int(s))
                t = Image.new("RGBA", (int(s * 1.4), int(s * 1.6)), (0, 0, 0, 0))
                ImageDraw.Draw(t).text((s * 0.2, 0), "?", font=f, fill=col)
                t = t.rotate(rnd.uniform(-25, 25), resample=Image.BICUBIC, expand=True)
                base.alpha_composite(t, (int(x - t.width / 2), int(y - t.height / 2)))
            placed += 1
    return base


def save(img, name):
    img.convert("RGB").save(os.path.join(OUT, name), quality=92)


# --- light content background
bg = gradient("#EAF5FF", "#F5F0FF", 90)
bg.alpha_composite(blob_layer([(1750, 80, 380, "#BDEFE0", 210), (120, 1000, 420, "#FFE7A3", 190),
                               (1850, 950, 330, "#DCD2FF", 200), (200, 60, 260, "#CDE9FF", 160)]))
bg = sprinkle(bg, [("bone", 16, ["#FFFFFF"], 150, (40, 70)), ("dot", 26, ["#FFFFFF", "#CFE3FF", "#FFE7A3"], 170, (4, 9)),
                   ("ring", 8, ["#FFFFFF"], 140, (10, 18))], 1)
save(bg, "bg_light.jpg")

# --- dark hero background
bg = gradient("#241E63", "#4B36A8", 35)
bg.alpha_composite(blob_layer([(1650, 220, 420, "#FF6FB1", 120), (250, 900, 460, "#36C5FF", 120),
                               (1000, 1150, 380, "#9B7BFF", 140)], 190))
bg = sprinkle(bg, [("star", 16, ["#FFFFFF", "#FFE08A"], 210, (5, 11)), ("dot", 60, ["#FFFFFF"], 140, (1.5, 3.5)),
                   ("bone", 10, ["#FFFFFF"], 34, (60, 100))], 2)
save(bg, "bg_dark.jpg")

# --- sunny celebration background
bg = gradient("#FFE37A", "#FFB04F", 60)
bg.alpha_composite(blob_layer([(1700, 150, 420, "#FFF6C9", 200), (180, 950, 420, "#FF8E6E", 120)], 170))
bg = sprinkle(bg, [("star", 14, ["#FFFFFF"], 200, (6, 12)), ("dot", 30, ["#FFFFFF", "#FF6B6B", "#6C5CE7", "#2EC4A6"], 170, (5, 10)),
                   ("bone", 8, ["#FFFFFF"], 90, (50, 80))], 3)
save(bg, "bg_sun.jpg")

# --- mint activity background
bg = gradient("#DDF8EE", "#E3F1FF", 20)
bg.alpha_composite(blob_layer([(1800, 120, 380, "#B6F0DA", 200), (100, 980, 400, "#C9E6FF", 200),
                               (1700, 1000, 300, "#FFE3A0", 170)]))
bg = sprinkle(bg, [("bone", 14, ["#FFFFFF"], 160, (40, 70)), ("dot", 24, ["#FFFFFF", "#9FE7CF"], 170, (4, 9))], 4)
save(bg, "bg_mint.jpg")

# --- quiz background
bg = gradient("#EFE9FF", "#E2F1FF", 70)
bg.alpha_composite(blob_layer([(1750, 100, 380, "#D8CCFF", 210), (150, 1000, 400, "#C7E8FF", 200),
                               (1800, 980, 300, "#FFD6E0", 170)]))
bg = sprinkle(bg, [("q", 14, ["#FFFFFF"], 150, (70, 130)), ("dot", 22, ["#FFFFFF", "#D8CCFF"], 170, (4, 9))], 5)
save(bg, "bg_quiz.jpg")

# --- coral (muscles / warm) background
bg = gradient("#FFF0EA", "#FFF6E0", 60)
bg.alpha_composite(blob_layer([(1750, 120, 380, "#FFD0C2", 200), (120, 1000, 420, "#FFE6A6", 190),
                               (1850, 980, 300, "#FFD9E6", 170)]))
bg = sprinkle(bg, [("bone", 14, ["#FFFFFF"], 170, (40, 70)), ("dot", 24, ["#FFFFFF", "#FFC2B0"], 170, (4, 9))], 6)
save(bg, "bg_warm.jpg")
print("backgrounds ok")

# --- emoji icons via Noto Color Emoji
EMOJI = {
    "bone": "\U0001F9B4", "muscle": "\U0001F4AA", "brain": "\U0001F9E0", "heart": "\U0001FAC0", "lungs": "\U0001FAC1",
    "leg": "\U0001F9B5", "foot": "\U0001F9B6", "hand": "✋", "run": "\U0001F3C3", "film": "\U0001F3AC",
    "museum": "\U0001F3DB️", "game": "\U0001F3AE", "globe": "\U0001F310", "trophy": "\U0001F3C6", "rainbow": "\U0001F308",
    "star": "⭐", "puzzle": "\U0001F9E9", "cartwheel": "\U0001F938", "search": "\U0001F50D", "milk": "\U0001F95B",
    "cheese": "\U0001F9C0", "fish": "\U0001F41F", "sleep": "\U0001F634", "ball": "⚽", "backpack": "\U0001F392",
    "chair": "\U0001FA91", "books": "\U0001F4DA", "home": "\U0001F3E0", "target": "\U0001F3AF", "bulb": "\U0001F4A1",
    "question": "❓", "check": "✅", "cross": "❌", "grin": "\U0001F601", "smile": "\U0001F642",
    "think": "\U0001F914", "confused": "\U0001F615", "party": "\U0001F389", "phone": "\U0001F4F1", "eyes": "\U0001F440",
    "stand": "\U0001F9CD", "raise": "\U0001F64B", "sparkles": "✨", "rocket": "\U0001F680", "ladder": "\U0001FA9C",
    "popcorn": "\U0001F37F", "clap": "\U0001F44F", "medal": "\U0001F947", "map": "\U0001F5FA️", "ticket": "\U0001F39F️",
    "bike": "\U0001F6B2", "swim": "\U0001F3CA", "apple": "\U0001F34E", "carrot": "\U0001F955", "pencil": "✏️",
    "magnet": "\U0001F9F2", "gear": "⚙️", "shield": "\U0001F6E1️", "house": "\U0001F3E1", "tent": "⛺",
    "jelly": "\U0001FABC", "robot": "\U0001F916", "skull": "\U0001F480", "ear": "\U0001F442", "ruler": "\U0001F4CF",
    "baby": "\U0001F476", "adult": "\U0001F9D1", "wave": "\U0001F44B", "thumbs": "\U0001F44D", "play": "▶️",
    "next": "➡️", "back": "⬅️", "flag": "\U0001F3C1", "glasses": "\U0001F453", "clock": "⏰",
    "calendar": "\U0001F4C5", "speech": "\U0001F4AC", "lock": "\U0001F512", "key": "\U0001F511", "sun": "☀️", "zap": "\u26A1",
}
emo_dir = os.path.join(OUT, "emoji")
os.makedirs(emo_dir, exist_ok=True)
font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109) if os.path.exists("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf") else None
if font is None:
    import subprocess
    path = subprocess.check_output(["fc-match", "-f", "%{file}", "Noto Color Emoji"]).decode()
    font = ImageFont.truetype(path, 109)
missing = []
for key, ch in EMOJI.items():
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=font, embedded_color=True, anchor="mm")
    bbox = im.getbbox()
    if not bbox:
        missing.append(key)
        continue
    im = im.crop(bbox)
    side = max(im.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    sq.resize((256, 256), Image.LANCZOS).save(os.path.join(emo_dir, key + ".png"))
print("emoji ok, missing:", missing)

# --- sounds
SR = 44100


def write_wav(name, sig):
    sig = np.clip(sig / (np.abs(sig).max() + 1e-9) * 0.85, -1, 1)
    with wave.open(os.path.join(OUT, name), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((sig * 32767).astype("<i2").tobytes())


def bell(freq, dur, decay=6.0):
    t = np.linspace(0, dur, int(SR * dur), False)
    env = np.exp(-decay * t) * np.minimum(1, t / 0.004)
    s = (np.sin(2 * np.pi * freq * t) + 0.45 * np.sin(2 * np.pi * freq * 2.01 * t) * np.exp(-3 * t)
         + 0.25 * np.sin(2 * np.pi * freq * 3.02 * t) * np.exp(-6 * t))
    return s * env


def place(total, parts):
    out = np.zeros(int(SR * total))
    for start, sig in parts:
        i = int(SR * start)
        n = min(len(sig), len(out) - i)
        out[i:i + n] += sig[:n]
    return out


write_wav("correct.wav", place(1.0, [(0.0, bell(1046.5, 0.9)), (0.11, bell(1318.5, 0.85)), (0.22, bell(1568.0, 0.8))]))
t = np.linspace(0, 0.5, int(SR * 0.5), False)
f = 320 * np.exp(-2.2 * t)
phase = 2 * np.pi * np.cumsum(f) / SR
wrong = (np.tanh(3 * np.sin(phase)) * 0.8 + 0.3 * np.sin(2 * phase)) * np.exp(-4.5 * t) * np.minimum(1, t / 0.005)
write_wav("wrong.wav", wrong)
notes = [523.25, 659.25, 783.99, 1046.5]
win = place(1.6, [(i * 0.12, bell(n, 1.2, 3.5)) for i, n in enumerate(notes)] + [(0.5, bell(n, 1.1, 2.8)) for n in notes])
write_wav("win.wav", win)
t = np.linspace(0, 0.3, int(SR * 0.3), False)
noise = np.random.default_rng(1).normal(size=t.size)
sweep = np.convolve(noise, np.ones(30) / 30, "same") * np.sin(np.pi * t / 0.3) ** 2
write_wav("flip.wav", sweep)
write_wav("pop.wav", place(0.35, [(0, bell(880, 0.3, 14)), (0.05, bell(1760, 0.25, 18))]))
print("sounds ok")
