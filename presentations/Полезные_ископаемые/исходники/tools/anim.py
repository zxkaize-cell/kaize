"""Inject PowerPoint custom animations (no slide transitions) into a pptxgenjs deck.

Spec per slide (JSON, produced by the JS builder):
{
  "slide": 1,
  "auto":    [effect, ...],            # start by themselves when the slide opens (absolute delays)
  "clicks":  [[effect, ...], ...],     # main sequence: each inner list is one click
  "triggers":[{"on": "objName", "fx": [effect, ...]}, ...],
  "audio":   [{"obj": "audName", "file": "path.mp3", "autoplay": true, "dur": 82337}],
}
effect = {"obj": name, "fx": "fade|float|zoom|pop|drop|wipeL|wipeU|appear|disappear|fadeOut|pulse|shake",
          "dur": ms, "delay": ms, "sound": "key"}
"""
import json, os, re, shutil, sys, zipfile
from lxml import etree

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
REL_AUDIO = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio"
REL_MEDIA = "http://schemas.microsoft.com/office/2007/relationships/media"
REL_IMAGE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
REL_SLIDE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
REL_HLINK = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"


class Ids:
    def __init__(self):
        self.n = 0

    def __call__(self):
        self.n += 1
        return self.n


def tgt(spid):
    return f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'


def set_vis(ids, spid, val, delay=0):
    return (f'<p:set><p:cBhvr><p:cTn id="{ids()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="{delay}"/></p:stCondLst></p:cTn>'
            f'{tgt(spid)}<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:to><p:strVal val="{val}"/></p:to></p:set>')


def anim_prop(ids, spid, attr, frames, dur, ease=True):
    tavs = "".join(f'<p:tav tm="{int(tm)}"><p:val><p:strVal val="{v}"/></p:val></p:tav>' for tm, v in frames)
    acc = ' decel="100000"' if ease else ''
    return (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr additive="base"><p:cTn id="{ids()}" dur="{dur}" fill="hold"{acc}/>'
            f'{tgt(spid)}<p:attrNameLst><p:attrName>{attr}</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:tavLst>{tavs}</p:tavLst></p:anim>')


def anim_effect(ids, spid, transition, filt, dur):
    return (f'<p:animEffect transition="{transition}" filter="{filt}"><p:cBhvr><p:cTn id="{ids()}" dur="{dur}"/>'
            f'{tgt(spid)}</p:cBhvr></p:animEffect>')


# (presetID, presetClass, presetSubtype) per effect
PRESETS = {
    "appear": (1, "entr", 0), "fade": (10, "entr", 0), "float": (42, "entr", 0), "drop": (47, "entr", 0),
    "zoom": (53, "entr", 16), "pop": (53, "entr", 16), "wipeL": (22, "entr", 8), "wipeU": (22, "entr", 4),
    "disappear": (1, "exit", 0), "fadeOut": (10, "exit", 0), "pulse": (6, "emph", 0), "shake": (35, "emph", 0),
    "sink": (42, "exit", 0),
}


def behaviours(ids, fx, spid, dur):
    if fx == "appear":
        return set_vis(ids, spid, "visible")
    if fx == "disappear":
        return set_vis(ids, spid, "hidden")
    if fx == "fade":
        return set_vis(ids, spid, "visible") + anim_effect(ids, spid, "in", "fade", dur)
    if fx == "float":  # fade in while rising a little, eased
        return (set_vis(ids, spid, "visible") + anim_effect(ids, spid, "in", "fade", dur)
                + anim_prop(ids, spid, "ppt_x", [(0, "#ppt_x"), (100000, "#ppt_x")], dur)
                + anim_prop(ids, spid, "ppt_y", [(0, "#ppt_y+.06"), (100000, "#ppt_y")], dur))
    if fx == "drop":  # fade in while settling down from above
        return (set_vis(ids, spid, "visible") + anim_effect(ids, spid, "in", "fade", dur)
                + anim_prop(ids, spid, "ppt_x", [(0, "#ppt_x"), (100000, "#ppt_x")], dur)
                + anim_prop(ids, spid, "ppt_y", [(0, "#ppt_y-.05"), (100000, "#ppt_y")], dur))
    if fx == "zoom":  # gentle zoom from 70 %
        return (set_vis(ids, spid, "visible")
                + anim_prop(ids, spid, "ppt_w", [(0, "#ppt_w*0.70"), (100000, "#ppt_w")], dur)
                + anim_prop(ids, spid, "ppt_h", [(0, "#ppt_h*0.70"), (100000, "#ppt_h")], dur)
                + anim_effect(ids, spid, "in", "fade", dur))
    if fx == "pop":  # springy zoom with a small overshoot
        return (set_vis(ids, spid, "visible")
                + anim_prop(ids, spid, "ppt_w", [(0, "#ppt_w*0.30"), (65000, "#ppt_w*1.08"), (100000, "#ppt_w")], dur, ease=False)
                + anim_prop(ids, spid, "ppt_h", [(0, "#ppt_h*0.30"), (65000, "#ppt_h*1.08"), (100000, "#ppt_h")], dur, ease=False)
                + anim_effect(ids, spid, "in", "fade", max(150, dur // 2)))
    if fx in ("wipeL", "wipeU"):
        f = "wipe(left)" if fx == "wipeL" else "wipe(down)"
        return set_vis(ids, spid, "visible") + anim_effect(ids, spid, "in", f, dur)
    if fx == "fadeOut":
        return anim_effect(ids, spid, "out", "fade", dur) + set_vis(ids, spid, "hidden", delay=max(dur - 1, 0))
    if fx == "sink":
        return (anim_effect(ids, spid, "out", "fade", dur)
                + anim_prop(ids, spid, "ppt_x", [(0, "#ppt_x"), (100000, "#ppt_x")], dur)
                + anim_prop(ids, spid, "ppt_y", [(0, "#ppt_y"), (100000, "#ppt_y+.04")], dur)
                + set_vis(ids, spid, "hidden", delay=max(dur - 1, 0)))
    if fx == "pulse":
        half = max(dur // 2, 100)
        return (f'<p:animScale><p:cBhvr><p:cTn id="{ids()}" dur="{half}" autoRev="1" fill="hold"/>{tgt(spid)}</p:cBhvr>'
                f'<p:by x="112000" y="112000"/></p:animScale>')
    if fx == "shake":
        fr = [(0, "#ppt_x"), (15000, "#ppt_x-0.012"), (32000, "#ppt_x+0.012"), (50000, "#ppt_x-0.010"),
              (68000, "#ppt_x+0.008"), (85000, "#ppt_x-0.004"), (100000, "#ppt_x")]
        return anim_prop(ids, spid, "ppt_x", fr, dur, ease=False)
    raise ValueError(fx)


class SlideAnim:
    def __init__(self, names, sounds):
        self.ids = Ids()
        self.names = names      # objectName -> (spid, is_sp)
        self.sounds = sounds    # sound key -> (rId, name)
        self.grp = {}           # spid -> next grpId
        self.bld = []           # (spid, grpId)

    def spid(self, name):
        if name not in self.names:
            raise KeyError(f"object '{name}' not on slide; known: {sorted(self.names)}")
        return self.names[name]

    def effect(self, e, node_type):
        spid, is_sp = self.spid(e["obj"])
        fx = e["fx"]
        pid, pcls, psub = PRESETS[fx]
        dur = int(e.get("dur", 500))
        g = self.grp.get(spid, 0)
        self.grp[spid] = g + 1
        if is_sp:
            self.bld.append((spid, g))
        ctn_id = self.ids()
        inner = behaviours(self.ids, fx, spid, dur)
        sub = ""
        if e.get("sound"):
            rid, nm = self.sounds[e["sound"]]
            sub = (f'<p:subTnLst><p:audio><p:cMediaNode vol="100000" showWhenStopped="0"><p:cTn id="{self.ids()}" display="0" masterRel="sameClick">'
                   f'<p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
                   f'<p:tgtEl><p:sndTgt r:embed="{rid}" name="{nm}"/></p:tgtEl></p:cMediaNode></p:audio></p:subTnLst>')
        return (f'<p:par><p:cTn id="{ctn_id}" presetID="{pid}" presetClass="{pcls}" presetSubtype="{psub}" fill="hold" '
                f'grpId="{g}" nodeType="{node_type}"><p:stCondLst><p:cond delay="{int(e.get("delay", 0))}"/></p:stCondLst>'
                f'<p:childTnLst>{inner}</p:childTnLst>{sub}</p:cTn></p:par>')

    def media_call(self, spid, dur, delay=0):
        return (f'<p:par><p:cTn id="{self.ids()}" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold" nodeType="withEffect">'
                f'<p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>'
                f'<p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr><p:cTn id="{self.ids()}" dur="{dur}" fill="hold"/>{tgt(spid)}</p:cBhvr></p:cmd>'
                f'</p:childTnLst></p:cTn></p:par>')

    def group(self, effects, first_node, delay_attr):
        """One click-group: outer par -> inner par (all effects with own delays)."""
        inner = "".join(self.effect(e, first_node if i == 0 else e.get("node", "withEffect")) for i, e in enumerate(effects))
        return (f'<p:par><p:cTn id="{self.ids()}" fill="hold"><p:stCondLst>{delay_attr}</p:stCondLst><p:childTnLst>'
                f'<p:par><p:cTn id="{self.ids()}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                f'{inner}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')

    def build(self, spec):
        root_id = self.ids()
        main_id = self.ids()
        groups = []
        auto = list(spec.get("auto", []))
        audio_items = [a for a in spec.get("audio", []) if a.get("autoplay")]
        if auto or audio_items:
            # first group starts on its own when the slide begins
            gid1 = self.ids()
            gid2 = self.ids()
            parts = []
            for a in audio_items:
                spid, _ = self.spid(a["obj"])
                parts.append(self.media_call(spid, int(a["dur"]), int(a.get("delay", 0))))
            for i, e in enumerate(auto):
                nt = "withEffect" if (i > 0 or audio_items) else "afterEffect"
                parts.append(self.effect(e, nt))
            groups.append(
                f'<p:par><p:cTn id="{gid1}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
                f'<p:cond evt="onBegin" delay="0"><p:tn val="{main_id}"/></p:cond></p:stCondLst><p:childTnLst>'
                f'<p:par><p:cTn id="{gid2}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                f'{"".join(parts)}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
        for clk in spec.get("clicks", []):
            groups.append(self.group(clk, "clickEffect", '<p:cond delay="indefinite"/>'))
        main = ""
        if groups:
            main = (f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="{main_id}" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
                    f'{"".join(groups)}</p:childTnLst></p:cTn>'
                    f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
                    f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>')
        trig = ""
        for t in spec.get("triggers", []):
            tsp, _ = self.spid(t["on"])
            seq_id = self.ids()
            body = self.group(t["fx"], "clickEffect", '<p:cond delay="0"/>')
            trig += (f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="{seq_id}" restart="whenNotActive" fill="hold" '
                     f'evtFilter="cancelBubble" nodeType="interactiveSeq"><p:stCondLst><p:cond evt="onClick" delay="0">{tgt(tsp)}</p:cond>'
                     f'</p:stCondLst><p:endSync evt="end" delay="0"><p:rtn val="all"/></p:endSync><p:childTnLst>{body}</p:childTnLst></p:cTn>'
                     f'<p:nextCondLst><p:cond evt="onClick" delay="0">{tgt(tsp)}</p:cond></p:nextCondLst></p:seq>')
        media_nodes = ""
        for a in spec.get("audio", []):
            spid, _ = self.spid(a["obj"])
            media_nodes += (f'<p:audio><p:cMediaNode vol="100000"><p:cTn id="{self.ids()}" fill="hold" display="0">'
                            f'<p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
                            f'<p:endCondLst><p:cond evt="onStopAudio" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:endCondLst>'
                            f'</p:cTn>{tgt(spid)}</p:cMediaNode></p:audio>')
        if not (main or trig or media_nodes):
            return None
        bld = "".join(f'<p:bldP spid="{s}" grpId="{g}" animBg="1"/>' for s, g in self.bld)
        bld = f"<p:bldLst>{bld}</p:bldLst>" if bld else ""
        return (f'<p:timing xmlns:p="{NS["p"]}" xmlns:r="{NS["r"]}"><p:tnLst><p:par><p:cTn id="{root_id}" dur="indefinite" restart="never" nodeType="tmRoot">'
                f'<p:childTnLst>{main}{trig}{media_nodes}</p:childTnLst></p:cTn></p:par></p:tnLst>{bld}</p:timing>')


def sanitize(root):
    """Fix pptxgenjs quirks the schema rejects: stray a:pPr between runs, buSzPct in 1/1000 %, English lang tags."""
    A = NS["a"]
    for para in root.iter(f"{{{A}}}p"):
        kids = list(para)
        for i, k in enumerate(kids):
            if k.tag == f"{{{A}}}pPr" and i > 0:
                para.remove(k)
    for b in list(root.iter(f"{{{A}}}buSzPct")):
        b.getparent().remove(b)
    for tag in ("rPr", "endParaRPr", "defRPr"):
        for r in root.iter(f"{{{A}}}{tag}"):
            if r.get("lang") == "en-US":
                r.set("lang", "ru-RU")


def add_rel(rels_root, rtype, target, external=False):
    used = {r.get("Id") for r in rels_root}
    n = 1
    while f"rId{n}" in used:
        n += 1
    el = etree.SubElement(rels_root, "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
    el.set("Id", f"rId{n}")
    el.set("Type", rtype)
    el.set("Target", target)
    if external:
        el.set("TargetMode", "External")
    return f"rId{n}"


def dedupe_media(work):
    """pptxgenjs stores one copy of an image per slide; keep one file per unique content."""
    import hashlib
    media = os.path.join(work, "ppt", "media")
    canon, remap = {}, {}
    for f in sorted(os.listdir(media)):
        h = hashlib.md5(open(os.path.join(media, f), "rb").read()).hexdigest() + os.path.splitext(f)[1]
        if h in canon:
            remap[f] = canon[h]
        else:
            canon[h] = f
    if not remap:
        return
    for base, _, files in os.walk(os.path.join(work, "ppt")):
        for f in files:
            if not f.endswith(".rels"):
                continue
            p = os.path.join(base, f)
            t = etree.parse(p)
            changed = False
            for r in t.getroot():
                tg = r.get("Target", "")
                name = tg.rsplit("/", 1)[-1]
                if "media/" in tg and name in remap:
                    r.set("Target", tg[: -len(name)] + remap[name])
                    changed = True
            if changed:
                t.write(p, xml_declaration=True, encoding="UTF-8", standalone=True)
    for f in remap:
        os.remove(os.path.join(media, f))


def process(src, spec_path, out, sound_files):
    """sound_files: key -> wav path (embedded once per slide that uses it)."""
    specs = {s["slide"]: s for s in json.load(open(spec_path))}
    work = out + ".dir"
    shutil.rmtree(work, ignore_errors=True)
    with zipfile.ZipFile(src) as z:
        z.extractall(work)
    media_dir = os.path.join(work, "ppt", "media")
    ct_path = os.path.join(work, "[Content_Types].xml")
    ct = etree.parse(ct_path)
    ctr = ct.getroot()
    cns = "http://schemas.openxmlformats.org/package/2006/content-types"

    def ensure_default(ext, ctype):
        for d in ctr.findall(f"{{{cns}}}Default"):
            if d.get("Extension") == ext:
                d.set("ContentType", ctype)
                return
        el = etree.Element(f"{{{cns}}}Default")
        el.set("Extension", ext)
        el.set("ContentType", ctype)
        ctr.insert(0, el)

    ensure_default("wav", "audio/wav")
    ensure_default("mp3", "audio/mpeg")
    copied = {}

    def copy_media(path, prefix):
        if path in copied:
            return copied[path]
        ext = os.path.splitext(path)[1]
        name = f"{prefix}{len(copied) + 1}{ext}"
        shutil.copy(path, os.path.join(media_dir, name))
        copied[path] = name
        return name

    for num, spec in specs.items():
        sp_path = os.path.join(work, "ppt", "slides", f"slide{num}.xml")
        rel_path = os.path.join(work, "ppt", "slides", "_rels", f"slide{num}.xml.rels")
        tree = etree.parse(sp_path)
        root = tree.getroot()
        rels = etree.parse(rel_path)
        rr = rels.getroot()
        names = {}
        for el in root.iter(f"{{{NS['p']}}}cNvPr"):
            parent = el.getparent().getparent()
            is_sp = parent.tag == f"{{{NS['p']}}}sp"
            names[el.get("name")] = (el.get("id"), is_sp)
        # click links (whole-shape hyperlinks to slides or web pages)
        for l in spec.get("links", []):
            spid, _ = names[l["obj"]]
            if "slide" in l:
                rid = add_rel(rr, REL_SLIDE, f"slide{l['slide']}.xml")
                action = "ppaction://hlinksldjump"
            else:
                rid = add_rel(rr, REL_HLINK, l["url"], external=True)
                action = None
            for el in root.iter(f"{{{NS['p']}}}cNvPr"):
                if el.get("id") == spid:
                    for h in el.findall(f"{{{NS['a']}}}hlinkClick"):
                        el.remove(h)
                    h = etree.Element(f"{{{NS['a']}}}hlinkClick")
                    h.set(f"{{{NS['r']}}}id", rid)
                    if action:
                        h.set("action", action)
                    el.insert(0, h)
        # sounds used on this slide
        keys = set()
        for grp in [spec.get("auto", [])] + spec.get("clicks", []) + [t["fx"] for t in spec.get("triggers", [])]:
            for e in grp:
                if e.get("sound"):
                    keys.add(e["sound"])
        sounds = {}
        for k in sorted(keys):
            mname = copy_media(sound_files[k], "sound")
            rid = add_rel(rr, REL_AUDIO, f"../media/{mname}")
            sounds[k] = (rid, f"{k}.wav")
        # audio objects: turn the placeholder picture into a real audio shape
        for a in spec.get("audio", []):
            spid, _ = names[a["obj"]]
            mname = copy_media(a["file"], "media")
            rid_link = add_rel(rr, REL_AUDIO, f"../media/{mname}")
            rid_media = add_rel(rr, REL_MEDIA, f"../media/{mname}")
            for el in root.iter(f"{{{NS['p']}}}cNvPr"):
                if el.get("id") == spid:
                    for h in el.findall(f"{{{NS['a']}}}hlinkClick"):
                        el.remove(h)
                    h = etree.SubElement(el, f"{{{NS['a']}}}hlinkClick")
                    h.set(f"{{{NS['r']}}}id", "")
                    h.set("action", "ppaction://media")
                    nvpr = el.getparent().find(f"{{{NS['p']}}}nvPr")
                    for c in list(nvpr):
                        nvpr.remove(c)
                    af = etree.SubElement(nvpr, f"{{{NS['a']}}}audioFile")
                    af.set(f"{{{NS['r']}}}link", rid_link)
                    ext = etree.fromstring(
                        f'<p:extLst xmlns:p="{NS["p"]}" xmlns:r="{NS["r"]}"><p:ext uri="{{DAA4B4D4-6D71-4841-9C94-3DE7FCFB9230}}">'
                        f'<p14:media xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" r:embed="{rid_media}"/></p:ext></p:extLst>')
                    nvpr.append(ext)
        sanitize(root)
        sa = SlideAnim(names, sounds)
        xml = sa.build(spec)
        if xml:
            timing = etree.fromstring(xml)
            for old in root.findall(f"{{{NS['p']}}}timing"):
                root.remove(old)
            # timing goes after clrMapOvr (and transition), before extLst
            anchor = root.find(f"{{{NS['p']}}}clrMapOvr")
            tr = root.find(f"{{{NS['p']}}}transition")
            if tr is not None:
                anchor = tr
            anchor.addnext(timing)
        tree.write(sp_path, xml_declaration=True, encoding="UTF-8", standalone=True)
        rels.write(rel_path, xml_declaration=True, encoding="UTF-8", standalone=True)
    ct.write(ct_path, xml_declaration=True, encoding="UTF-8", standalone=True)
    dedupe_media(work)
    if os.path.exists(out):
        os.remove(out)
    # [Content_Types].xml must be the first entry
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(ct_path, "[Content_Types].xml")
        for base, _, files in os.walk(work):
            for f in sorted(files):
                full = os.path.join(base, f)
                arc = os.path.relpath(full, work)
                if arc == "[Content_Types].xml":
                    continue
                ctype = zipfile.ZIP_STORED if arc.endswith((".mp3", ".mp4", ".jpg", ".png", ".jpeg")) else zipfile.ZIP_DEFLATED
                z.write(full, arc, compress_type=ctype)
    shutil.rmtree(work)


if __name__ == "__main__":
    src, spec, out, sounds_json = sys.argv[1:5]
    process(src, spec, out, json.load(open(sounds_json)))
    print("wrote", out)
