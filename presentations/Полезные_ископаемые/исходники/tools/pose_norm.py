"""Put every exercise pose on one canvas size at one scale, feet on the same line, so swapping poses doesn't jump."""
import os
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CUT = os.path.join(ROOT, "img", "cut"); OUT = os.path.join(ROOT, "img", "pose")
os.makedirs(OUT, exist_ok=True)
codes = ["P0", "P1", "P2", "P3", "P4", "P5", "C1", "C4"]
figs = {}
for c in codes:
    im = Image.open(os.path.join(CUT, c + ".png")).convert("RGBA")
    figs[c] = im.crop(im.getbbox())
# P0 comes from the teacher's own picture at another scale: match its height to P3 (same standing pose)
ref_h = figs["P3"].height
f = ref_h / figs["P0"].height
figs["P0"] = figs["P0"].resize((round(figs["P0"].width * f), ref_h), Image.LANCZOS)
CW, CH = 1000, 1150
maxh = max(im.height for im in figs.values()); maxw = max(im.width for im in figs.values())
s = min((CH - 40) / maxh, (CW - 20) / maxw, 1.0)
for c, im in figs.items():
    if s < 1:
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    canvas.paste(im, ((CW - im.width) // 2, CH - 20 - im.height), im)
    canvas.save(os.path.join(OUT, c + ".png"), optimize=True)
    print(c, im.size)
