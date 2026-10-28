"""Download Higgsfield results (needs d8j0ntlcm91z4.cloudfront.net allowed) or pick up
user-uploaded files whose names contain the job id. Mascots are chroma-keyed."""
import json, os, sys, glob, subprocess
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://d8j0ntlcm91z4.cloudfront.net/user_3L421efSnnZAMIV07WA2CiZG31R/"
man = json.load(open(os.path.join(HERE, "manifest.json")))
upload_dirs = sys.argv[1:]


def find_upload(fname):
    jid = fname.split("_")[-1].split(".")[0]
    short = jid.split("-")[0]
    for d in upload_dirs:
        for p in glob.glob(os.path.join(d, "**", "*"), recursive=True):
            b = os.path.basename(p)
            if jid in b or short in b:
                return p
    return None


def key_green(src, dst):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = g - np.maximum(r, b)
    alpha = np.clip(1 - (green - 25) / 60, 0, 1)
    # despill: pull green down to the max of red/blue where it dominates
    spill = np.clip(green, 0, None) * (alpha > 0)
    g2 = np.where(green > 0, np.maximum(r, b) + np.clip(green, 0, 12), g)
    out = np.dstack([r, g2, b, alpha * 255]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")
    al = img.getchannel("A").filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    img.putalpha(al)
    bbox = img.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
    img = img.crop(bbox)
    img.save(dst)


for key, fname in man.items():
    raw = os.path.join(HERE, "raw", fname)
    if not os.path.exists(raw):
        up = find_upload(fname)
        if up:
            Image.open(up).convert("RGB").save(raw)
        else:
            r = subprocess.run(["curl", "-sSf", "--max-time", "60", "-o", raw, BASE + fname])
            if r.returncode != 0:
                if os.path.exists(raw):
                    os.remove(raw)
                print("MISSING", key)
                continue
    out = os.path.join(HERE, key + ".png")
    if key.startswith("mascot"):
        key_green(raw, out)
    else:
        Image.open(raw).convert("RGB").save(os.path.join(HERE, key + ".jpg"), quality=92)
    print("ok", key)
