"""Embed Nunito into the .pptx and make it the theme font."""
import os, re, sys, zipfile, shutil

FONTS = [("Nunito", "regular", "~/.fonts/Nunito-Regular.ttf"), ("Nunito", "bold", "~/.fonts/Nunito-Bold.ttf"),
         ("Nunito Black", "regular", "~/.fonts/NunitoBlack-Regular.ttf")]
RT_FONT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"


def run(path):
    tmp = path + ".tmp"
    zin = zipfile.ZipFile(path)
    zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
    rids = {}
    for item in zin.infolist():
        data = zin.read(item.filename)
        name = item.filename
        if name == "[Content_Types].xml":
            s = data.decode("utf-8")
            if 'Extension="fntdata"' not in s:
                s = s.replace("<Default ", '<Default Extension="fntdata" ContentType="application/x-fontdata"/><Default ', 1)
            data = s.encode("utf-8")
        elif re.match(r"ppt/theme/theme\d+\.xml", name):
            s = data.decode("utf-8")
            s = re.sub(r'(<a:majorFont><a:latin typeface=")[^"]*(")', r"\1Nunito Black\2", s)
            s = re.sub(r'(<a:minorFont><a:latin typeface=")[^"]*(")', r"\1Nunito\2", s)
            data = s.encode("utf-8")
        elif name == "ppt/_rels/presentation.xml.rels":
            s = data.decode("utf-8")
            for i, (fam, style, fp) in enumerate(FONTS):
                rid = "rIdFont%d" % (i + 1)
                rids[(fam, style)] = rid
                s = s.replace("</Relationships>", '<Relationship Id="%s" Type="%s" Target="fonts/font%d.fntdata"/></Relationships>'
                              % (rid, RT_FONT, i + 1))
            data = s.encode("utf-8")
        zout.writestr(item, data)
    zin.close()
    # presentation.xml needs the rIds, so rewrite it in a second pass
    zout.close()
    zin = zipfile.ZipFile(tmp)
    final = path + ".final"
    zout = zipfile.ZipFile(final, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "ppt/presentation.xml":
            s = data.decode("utf-8")
            fams = {}
            for (fam, style), rid in rids.items():
                fams.setdefault(fam, []).append((style, rid))
            lst = "<p:embeddedFontLst>"
            for fam, styles in fams.items():
                lst += '<p:embeddedFont><p:font typeface="%s" pitchFamily="2" charset="0"/>' % fam
                for style in ("regular", "bold"):
                    for st, rid in styles:
                        if st == style:
                            lst += '<p:%s r:id="%s"/>' % (style, rid)
                lst += "</p:embeddedFont>"
            lst += "</p:embeddedFontLst>"
            s = re.sub(r"(<p:notesSz[^>]*/>)", r"\1" + lst, s, count=1)
            s = s.replace("<p:presentation ", '<p:presentation embedTrueTypeFonts="1" ', 1)
            s = s.replace(' type="screen4x3"', "")
            data = s.encode("utf-8")
        zout.writestr(item, data)
    for i, (fam, style, fp) in enumerate(FONTS):
        zout.write(os.path.expanduser(fp), "ppt/fonts/font%d.fntdata" % (i + 1))
    zout.close()
    zin.close()
    os.replace(final, path)
    os.remove(tmp)


if __name__ == "__main__":
    run(sys.argv[1])
    print("fonts embedded")
