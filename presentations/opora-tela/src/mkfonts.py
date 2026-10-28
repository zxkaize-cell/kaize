import sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

src = sys.argv[1]
specs = [
    # (outfile, wght, family, subfamily, bold)
    ("Nunito-Regular.ttf", 400, "Nunito", "Regular", False),
    ("Nunito-Bold.ttf", 800, "Nunito", "Bold", True),
    ("NunitoBlack-Regular.ttf", 950, "Nunito Black", "Regular", False),
]
for out, w, fam, sub, bold in specs:
    f = TTFont(src)
    inst = instancer.instantiateVariableFont(f, {"wght": w})
    name = inst["name"]
    # drop typographic family names so apps use nameID 1/2
    name.names = [n for n in name.names if n.nameID not in (16, 17, 21, 22, 25)]
    full = fam if sub == "Regular" else f"{fam} {sub}"
    ps = (fam.replace(" ", "") + "-" + sub)
    for rec in list(name.names):
        if rec.nameID == 1: rec.string = fam
        elif rec.nameID == 2: rec.string = sub
        elif rec.nameID == 3: rec.string = f"{ps};custom"
        elif rec.nameID == 4: rec.string = full
        elif rec.nameID == 6: rec.string = ps
    os2 = inst["OS/2"]
    os2.usWeightClass = 700 if bold else (900 if fam.endswith("Black") else 400)
    sel = os2.fsSelection & ~(0b1100001)  # clear italic, bold, regular
    sel |= (1 << 5) if bold else (1 << 6)
    os2.fsSelection = sel
    inst["head"].macStyle = 1 if bold else 0
    os2.fsType = 0
    for t in ("STAT", "MVAR", "HVAR", "fvar", "gvar", "avar"):
        if t in inst:
            del inst[t]
    inst.save(out)
    print(out, "fsType", os2.fsType, "weight", os2.usWeightClass)
