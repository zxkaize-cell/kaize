import sys, zipfile, re
from lxml import etree
V="/root/.claude/skills/synced/24712791-6e12-43ba-b50d-51f8f1496d68_5a144236-568f-4220-a43c-5d521cd49348/pptx/scripts/office/schemas/ISO-IEC29500-4_2016/pml.xsd"
schema = etree.XMLSchema(etree.parse(V))
z = zipfile.ZipFile(sys.argv[1])
bad=0
for n in sorted(z.namelist()):
    if re.match(r'ppt/slides/slide\d+\.xml$', n):
        doc = etree.fromstring(z.read(n))
        # strip extLst (MS extensions use other namespaces/schemas)
        for ext in doc.iter('{http://schemas.openxmlformats.org/presentationml/2006/main}extLst'):
            for c in list(ext): ext.remove(c)
        if not schema.validate(doc):
            bad+=1
            errs=[e for e in schema.error_log]
            print(n, len(errs)); [print('   ', e.message[:220]) for e in errs[:6]]
print('slides with schema errors:', bad)
