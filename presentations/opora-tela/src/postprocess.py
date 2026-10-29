"""Final touches on the saved .pptx: Arial as the theme font, a true 16:9 slide size, a preview
thumbnail of the title slide and lighter media (pictures scaled to the size they are shown at,
video re-encoded), so the file stays small enough for phones and mail. No fonts are embedded —
every non-Arial text is a picture."""
import io
import os
import re
import subprocess
import sys
import tempfile
import zipfile

from PIL import Image

EMU = 914400
DPI = 170              # ~1.2× a 1920×1080 projector, leaves room for the slow "grow" zoom
SLIDE_IN = (13.333, 7.5)


def _rels(zin, part):
    d, f = part.rsplit("/", 1)
    try:
        x = zin.read(f"{d}/_rels/{f}.rels").decode("utf-8")
    except KeyError:
        return {}
    out = {}
    for rid, target in re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', x):
        out[rid] = os.path.normpath(os.path.join(d, target)).replace("\\", "/")
    return out


def needed_sizes(zin):
    """media part → largest (w, h) in inches it is shown at, counting crops."""
    need = {}

    def add(media, w_in, h_in):
        ow, oh = need.get(media, (0, 0))
        need[media] = (max(ow, w_in), max(oh, h_in))

    for part in zin.namelist():
        if not re.match(r"ppt/(slides|slideLayouts|slideMasters)/[^/]+\.xml$", part):
            continue
        x = zin.read(part).decode("utf-8")
        rels = _rels(zin, part)
        for pic in re.findall(r"<p:pic>.*?</p:pic>", x, re.S):
            m = re.search(r'<a:blip r:embed="(rId\d+)"', pic)
            e = re.search(r'<a:ext cx="(\d+)" cy="(\d+)"', pic)
            if not m or not e or m.group(1) not in rels:
                continue
            w, h = int(e.group(1)) / EMU, int(e.group(2)) / EMU
            crop = dict(re.findall(r'\b([ltrb])="(-?\d+)"', (re.search(r"<a:srcRect[^>]*/>", pic) or [""])[0]))
            fx = 1 - (int(crop.get("l", 0)) + int(crop.get("r", 0))) / 100000
            fy = 1 - (int(crop.get("t", 0)) + int(crop.get("b", 0))) / 100000
            add(rels[m.group(1)], w / max(fx, 0.05), h / max(fy, 0.05))
        for bg in re.findall(r"<p:bg>.*?</p:bg>", x, re.S):
            m = re.search(r'r:embed="(rId\d+)"', bg)
            if m and m.group(1) in rels:
                add(rels[m.group(1)], *SLIDE_IN)
    return need


def slim_image(data, ext, size_in):
    img = Image.open(io.BytesIO(data))
    img.load()
    w_in, h_in = size_in
    scale = min(1.0, max(w_in * DPI / img.width, h_in * DPI / img.height))
    if scale < 0.9:
        img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)
    buf = io.BytesIO()
    if ext in ("jpg", "jpeg"):
        img.convert("RGB").save(buf, "JPEG", quality=84, optimize=True)
    else:
        img.save(buf, "PNG", optimize=True)
    return buf.getvalue() if buf.tell() < len(data) else data


def slim_video(data):
    """H.264 Main + AAC at 720p: plays in PowerPoint on Windows, Mac and phones."""
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = os.path.join(tmp, "in.mp4"), os.path.join(tmp, "out.mp4")
        open(src, "wb").write(data)
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", "scale=-2:720", "-c:v", "libx264",
               "-profile:v", "main", "-level", "3.1", "-pix_fmt", "yuv420p", "-crf", "25", "-preset", "slow",
               "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", dst]
        if subprocess.run(cmd).returncode != 0:
            return data
        out = open(dst, "rb").read()
    return out if len(out) < len(data) else data


def run(path, thumb=None):
    tmp = path + ".tmp"
    zin = zipfile.ZipFile(path)
    need = needed_sizes(zin)
    zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        name = item.filename
        ext = name.rsplit(".", 1)[-1].lower()
        if re.match(r"ppt/theme/theme\d+\.xml", name):
            s = data.decode("utf-8")
            s = re.sub(r'(<a:majorFont><a:latin typeface=")[^"]*(")', r"\1Arial\2", s)
            s = re.sub(r'(<a:minorFont><a:latin typeface=")[^"]*(")', r"\1Arial\2", s)
            data = s.encode("utf-8")
        elif name == "ppt/presentation.xml":
            data = data.decode("utf-8").replace(' type="screen4x3"', "").encode("utf-8")
        elif name == "docProps/thumbnail.jpeg" and thumb:
            data = open(thumb, "rb").read()
        elif name.startswith("ppt/media/") and ext in ("jpg", "jpeg", "png") and name in need:
            data = slim_image(data, ext, need[name])
        elif name.startswith("ppt/media/") and ext == "mp4":
            data = slim_video(data)
        # media is already compressed, deflating it again only costs time
        kind = zipfile.ZIP_STORED if ext in ("jpg", "jpeg", "png", "mp4") else zipfile.ZIP_DEFLATED
        zout.writestr(zipfile.ZipInfo(name, item.date_time), data, compress_type=kind)
    zin.close()
    zout.close()
    os.replace(tmp, path)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print("postprocessed")
