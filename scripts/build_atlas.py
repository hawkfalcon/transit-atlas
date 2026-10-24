"""Build a self-contained offline atlas: two factual networks + a planning notebook."""
from pathlib import Path
import base64,json,re
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'assets'
def uri(path,mime):return f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode()
css=((A/'app.css').read_text()+'\n'+(A/'saving.css').read_text()).replace('/*FONT_URI*/',uri(A/'manrope.ttf','font/ttf'))
css += '\n.intro p{color:#66766b}.scenario-note{color:#6c7b6b}.route-name small{color:#7c8b75}.route-frequency small{color:#7e8e75}.legend-note{color:#73866a}.map-title-card p{color:#667e65}.selected-card{max-height:calc(100% - 310px)}@media(max-width:760px){.selected-card{max-height:calc(100% - 250px)}}\n'
js=(A/'app.js').read_text().replace('/*CSV_B64*/',base64.b64encode((ROOT/'data/route-comparison.csv').read_bytes()).decode())
saving_js=(A/'saving.js').read_text().replace('/*PERFORMANCE_CSV_B64*/',base64.b64encode((ROOT/'data/route-performance-fy2025-26.csv').read_bytes()).decode())
payload=json.loads((ROOT/'data/network.json').read_text())
payload['planning']=json.loads((ROOT/'data/planning.json').read_text())
assert 'cutFactor' not in payload['meta'] and 'cutMethod' not in payload['meta']
template=(A/'index.template.html').read_text()
replacements={
 '/*LEAFLET_CSS*/':(A/'leaflet.css').read_text(),
 '/*APP_CSS*/':css,
 '/*SAVING_TAB*/':(A/'saving-tab.html').read_text(),
 '/*LEAFLET_JS*/':re.sub(r'//# sourceMappingURL=.*','',(A/'leaflet.js').read_text()),
 '/*DATA_JSON*/':json.dumps(payload,separators=(',',':')).replace('</','<\\/'),
 '/*BASEMAP_URI*/':uri(A/'basemap.webp','image/webp'),
 '/*BASEMAP_BOUNDS*/':(A/'basemap-bounds.json').read_text(),
 '/*APP_JS*/':js,
 '/*SAVING_JS*/':saving_js,
}
for key,value in replacements.items():template=template.replace(key,value)
assert not any(k in template for k in replacements)
assert '/*FONT_URI*/' not in template and 'data-mode="cut"' not in template
for name in ('Santa-Barbara-Transit-Atlas.html','index.html'):
    tmp=ROOT/(name+'.tmp');tmp.write_text(template);tmp.replace(ROOT/name)
print('Built offline atlas and live-preview index:',len(template.encode()),'bytes')
