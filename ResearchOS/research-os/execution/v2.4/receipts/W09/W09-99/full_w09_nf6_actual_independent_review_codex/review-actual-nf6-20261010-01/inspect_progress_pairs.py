import json
from pathlib import Path

R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W09/W09-99'
Q=Path(__file__).resolve().parent
S=B/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
rows={}
for key in ('G01','G02'):
    for phase in ('compiler','producer'):
        path=S/('nf6-'+key+'-'+phase+'-progress.host-pair.root.json')
        binding=json.loads(path.read_text(encoding='utf-8'))
        raw=Path(binding['original_capture_ref']['path']).read_bytes()
        lines=[json.loads(x) for x in raw.splitlines()]
        rows[key+'/'+phase]={'binding':binding,'call':lines[1],'output':lines[2]}
out=Q/'progress-pair-shapes.json'
with out.open('xb') as stream:stream.write((json.dumps(rows,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(rows,ensure_ascii=False,indent=2))
print('ROOT_PYTHON_EXIT=0')
