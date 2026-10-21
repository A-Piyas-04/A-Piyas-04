"""Read the public GitHub contribution SVG, recolor real reported levels, and save locally."""
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

URL = 'https://github.com/users/A-Piyas-04/contributions'
req = urllib.request.Request(URL, headers={'User-Agent': 'Profile-README-calendar/1.0', 'Accept': 'image/svg+xml,text/html'})
with urllib.request.urlopen(req, timeout=25) as resp:
    raw = resp.read().decode('utf-8')

# GitHub sometimes serves HTML wrapping the calendar SVG.
if '<svg' not in raw:
    raise RuntimeError('GitHub did not return a contribution SVG; keeping existing file unchanged')
raw = raw[raw.index('<svg'):]
raw = raw[:raw.rfind('</svg>')+6]
root = ET.fromstring(raw)
SVG = '{http://www.w3.org/2000/svg}'
rects = [el for el in root.iter() if el.tag in ('rect', SVG+'rect')]
palette = ['#26181F', '#315C3B', '#589D4E', '#A9DE55', '#E8D94F']
updated = 0
for rect in rects:
    level = rect.attrib.get('data-level')
    if level is None:
        continue
    try:
        n = int(level)
    except ValueError:
        continue
    rect.set('fill', palette[max(0,min(4,n))])
    rect.set('stroke', '#10070C')
    rect.set('stroke-width', '1')
    rect.attrib.pop('class', None)
    updated += 1

if updated < 100:
    raise RuntimeError(f'Only {updated} contribution cells found; refusing to publish inaccurate graph')
root.set('style', 'background:#10070C;color:#E5B5C7')
root.set('role','img')
root.set('aria-label','GitHub contribution calendar for A-Piyas-04, recolored by real activity levels')
ET.register_namespace('', 'http://www.w3.org/2000/svg')
output = Path('assets/contributions.svg')
output.parent.mkdir(exist_ok=True)
output.write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
print(f'Updated {updated} genuine contribution cells in {output}')
