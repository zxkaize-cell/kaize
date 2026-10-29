"""Design helpers: text, cards, pictures, 3D/shadow effects, navigation."""
import copy
import os
from lxml import etree
from PIL import ImageFont
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
EMOJI = os.path.join(ASSETS, "emoji")
IMG = os.path.join(HERE, "img")

FONT = "Arial"           # live body text: present on every device
NUNITO = "Nunito"        # rounded body face, used only inside rendered pictures
DISPLAY = "Unbounded"    # titles and big numbers (rendered as pictures)
HAND = "Caveat"          # handwritten accents (rendered as pictures)
FONT_BLACK = DISPLAY
RASTER_FACES = (NUNITO, DISPLAY, HAND)
FONT_FILES = {
    (FONT, False): "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    (FONT, True): "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    (NUNITO, False): os.path.expanduser("~/.fonts/Nunito-Regular.ttf"),
    (NUNITO, True): os.path.expanduser("~/.fonts/Nunito-Bold.ttf"),
    (DISPLAY, False): os.path.expanduser("~/.fonts/Unbounded-Regular.ttf"),
    (DISPLAY, True): os.path.expanduser("~/.fonts/Unbounded-Regular.ttf"),
    (HAND, False): os.path.expanduser("~/.fonts/Caveat-Regular.ttf"),
    (HAND, True): os.path.expanduser("~/.fonts/Caveat-Regular.ttf"),
}

C = {
    "ink": "2B2A5A",       # main text, deep indigo
    "indigo": "3B2F8F",
    "night": "2A2370",
    "violet": "6C5CE7",
    "lilac": "B9A9FF",
    "lilac_soft": "EEEAFF",
    "sky": "3BA7F5",
    "sky_soft": "E3F2FF",
    "mint": "1FB89A",
    "mint_soft": "DDF7EE",
    "sun": "FFC23C",
    "sun_soft": "FFF3CF",
    "coral": "FF6B6B",
    "coral_soft": "FFE4E1",
    "orange": "FF9F43",
    "green": "22B573",
    "red": "F0505A",
    "white": "FFFFFF",
    "muted": "6B6A8E",
    "ivory": "FFF8EC",
}


def E(inches):
    return Emu(int(round(inches * 914400)))


def rgb(hexstr):
    return RGBColor.from_string(hexstr)


# ------------------------------------------------------------- text metrics
_font_cache = {}


def _pil_font(face, bold, size):
    key = (face, bold, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(FONT_FILES[(face, bold)], int(size * 10))
    return _font_cache[key]


def text_width_in(text, size, face=FONT, bold=False):
    f = _pil_font(face, bold, size)
    return f.getlength(text) / 10 / 72


def wrap(text, size, width_in, face=FONT, bold=False):
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if text_width_in(trial, size, face, bold) <= width_in or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def fits(text, size, w, h, face=FONT, bold=False, spacing=1.2):
    lines = wrap(text, size, w, face, bold)
    longest = max(text_width_in(l, size, face, bold) for l in lines)
    height = len(lines) * size * spacing / 72
    return longest <= w + 1e-6 and height <= h + 1e-6, len(lines)


WARNINGS = []


def check_fit(label, text, size, w, h, face=FONT, bold=False, spacing=1.2):
    ok, n = fits(text, size, w, h, face, bold, spacing)
    if not ok:
        WARNINGS.append("%s: '%s' (%spt, %d lines) does not fit %.2fx%.2f" % (label, text[:40], size, n, w, h))
    return ok


# ------------------------------------------------------------------ XML bits
A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _el(xml):
    return etree.fromstring('<root xmlns:a="%s">%s</root>' % (A, xml))[0]


def _sppr(shape):
    return shape._element.spPr


def _insert_after_fill(spPr, el):
    """Insert an effect element at its schema position inside spPr."""
    order = ["xfrm", "custGeom", "prstGeom", "noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill",
             "ln", "effectLst", "effectDag", "scene3d", "sp3d", "extLst"]
    tag = etree.QName(el).localname
    idx = order.index(tag)
    for child in list(spPr):
        if etree.QName(child).localname == tag:
            spPr.remove(child)
    pos = 0
    for i, child in enumerate(spPr):
        name = etree.QName(child).localname
        if name in order and order.index(name) < idx:
            pos = i + 1
    spPr.insert(pos, el)


def shadow(shape, blur=0.18, dist=0.06, color="2B2A5A", alpha=22, angle=90):
    el = _el('<a:effectLst><a:outerShdw blurRad="%d" dist="%d" dir="%d" algn="t" rotWithShape="0">'
             '<a:srgbClr val="%s"><a:alpha val="%d"/></a:srgbClr></a:outerShdw></a:effectLst>'
             % (E(blur), E(dist), angle * 60000, color, alpha * 1000))
    _insert_after_fill(_sppr(shape), el)


def glow(shape, color="FFFFFF", rad=0.15, alpha=60):
    el = _el('<a:effectLst><a:glow rad="%d"><a:srgbClr val="%s"><a:alpha val="%d"/></a:srgbClr></a:glow></a:effectLst>'
             % (E(rad), color, alpha * 1000))
    _insert_after_fill(_sppr(shape), el)


def bevel(shape, w=0.09, h=0.035, prst="circle", light="threePt"):
    """Soft 'puffy' 3D look in PowerPoint (flat elsewhere)."""
    _insert_after_fill(_sppr(shape), _el('<a:scene3d><a:camera prst="orthographicFront"/>'
                                         '<a:lightRig rig="%s" dir="t"/></a:scene3d>' % light))
    _insert_after_fill(_sppr(shape), _el('<a:sp3d><a:bevelT w="%d" h="%d" prst="%s"/></a:sp3d>' % (E(w), E(h), prst)))


def tilt3d(shape, camera="perspectiveRelaxedModerately", w=0.06, h=0.03, extrusion=0.0, ext_color=None):
    _insert_after_fill(_sppr(shape), _el('<a:scene3d><a:camera prst="%s"/><a:lightRig rig="threePt" dir="t"/></a:scene3d>' % camera))
    ext = ""
    if extrusion:
        ext = ' extrusionH="%d"' % E(extrusion)
    clr = '<a:extrusionClr><a:srgbClr val="%s"/></a:extrusionClr>' % ext_color if ext_color else ""
    _insert_after_fill(_sppr(shape), _el('<a:sp3d%s><a:bevelT w="%d" h="%d"/>%s</a:sp3d>' % (ext, E(w), E(h), clr)))


def transparent_fill(shape):
    """Fully transparent fill: invisible but still clickable in slide show."""
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb("FFFFFF")
    clr = shape._element.spPr.find(qn("a:solidFill"))[0]
    for a in clr.findall(qn("a:alpha")):
        clr.remove(a)
    alpha = etree.SubElement(clr, qn("a:alpha"))
    alpha.set("val", "0")
    shape.line.fill.background()


def fill_alpha(shape, hexcolor, alpha_pct):
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(hexcolor)
    clr = shape._element.spPr.find(qn("a:solidFill"))[0]
    a = etree.SubElement(clr, qn("a:alpha"))
    a.set("val", str(int(alpha_pct * 1000)))


def set_name(shape, name):
    shape._element.xpath("./*[1]/p:cNvPr")[0].set("name", name)


def set_descr(shape, text):
    shape._element.xpath("./*[1]/p:cNvPr")[0].set("descr", text)


# ------------------------------------------------------------------ text
def _style_run(run, size, color, face, bold, italic=False):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = rgb(color)
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:latin", "a:ea", "a:cs"):
        for old in rPr.findall(qn(tag)):
            rPr.remove(old)
    for tag in ("a:latin", "a:cs"):
        el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", face)
    rPr.set("lang", "ru-RU")


def text(slide, x, y, w, h, content, size=18, color=None, face=FONT, bold=False, align="l", anchor="t",
         name=None, spacing=None, italic=False, para_space=0, check=True, extrude=None, glow_shadow=None):
    """content: str (\\n = new paragraph) or list of paragraphs, each a list of (text, opts) runs.
    Display and handwritten faces come out as pictures so no font has to travel with the file."""
    color = color or C["ink"]
    if face in RASTER_FACES or extrude:
        return text_img(slide, x, y, w, h, content, size, color, face, bold, align, anchor, name, spacing,
                        extrude=extrude, shadow=glow_shadow, check=check)
    tb = slide.shapes.add_textbox(E(x), E(y), E(w), E(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
    bodyPr = tf._txBody.bodyPr
    for old in list(bodyPr):
        bodyPr.remove(old)
    etree.SubElement(bodyPr, qn("a:noAutofit"))
    paras = content if isinstance(content, list) else [[(p, {})] for p in content.split("\n")]
    for i, runs in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
        if spacing:
            p.line_spacing = spacing
        if para_space and i:
            p.space_before = Pt(para_space)
        for t, o in runs:
            r = p.add_run()
            r.text = t
            _style_run(r, o.get("size", size), o.get("color", color), o.get("face", face), o.get("bold", bold),
                       o.get("italic", italic))
    if name:
        set_name(tb, name)
    if check and isinstance(content, str):
        check_fit(name or content[:20], content, size, w, h, face, bold, spacing or 1.2)
    return tb


def shape_text(shp, content, size=18, color=None, face=FONT, bold=False, align="c", anchor="m",
               margins=(0.12, 0.08), spacing=None, check=True, label=None):
    color = color or C["ink"]
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = E(margins[0])
    tf.margin_top = tf.margin_bottom = E(margins[1])
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
    bodyPr = tf._txBody.bodyPr
    for old in list(bodyPr):
        bodyPr.remove(old)
    etree.SubElement(bodyPr, qn("a:noAutofit"))
    paras = content if isinstance(content, list) else [[(p, {})] for p in content.split("\n")]
    for i, runs in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
        if spacing:
            p.line_spacing = spacing
        for t, o in runs:
            r = p.add_run()
            r.text = t
            _style_run(r, o.get("size", size), o.get("color", color), o.get("face", face), o.get("bold", bold),
                       o.get("italic", False))
    if check and isinstance(content, str):
        w = shp.width / 914400 - 2 * margins[0]
        h = shp.height / 914400 - 2 * margins[1]
        check_fit(label or content[:20], content, size, w, h, face, bold, spacing or 1.2)


def text_3d(tb, extrusion_color="1E1856", depth=0.06, camera="obliqueBottomRight", outline=None, outline_w=0.0):
    """WordArt-style 3D extrusion on every run of a text box (PowerPoint only)."""
    bodyPr = tb.text_frame._txBody.bodyPr
    bodyPr.append(_el('<a:scene3d><a:camera prst="%s"/><a:lightRig rig="balanced" dir="t"/></a:scene3d>' % camera))
    bodyPr.append(_el('<a:sp3d extrusionH="%d" prstMaterial="softEdge"><a:bevelT w="%d" h="%d"/>'
                      '<a:extrusionClr><a:srgbClr val="%s"/></a:extrusionClr></a:sp3d>'
                      % (E(depth), E(0.02), E(0.012), extrusion_color)))
    if outline:
        for r in tb._element.iter(qn("a:rPr")):
            ln = _el('<a:ln w="%d"><a:solidFill><a:srgbClr val="%s"/></a:solidFill></a:ln>' % (E(outline_w), outline))
            r.insert(0, ln)


def text_shadow(tb, color="1E1856", alpha=35, blur=0.04, dist=0.035):
    for rPr in tb._element.iter(qn("a:rPr")):
        el = _el('<a:effectLst><a:outerShdw blurRad="%d" dist="%d" dir="5400000" algn="t" rotWithShape="0">'
                 '<a:srgbClr val="%s"><a:alpha val="%d"/></a:srgbClr></a:outerShdw></a:effectLst>'
                 % (E(blur), E(dist), color, alpha * 1000))
        fill = rPr.find(qn("a:solidFill"))
        if fill is not None:
            fill.addnext(el)
        else:
            rPr.insert(0, el)


# ------------------------------------------------------------------ shapes
def box(slide, x, y, w, h, fill="FFFFFF", radius=0.22, line=None, line_w=0.0, name=None, kind="round",
        shadow_on=False):
    shape_type = {"round": MSO_SHAPE.ROUNDED_RECTANGLE, "rect": MSO_SHAPE.RECTANGLE, "oval": MSO_SHAPE.OVAL,
                  "pill": MSO_SHAPE.ROUNDED_RECTANGLE}[kind]
    s = slide.shapes.add_shape(shape_type, E(x), E(y), E(w), E(h))
    if kind in ("round", "pill"):
        r = (min(w, h) / 2) if kind == "pill" else radius
        s.adjustments[0] = min(0.5, r / min(w, h))
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = E(line_w)
    else:
        s.line.fill.background()
    if name:
        set_name(s, name)
    if shadow_on:
        shadow(s)
    # no stray text style from theme
    return s


def picture(slide, path, x, y, w=None, h=None, name=None, rounded=None, border=None, border_w=0.06,
            shadow_on=False, descr=None, crop_to=None):
    """Insert a picture. crop_to=(w,h): center-crop to that aspect and size."""
    from PIL import Image
    if crop_to:
        cw, ch = crop_to
        im = Image.open(path)
        iw, ih = im.size
        target = cw / ch
        pic = slide.shapes.add_picture(path, E(x), E(y), E(cw), E(ch))
        if iw / ih > target:  # too wide
            excess = 1 - target / (iw / ih)
            pic.crop_left = excess / 2
            pic.crop_right = excess / 2
        else:
            excess = 1 - (iw / ih) / target
            pic.crop_top = excess / 2
            pic.crop_bottom = excess / 2
    else:
        pic = slide.shapes.add_picture(path, E(x), E(y), E(w) if w else None, E(h) if h else None)
    if rounded:
        geom = pic._element.spPr.find(qn("a:prstGeom"))
        geom.set("prst", "roundRect")
        av = geom.find(qn("a:avLst"))
        if av is None:
            av = etree.SubElement(geom, qn("a:avLst"))
        for g in list(av):
            av.remove(g)
        gd = etree.SubElement(av, qn("a:gd"))
        mn = min(pic.width, pic.height) / 914400
        gd.set("name", "adj")
        gd.set("fmla", "val %d" % int(min(50000, rounded / mn * 100000)))
    if border:
        pic.line.color.rgb = rgb(border)
        pic.line.width = E(border_w)
    if shadow_on:
        shadow(pic, blur=0.25, dist=0.08, alpha=25)
    if name:
        set_name(pic, name)
    if descr:
        set_descr(pic, descr)
    return pic


def emoji(slide, key, x, y, size, name=None):
    pic = slide.shapes.add_picture(os.path.join(EMOJI, key + ".png"), E(x), E(y), E(size), E(size))
    set_name(pic, name or ("icon " + key))
    set_descr(pic, "")
    return pic


def link_slide(shape, target_slide):
    shape.click_action.target_slide = target_slide


def link_url(shape, url):
    shape.click_action.hyperlink.address = url


def notes(slide, txt):
    slide.notes_slide.notes_text_frame.text = txt


def badge(slide, path, x, y, d, center=(0.5, 0.5), side=0.5, name=None, ring="FFFFFF", ring_w=0.05, shadow_on=True,
          descr=""):
    """Round photo crop: center/side are fractions of the image (side of min(w, h))."""
    from PIL import Image
    iw, ih = Image.open(path).size
    s = side * min(iw, ih)
    cx, cy = center[0] * iw, center[1] * ih
    l, t = max(0, min(iw - s, cx - s / 2)), max(0, min(ih - s, cy - s / 2))
    pic = slide.shapes.add_picture(path, E(x), E(y), E(d), E(d))
    pic.crop_left, pic.crop_right = l / iw, (iw - l - s) / iw
    pic.crop_top, pic.crop_bottom = t / ih, (ih - t - s) / ih
    pic._element.spPr.find(qn("a:prstGeom")).set("prst", "ellipse")
    if ring:
        pic.line.color.rgb = rgb(ring)
        pic.line.width = E(ring_w)
    if shadow_on:
        shadow(pic, blur=0.2, dist=0.06, alpha=22)
    set_name(pic, name or "badge")
    set_descr(pic, descr)
    return pic


def glass(slide, x, y, w, h, alpha=88, radius=0.25, name="card", tint="FFFFFF", sh=True):
    """Frosted card: translucent white with a soft shadow."""
    b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, E(x), E(y), E(w), E(h))
    st = b._element.find(qn("p:style"))
    if st is not None:
        b._element.remove(st)
    b.adjustments[0] = min(0.5, radius / min(w, h))
    fill_alpha(b, tint, alpha)
    b.line.fill.background()
    if sh:
        shadow(b, blur=0.35, dist=0.08, alpha=13, color="3B2F8F")
    set_name(b, name)
    return b


# ------------------------------------------------------------ rendered text
import raster


def _paras(content, size, color, face, bold, spacing):
    default = {"face": face, "size": size, "color": color, "bold": bold, "spacing": spacing or 1.0}
    if isinstance(content, str):
        paras = [[(p, {})] for p in content.split("\n")]
    else:
        paras = content
    plain = "\n".join("".join(t for t, o in runs) for runs in paras)
    return paras, default, plain


def text_img(slide, x, y, w, h, content, size=18, color=None, face=DISPLAY, bold=False, align="l", anchor="t",
             name=None, spacing=None, extrude=None, shadow=None, check=True):
    color = color or C["ink"]
    paras, default, plain = _paras(content, size, color, face, bold, spacing)
    pad = 0.15 if (extrude or shadow) else 0.02
    img = raster.render(paras, w, h, default, align, anchor, pad_in=pad, extrude=extrude, shadow=shadow)
    if check:
        lines = raster._layout(paras, int(w * raster.DPI), default, raster.DPI)
        tot = sum(l[4] for l in lines) / raster.DPI
        widest = max((l[1] for l in lines), default=0) / raster.DPI
        if tot > h + 0.02 or widest > w + 0.02:
            WARNINGS.append("%s: '%s' (%spt) needs %.2fx%.2f in %.2fx%.2f" % (name or plain[:20], plain[:40], size, widest, tot, w, h))
    path = raster.save(img, ("t", paras, default, w, h, align, anchor, pad, extrude, shadow))
    pic = slide.shapes.add_picture(path, E(x - pad), E(y - pad), E(w + 2 * pad), E(h + 2 * pad))
    set_name(pic, name or ("text " + plain[:30]))
    set_descr(pic, plain)
    return pic


def label(slide, x, y, w, h, content, size=16, color="FFFFFF", face=DISPLAY, bold=False, fill="6C5CE7", radius=None,
          align="c", anchor="m", margins=(0.12, 0.05), alpha=100, line=None, line_w=0.0, shadow_on=True, gloss=True,
          oval=False, name=None, spacing=None, check=True):
    """A filled shape with its caption, rendered as one picture (animates and links as a unit)."""
    paras, default, plain = _paras(content, size, color, face, bold, spacing) if content else (None, None, "")
    r = (min(w, h) / 2) if radius is None else radius
    img, pad = raster.box_image(w, h, fill, r, paras, default, align, anchor, margins, int(alpha * 2.55), line, line_w,
                                shadow_on, gloss, oval)
    if check and paras:
        lines = raster._layout(paras, int((w - 2 * margins[0]) * raster.DPI), default, raster.DPI)
        tot = sum(l[4] for l in lines) / raster.DPI
        widest = max((l[1] for l in lines), default=0) / raster.DPI
        if tot > h - 2 * margins[1] + 0.02 or widest > w - 2 * margins[0] + 0.02:
            WARNINGS.append("label %s: '%s' (%spt) needs %.2fx%.2f" % (name or plain[:20], plain[:40], size, widest, tot))
    path = raster.save(img, ("b", paras, default, w, h, fill, r, align, anchor, margins, alpha, line, line_w, shadow_on,
                             gloss, oval))
    pic = slide.shapes.add_picture(path, E(x - pad), E(y - pad), E(w + 2 * pad), E(h + 2 * pad))
    set_name(pic, name or ("label " + plain[:30]))
    set_descr(pic, plain)
    return pic
