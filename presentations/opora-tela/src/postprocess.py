"""Final touches on the saved .pptx: Arial as the theme font, a true 16:9 slide size and a
preview thumbnail of the title slide. No fonts are embedded — every non-Arial text is a picture."""
import re
import sys
import zipfile
import os


def run(path, thumb=None):
    tmp = path + ".tmp"
    zin = zipfile.ZipFile(path)
    zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        name = item.filename
        if re.match(r"ppt/theme/theme\d+\.xml", name):
            s = data.decode("utf-8")
            s = re.sub(r'(<a:majorFont><a:latin typeface=")[^"]*(")', r"\1Arial\2", s)
            s = re.sub(r'(<a:minorFont><a:latin typeface=")[^"]*(")', r"\1Arial\2", s)
            data = s.encode("utf-8")
        elif name == "ppt/presentation.xml":
            data = data.decode("utf-8").replace(' type="screen4x3"', "").encode("utf-8")
        elif name == "docProps/thumbnail.jpeg" and thumb:
            data = open(thumb, "rb").read()
        zout.writestr(item, data)
    zin.close()
    zout.close()
    os.replace(tmp, path)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print("postprocessed")
