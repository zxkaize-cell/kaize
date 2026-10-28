"""Animation, trigger, media, sound and transition XML for python-pptx slides.

PowerPoint stores all of this in <p:timing> and <p:transition>; python-pptx
exposes neither, so the XML is written here by hand following the shapes
PowerPoint itself saves.
"""
from lxml import etree

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "p14": "http://schemas.microsoft.com/office/powerpoint/2010/main",
    "p15": "http://schemas.microsoft.com/office/powerpoint/2012/main",
    "p159": "http://schemas.microsoft.com/office/powerpoint/2015/09/main",
}
RT_AUDIO = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio"
DECL = 'xmlns:p="%s" xmlns:a="%s" xmlns:r="%s"' % (NS["p"], NS["a"], NS["r"])


def q(tag):
    pre, local = tag.split(":")
    return "{%s}%s" % (NS[pre], local)


# ----------------------------------------------------------------- transitions
P14_KINDS = {"vortex", "switch", "flip", "ripple", "honeycomb", "prism", "doors", "window", "ferris",
             "gallery", "conveyor", "pan", "glitter", "warp", "flythrough", "flash", "shred", "reveal"}
P15_KINDS = {"curtains", "drape", "wind", "prestige", "fracture", "crush", "peelOff", "pageCurlDouble",
             "pageCurlSingle", "airplane", "origami", "fallOver"}


def set_transition(slide, kind="fade", dur=1200, adv_click=True, **attrs):
    """Attach a transition. kind: fade | morph | a p14 name | a p15 preset name."""
    sld = slide._element
    for old in sld.findall(q("p:transition")) + sld.findall(q("mc:AlternateContent")):
        sld.remove(old)
    adv = "" if adv_click else ' advClick="0"'
    spd = "slow" if dur >= 1000 else ("med" if dur >= 600 else "fast")
    fallback = '<p:transition spd="%s"%s><p:fade/></p:transition>' % (spd, adv)
    attr_s = "".join(' %s="%s"' % (k, v) for k, v in attrs.items())
    if kind == "fade":
        xml = '<p:transition %s spd="%s"%s><p:fade/></p:transition>' % (DECL, spd, adv)
    else:
        if kind == "morph":
            req, inner = "p159", '<p159:morph option="byObject"/>'
        elif kind in P14_KINDS:
            req, inner = "p14", "<p14:%s%s/>" % (kind, attr_s)
        elif kind in P15_KINDS:
            req, inner = "p15", '<p15:prstTrans prst="%s"%s/>' % (kind, attr_s)
        else:
            raise ValueError(kind)
        xml = (
            '<mc:AlternateContent %s xmlns:mc="%s" xmlns:p14="%s">'
            '<mc:Choice xmlns:%s="%s" Requires="%s">'
            '<p:transition spd="%s" p14:dur="%d"%s>%s</p:transition>'
            "</mc:Choice><mc:Fallback>%s</mc:Fallback></mc:AlternateContent>"
        ) % (DECL, NS["mc"], NS["p14"], req, NS[req], req, spd, dur, adv, inner, fallback)
    el = etree.fromstring(xml)
    anchor = sld.find(q("p:clrMapOvr"))
    if anchor is None:
        anchor = sld.find(q("p:cSld"))
    anchor.addnext(el)
    timing = sld.find(q("p:timing"))
    if timing is not None:  # timing must follow the transition
        sld.remove(timing)
        el.addnext(timing)


# --------------------------------------------------------------------- effects
class Fx:
    """One animation effect on one shape."""

    def __init__(self, shape, kind, dur=500, delay=0, sound=None, **kw):
        self.shape = shape
        self.spid = shape.shape_id
        self.kind = kind
        self.dur = dur
        self.delay = delay
        self.sound = sound  # name of a registered sound
        self.kw = kw

    # total time the effect occupies (for chaining "after previous")
    @property
    def length(self):
        if self.kind == "shake":
            return 800
        if self.kind == "pulse":
            return self.dur * 2
        return self.dur


ENTR = {
    "appear": (1, 0), "fade": (10, 0), "zoom": (53, 16), "pop": (53, 16), "float_up": (42, 0),
    "float_down": (47, 0), "fly_left": (2, 8), "fly_right": (2, 2), "fly_bottom": (2, 4), "fly_top": (2, 1),
    "grow_turn": (31, 0), "wipe_left": (22, 8), "wipe_right": (22, 2), "wipe_down": (22, 1), "wipe_up": (22, 4),
    "stretch_h": (17, 10), "bounce": (26, 0), "spin_in": (31, 0),
}
EXIT = {"fade_out": (10, 0), "zoom_out": (53, 16), "collapse_h": (17, 10)}
EMPH = {"pulse": (6, 0), "shake": (32, 0), "spin": (8, 0), "grow": (6, 0)}
MEDIA = {"play": (1, 0), "toggle": (2, 0)}


class _Ids:
    def __init__(self):
        self.n = 0

    def next(self):
        self.n += 1
        return self.n


def _tgt(spid):
    return '<p:tgtEl><p:spTgt spid="%d"/></p:tgtEl>' % spid


def _set_vis(ids, spid, val, delay=0):
    cond = '<p:stCondLst><p:cond delay="%d"/></p:stCondLst>' % delay
    return ('<p:set><p:cBhvr><p:cTn id="%d" dur="1" fill="hold">%s</p:cTn>%s'
            '<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            '<p:to><p:strVal val="%s"/></p:to></p:set>') % (ids.next(), cond, _tgt(spid), val)


def _anim(ids, spid, attr, keys, dur, delay=0, calc="lin"):
    tavs = "".join(
        '<p:tav tm="%d"><p:val>%s</p:val></p:tav>' % (
            int(t * 100000),
            ('<p:fltVal val="%s"/>' % v) if isinstance(v, (int, float)) else ('<p:strVal val="%s"/>' % v))
        for t, v in keys)
    cond = ('<p:stCondLst><p:cond delay="%d"/></p:stCondLst>' % delay) if delay else ""
    return ('<p:anim calcmode="%s" valueType="num"><p:cBhvr><p:cTn id="%d" dur="%d" fill="hold">%s</p:cTn>%s'
            '<p:attrNameLst><p:attrName>%s</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst>%s</p:tavLst></p:anim>'
            ) % (calc, ids.next(), dur, cond, _tgt(spid), attr, tavs)


def _effect(ids, spid, trans, filt, dur, delay=0):
    cond = ('<p:stCondLst><p:cond delay="%d"/></p:stCondLst>' % delay) if delay else ""
    return ('<p:animEffect transition="%s" filter="%s"><p:cBhvr><p:cTn id="%d" dur="%d">%s</p:cTn>%s</p:cBhvr></p:animEffect>'
            ) % (trans, filt, ids.next(), dur, cond, _tgt(spid))


def _rot(ids, spid, by, dur, delay=0):
    cond = ('<p:stCondLst><p:cond delay="%d"/></p:stCondLst>' % delay) if delay else ""
    return ('<p:animRot by="%d"><p:cBhvr><p:cTn id="%d" dur="%d" fill="hold">%s</p:cTn>%s'
            '<p:attrNameLst><p:attrName>r</p:attrName></p:attrNameLst></p:cBhvr></p:animRot>') % (
        by, ids.next(), dur, cond, _tgt(spid))


def _behaviours(ids, fx):
    s, d, k = fx.spid, fx.dur, fx.kind
    out = []
    if k in ENTR:
        out.append(_set_vis(ids, s, "visible"))
        if k == "fade":
            out.append(_effect(ids, s, "in", "fade", d))
        elif k == "zoom":
            out += [_anim(ids, s, "ppt_w", [(0, 0), (1, "#ppt_w")], d), _anim(ids, s, "ppt_h", [(0, 0), (1, "#ppt_h")], d),
                    _effect(ids, s, "in", "fade", d)]
        elif k == "pop":
            kw = [(0, 0), (0.6, "#ppt_w*1.12"), (0.8, "#ppt_w*0.96"), (1, "#ppt_w")]
            kh = [(0, 0), (0.6, "#ppt_h*1.12"), (0.8, "#ppt_h*0.96"), (1, "#ppt_h")]
            out += [_anim(ids, s, "ppt_w", kw, d), _anim(ids, s, "ppt_h", kh, d), _effect(ids, s, "in", "fade", int(d * 0.4))]
        elif k in ("float_up", "float_down"):
            off = "#ppt_y+.1" if k == "float_up" else "#ppt_y-.1"
            out += [_effect(ids, s, "in", "fade", d), _anim(ids, s, "ppt_x", [(0, "#ppt_x"), (1, "#ppt_x")], d),
                    _anim(ids, s, "ppt_y", [(0, off), (1, "#ppt_y")], d)]
        elif k.startswith("fly_"):
            start = {"fly_left": ("0-#ppt_w/2", None), "fly_right": ("1+#ppt_w/2", None),
                     "fly_bottom": (None, "1+#ppt_h/2"), "fly_top": (None, "0-#ppt_h/2")}[k]
            out += [_anim(ids, s, "ppt_x", [(0, start[0] or "#ppt_x"), (1, "#ppt_x")], d),
                    _anim(ids, s, "ppt_y", [(0, start[1] or "#ppt_y"), (1, "#ppt_y")], d)]
        elif k in ("grow_turn", "spin_in"):
            rot = 90 if k == "grow_turn" else -360
            out += [_anim(ids, s, "ppt_w", [(0, 0), (1, "#ppt_w")], d), _anim(ids, s, "ppt_h", [(0, 0), (1, "#ppt_h")], d),
                    _anim(ids, s, "style.rotation", [(0, rot), (1, 0)], d), _effect(ids, s, "in", "fade", d)]
        elif k.startswith("wipe_"):
            out.append(_effect(ids, s, "in", "wipe(%s)" % k.split("_")[1].replace("left", "left"), d))
        elif k == "stretch_h":
            out += [_anim(ids, s, "ppt_w", [(0, 0), (1, "#ppt_w")], d), _anim(ids, s, "ppt_h", [(0, "#ppt_h"), (1, "#ppt_h")], d)]
        elif k == "bounce":
            ky = [(0, "#ppt_y-0.3"), (0.45, "#ppt_y"), (0.62, "#ppt_y-0.06"), (0.78, "#ppt_y"), (0.9, "#ppt_y-0.015"), (1, "#ppt_y")]
            out += [_anim(ids, s, "ppt_x", [(0, "#ppt_x"), (1, "#ppt_x")], d), _anim(ids, s, "ppt_y", ky, d),
                    _effect(ids, s, "in", "fade", int(d * 0.3))]
    elif k in EXIT:
        if k == "fade_out":
            out.append(_effect(ids, s, "out", "fade", d))
        elif k == "zoom_out":
            out += [_anim(ids, s, "ppt_w", [(0, "#ppt_w"), (1, 0)], d), _anim(ids, s, "ppt_h", [(0, "#ppt_h"), (1, 0)], d),
                    _effect(ids, s, "out", "fade", d)]
        elif k == "collapse_h":
            out += [_anim(ids, s, "ppt_w", [(0, "#ppt_w"), (1, 0)], d), _anim(ids, s, "ppt_h", [(0, "#ppt_h"), (1, "#ppt_h")], d)]
        out.append(_set_vis(ids, s, "hidden", delay=max(d - 1, 0)))
    elif k == "pulse":
        scale = fx.kw.get("scale", 112000)
        out.append(('<p:animScale><p:cBhvr><p:cTn id="%d" dur="%d" autoRev="1" fill="hold"/>%s</p:cBhvr>'
                    '<p:by x="%d" y="%d"/></p:animScale>') % (ids.next(), d, _tgt(s), scale, scale))
    elif k == "grow":
        scale = fx.kw.get("scale", 107000)
        out.append(('<p:animScale><p:cBhvr><p:cTn id="%d" dur="%d" decel="100000" fill="hold"/>%s</p:cBhvr>'
                    '<p:by x="%d" y="%d"/></p:animScale>') % (ids.next(), d, _tgt(s), scale, scale))
    elif k == "shake":
        a = 240000
        steps = [(a, 100, 0), (-2 * a, 200, 100), (2 * a, 200, 300), (-2 * a, 200, 500), (a, 100, 700)]
        out += [_rot(ids, s, by, du, de) for by, du, de in steps]
    elif k == "spin":
        out.append(_rot(ids, s, 21600000, d))
    elif k == "bob":
        out.append(('<p:animMotion origin="layout" path="M 0 0 L 0 %s E" pathEditMode="relative" rAng="0" ptsTypes="AA">'
                    '<p:cBhvr><p:cTn id="%d" dur="%d" fill="hold"/>%s<p:attrNameLst><p:attrName>ppt_x</p:attrName>'
                    '<p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:rCtr x="0" y="0"/></p:animMotion>'
                    ) % (fx.kw.get("dy", "-0.025"), ids.next(), d, _tgt(s)))
    elif k == "play":
        out.append(('<p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr><p:cTn id="%d" dur="%d" fill="hold"/>%s'
                    '</p:cBhvr></p:cmd>') % (ids.next(), d, _tgt(s)))
    elif k == "toggle":
        out.append(('<p:cmd type="call" cmd="togglePause"><p:cBhvr><p:cTn id="%d" dur="1" fill="hold"/>%s'
                    '</p:cBhvr></p:cmd>') % (ids.next(), _tgt(s)))
    else:
        raise ValueError(k)
    return out


def _preset(fx):
    k = fx.kind
    if k in ENTR:
        return "entr", ENTR[k]
    if k in EXIT:
        return "exit", EXIT[k]
    if k in EMPH:
        return "emph", EMPH[k]
    if k == "bob":
        return "path", (0, 0)
    if k in MEDIA:
        return "mediacall", MEDIA[k]
    raise ValueError(k)


# -------------------------------------------------------------------- timeline
class Timeline:
    """Builds <p:timing> for one slide.

    main sequence:  tl.begin([...]) / tl.click([...]) start a group,
                    tl.then([...], delay) chains an "after previous" step.
    triggers:       trig = tl.trigger(shape, [...]); trig.then([...], delay).
    media:          tl.media(video_shape, loop=True).
    """

    def __init__(self, slide, sounds=None):
        self.slide = slide
        self.sounds = sounds or {}  # name -> path of a wav
        self.main = []  # groups: {"start": "begin"|"click", "steps": [(delay, [fx...])]}
        self.triggers = []  # (shape, steps)
        self.medias = []
        self._sound_rids = {}

    def begin(self, fxs, delay=0):
        assert not self.main, "begin() must be the first main-sequence group"
        self.main.append({"start": "begin", "steps": [(delay, list(fxs))]})
        return self

    def click(self, fxs):
        self.main.append({"start": "click", "steps": [(0, list(fxs))]})
        return self

    def then(self, fxs, delay=0):
        self.main[-1]["steps"].append((delay, list(fxs)))
        return self

    def trigger(self, shape, fxs):
        t = _Trigger(shape, [(0, list(fxs))])
        self.triggers.append(t)
        return t

    def media(self, shape, loop=False, vol=80000):
        self.medias.append((shape, loop, vol))
        return self

    # ------------------------------------------------------------- rendering
    def _sound_rid(self, name):
        if name not in self._sound_rids:
            part = self.slide.part
            from pptx.opc.package import Part
            from pptx.opc.packuri import PackURI
            pkg = part.package
            existing = getattr(pkg, "_kid_sound_parts", {})
            if name not in existing:
                idx = len(existing) + 1
                blob = open(self.sounds[name], "rb").read()
                existing[name] = Part(PackURI("/ppt/media/sound%d.wav" % idx), "audio/wav", pkg, blob)
                pkg._kid_sound_parts = existing
            self._sound_rids[name] = part.relate_to(existing[name], RT_AUDIO)
        return self._sound_rids[name]

    def _fx_xml(self, ids, fx, node, grp):
        cls, (pid, sub) = _preset(fx)
        ctn_id = ids.next()
        g = grp.get(fx.spid, 0)
        grp[fx.spid] = g + 1
        self._built.append((fx, g))
        extra = ""
        if fx.kind == "bob":
            extra = ' accel="50000" decel="50000" autoRev="1" repeatCount="indefinite"'
        beh = "".join(_behaviours(ids, fx))
        snd = ""
        if fx.sound:
            rid = self._sound_rid(fx.sound)
            snd = ('<p:subTnLst><p:audio><p:cMediaNode><p:cTn id="%d" display="0" masterRel="sameClick">'
                   '<p:stCondLst><p:cond evt="begin" delay="0"><p:tn val="%d"/></p:cond></p:stCondLst>'
                   '<p:endCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond>'
                   '</p:endCondLst></p:cTn><p:tgtEl><p:sndTgt r:embed="%s" name="%s.wav"/></p:tgtEl>'
                   '</p:cMediaNode></p:audio></p:subTnLst>') % (ids.next(), ctn_id, rid, fx.sound)
        return ('<p:par><p:cTn id="%d" presetID="%d" presetClass="%s" presetSubtype="%d"%s fill="hold" grpId="%d" '
                'nodeType="%s"><p:stCondLst><p:cond delay="%d"/></p:stCondLst><p:childTnLst>%s</p:childTnLst>%s'
                '</p:cTn></p:par>') % (ctn_id, pid, cls, sub, extra, g, node, fx.delay, beh, snd)

    def _steps(self, ids, steps, first_node, grp):
        out = []
        t = 0
        prev_len = 0
        for si, (delay, fxs) in enumerate(steps):
            t = (t + prev_len + delay) if si else delay
            step_id = ids.next()
            inner = []
            for fi, fx in enumerate(fxs):
                if fi:
                    node = "withEffect"
                else:
                    node = first_node if si == 0 else "afterEffect"
                inner.append(self._fx_xml(ids, fx, node, grp))
            out.append('<p:par><p:cTn id="%d" fill="hold"><p:stCondLst><p:cond delay="%d"/></p:stCondLst>'
                       '<p:childTnLst>%s</p:childTnLst></p:cTn></p:par>' % (step_id, t, "".join(inner)))
            prev_len = max(fx.delay + fx.length for fx in fxs)
        return "".join(out)

    def render(self):
        ids = _Ids()
        self._built = []
        grp = {}
        root_id = ids.next()  # 1
        body = []
        if self.main:
            main_id = ids.next()  # 2
            groups = []
            for g in self.main:
                gid = ids.next()
                steps = self._steps(ids, g["steps"], "clickEffect" if g["start"] == "click" else "afterEffect", grp)
                if g["start"] == "begin":
                    cond = '<p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="%d"/></p:cond>' % main_id
                else:
                    cond = '<p:cond delay="indefinite"/>'
                groups.append('<p:par><p:cTn id="%d" fill="hold"><p:stCondLst>%s</p:stCondLst><p:childTnLst>%s'
                              '</p:childTnLst></p:cTn></p:par>' % (gid, cond, steps))
            body.append('<p:seq concurrent="1" nextAc="seek"><p:cTn id="%d" dur="indefinite" nodeType="mainSeq">'
                        '<p:childTnLst>%s</p:childTnLst></p:cTn>'
                        '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
                        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
                        '</p:seq>' % (main_id, "".join(groups)))
        for trig in self.triggers:
            seq_id = ids.next()
            gid = ids.next()
            steps = self._steps(ids, trig.steps, "clickEffect", grp)
            cond = '<p:cond evt="onClick" delay="0"><p:tgtEl><p:spTgt spid="%d"/></p:tgtEl></p:cond>' % trig.shape.shape_id
            body.append('<p:seq concurrent="1" nextAc="seek"><p:cTn id="%d" restart="whenNotActive" fill="hold" '
                        'evtFilter="cancelBubble" nodeType="interactiveSeq"><p:stCondLst>%s</p:stCondLst>'
                        '<p:endSync evt="end" delay="0"><p:rtn val="all"/></p:endSync><p:childTnLst>'
                        '<p:par><p:cTn id="%d" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
                        '<p:childTnLst>%s</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn>'
                        '<p:nextCondLst>%s</p:nextCondLst></p:seq>' % (seq_id, cond, gid, steps, cond))
        for shape, loop, vol in self.medias:
            rep = ' repeatCount="indefinite"' if loop else ""
            body.append('<p:video><p:cMediaNode vol="%d"><p:cTn id="%d"%s fill="hold" display="0"><p:stCondLst>'
                        '<p:cond delay="indefinite"/></p:stCondLst></p:cTn>%s</p:cMediaNode></p:video>'
                        % (vol, ids.next(), rep, _tgt(shape.shape_id)))
        if not body:
            return None
        builds = []
        seen = set()
        for fx, g in self._built:
            el = fx.shape._element
            if el.tag == q("p:sp") and (fx.spid, g) not in seen:
                seen.add((fx.spid, g))
                builds.append('<p:bldP spid="%d" grpId="%d" animBg="1"/>' % (fx.spid, g))
        bld = "<p:bldLst>%s</p:bldLst>" % "".join(builds) if builds else ""
        xml = ('<p:timing %s><p:tnLst><p:par><p:cTn id="%d" dur="indefinite" restart="never" nodeType="tmRoot">'
               '<p:childTnLst>%s</p:childTnLst></p:cTn></p:par></p:tnLst>%s</p:timing>') % (DECL, root_id, "".join(body), bld)
        return etree.fromstring(xml)

    def apply(self):
        sld = self.slide._element
        old = sld.find(q("p:timing"))
        if old is not None:
            sld.remove(old)
        el = self.render()
        if el is None:
            return
        anchor = None
        for tag in ("mc:AlternateContent", "p:transition", "p:clrMapOvr", "p:cSld"):
            found = sld.findall(q(tag))
            if found:
                anchor = found[-1]
                break
        anchor.addnext(el)


class _Trigger:
    def __init__(self, shape, steps):
        self.shape = shape
        self.steps = steps

    def then(self, fxs, delay=0):
        self.steps.append((delay, list(fxs)))
        return self
