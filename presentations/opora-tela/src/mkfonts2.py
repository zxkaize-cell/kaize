"""Static instances of Unbounded (display) and Caveat (accent) as single-weight families."""
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

specs = [("cand/Unbounded.ttf", 700, "Unbounded", "Unbounded-Regular.ttf"),
         ("cand/Caveat.ttf", 700, "Caveat", "Caveat-Regular.ttf")]
base = sys.argv[1]
for src, w, fam, out in specs:
    f = TTFont(base + "/" + src)
    inst = instancer.instantiateVariableFont(f, {"wght": w})
    name = inst["name"]
    name.names = [n for n in name.names if n.nameID not in (16, 17, 21, 22, 25)]
    for rec in name.names:
        if rec.nameID == 1: rec.string = fam
        elif rec.nameID == 2: rec.string = "Regular"
        elif rec.nameID == 3: rec.string = fam + "-Regular;custom"
        elif rec.nameID == 4: rec.string = fam
        elif rec.nameID == 6: rec.string = fam.replace(" ", "") + "-Regular"
    os2 = inst["OS/2"]
    os2.usWeightClass = 400
    os2.fsSelection = (os2.fsSelection & ~0b1100001) | (1 << 6)
    inst["head"].macStyle = 0
    os2.fsType = 0
    for t in ("STAT", "MVAR", "HVAR", "fvar", "gvar", "avar"):
        if t in inst:
            del inst[t]
    inst.save(out)
    cm = inst.getBestCmap()
    need = "«»—–…≈№+?!ЁёЙй·×"
    print(out, "missing:", [c for c in need if ord(c) not in cm])
