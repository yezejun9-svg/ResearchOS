import pathlib,json
B=pathlib.Path(__file__).parent
p=B/'PHASE2-jobs/098-phase2-boot-d-owned-cache.json'
j=json.loads(p.read_text(encoding='utf-8'))
j['tag']='108-phase2-boot-d-all-temp'
d='D:/作品集/ResearchOS/research-os/.local/qualification-maintenance-c57-independent-review-20261025-tmp/native-d'
for key in ['TEMP','TMP','TMPDIR','GOTMPDIR']:j['env'][key]=d
(B/'PHASE2-jobs/108-phase2-boot-d-all-temp.json').write_text(json.dumps(j,indent=2),encoding='utf-8')
print(json.dumps(j['env'],indent=2))
