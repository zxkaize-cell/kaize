"""Phone version: every slide becomes one picture (final state of the correct path), so any viewer shows it right.
usage: phone_version.py deck.pptx out.pptx workdir"""
import os, re, shutil, subprocess, sys, zipfile, glob
from lxml import etree
from pptx import Presentation
from pptx.util import Emu

src, out, work = sys.argv[1:4]
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
clean = os.path.join(work, "clean.pptx")
zin = zipfile.ZipFile(src)
zout = zipfile.ZipFile(clean, "w", zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if re.match(r"ppt/slides/slide\d+\.xml$", item.filename):
        root = etree.fromstring(data)
        for el in list(root.iter(f"{{{P}}}sp", f"{{{P}}}pic")):
            nv = el.find(f".//{{{P}}}cNvPr")
            name = nv.get("name") if nv is not None else ""
            xml = etree.tostring(el).decode()
            drop = (re.fullmatch(r"no\d", name) or name == "bad" or re.fullmatch(r"hl\d", name)
                    or (name.startswith("pose_") and name != "pose_C1")
                    or (name.startswith("ring") and "EF5B5B" in xml))
            if drop:
                el.getparent().remove(el)
        for t in root.findall(f"{{{P}}}timing"):
            root.remove(t)
        data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    zout.writestr(item, data)
zout.close()
soffice = "/root/.claude/skills/synced/24712791-6e12-43ba-b50d-51f8f1496d68_5a144236-568f-4220-a43c-5d521cd49348/pptx/scripts/office/soffice.py"
subprocess.run([sys.executable, soffice, "--headless", "--convert-to", "pdf", "--outdir", work, clean], check=True, capture_output=True, timeout=600)
subprocess.run(["pdftoppm", "-jpeg", "-jpegopt", "quality=90", "-r", "144", os.path.join(work, "clean.pdf"), os.path.join(work, "s")], check=True)
imgs = sorted(glob.glob(os.path.join(work, "s-*.jpg")))
orig = Presentation(src)
prs = Presentation()
prs.slide_width, prs.slide_height = orig.slide_width, orig.slide_height
blank = prs.slide_layouts[6]
for i, img in enumerate(imgs):
    sl = prs.slides.add_slide(blank)
    sl.shapes.add_picture(img, 0, 0, prs.slide_width, prs.slide_height)
    o = orig.slides[i]
    if o.has_notes_slide and o.notes_slide.notes_text_frame.text.strip():
        sl.notes_slide.notes_text_frame.text = o.notes_slide.notes_text_frame.text
prs.save(out)
print("slides", len(imgs), "->", out, os.path.getsize(out) // 1024, "KB")
