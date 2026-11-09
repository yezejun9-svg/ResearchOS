from pathlib import Path
import json,hashlib
OUT=Path(__file__).parent
LIVE=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/host-candidate-capture-20261104')
pins=json.loads((OUT/'pin-verification.json').read_text(encoding='utf-8'))['source_pins']
replace={}
for entry in pins:
 rel=entry['path'];path=OUT/'snapshot'/rel
 assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
 replace[str(LIVE/rel)]=str(path)
for part,extra in (('domain','independent-domain-extra.txt'),('host','independent-host-extra.txt')):
 rel='internal/'+part+('/runtime_tools_capture_test.go' if part=='domain' else '/runtime_check_delivery_windows_test.go')
 data=(OUT/'snapshot'/rel).read_text(encoding='utf-8')
 if part=='host':
  old='"encoding/binary"';assert data.count(old)==1
  data=data.replace(old,'"encoding/binary"\n\t"encoding/base64"')
 data+='\n'+(OUT/extra).read_text(encoding='utf-8')
 dest=OUT/('combined-'+part+'-test.go');dest.write_text(data,encoding='utf-8',newline='')
 replace[str(LIVE/rel)]=str(dest)
(OUT/'go-overlay.json').write_text(json.dumps({'Replace':replace},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='STAGED_OVERLAY_ONLY',production_source_replacements=4,test_replacements=2,source_modifications=0)))
