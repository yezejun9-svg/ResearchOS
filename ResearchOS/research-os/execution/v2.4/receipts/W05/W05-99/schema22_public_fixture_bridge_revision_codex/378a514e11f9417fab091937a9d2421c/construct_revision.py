from pathlib import Path
import json,hashlib,uuid,difflib
r=Path(r'D:/作品集/ResearchOS/research-os');b=r/'execution/v2.4/receipts/W05/W05-99'
prior=b/'schema22_public_fixture_bridge_source_codex/3d7d237d23244950a6d9008753e3fde9'
actual=b/'integration_codex/prepared-historical-regression-root-a3014611fc9b4e9b'
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
assert ref(prior/'HDF.json')['sha256']=='7d5d39f04557592c54bbf9ff877d787542f8c34549e4cd284ae26a85a71ad037'
assert ref(prior/'MF.json')['sha256']=='177d8f3c3199a258b83b4acc7c29b7be67323966f9c023642a6ddd4ebc089819'
oldh=json.loads((prior/'HDF.json').read_text());oldm=json.loads((prior/'MF.json').read_text())
pins={}
for v in oldm['base_refs']+list(oldm['members'].values())+[ref(prior/'HDF.json'),ref(prior/'MF.json')]:
 current=ref(Path(v['path']));assert current==v,v['path'];pins[current['path']]=current
for n in ['validation.closed.json','prepared-and-historical-backup-regression.stdout.raw','prepared-and-historical-backup-regression.stderr.raw','prepared-and-historical-backup-regression.invocation.json','source-overlay.json']:
 v=ref(actual/n);pins[v['path']]=v
events=[json.loads(x) for x in (actual/'prepared-and-historical-backup-regression.stdout.raw').read_text().splitlines() if x.strip()]
assert any(x.get('Action')=='build-fail' for x in events)
assert not any(x.get('Test') and x.get('Action') in ['run','pass','fail','skip'] for x in events)
assert any('"time" imported and not used' in x.get('Output','') for x in events)
own=b/'schema22_public_fixture_bridge_revision_codex'/uuid.uuid4().hex
own.mkdir(parents=True,exist_ok=False)
old_sources={**oldh['source_refs'],**oldh['historical22_overlay_refs']}
for rel,v in old_sources.items():
 p=own/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(Path(v['path']).read_bytes())
rel='candidate-root/internal/domain/backup_configuration_upgrade_test.go'
p=own/rel;before=p.read_bytes();matches=[line for line in before.splitlines(keepends=True) if line.strip()==b'"time"'];assert len(matches)==1;line=matches[0]
assert before.count(line)==1 and b'time.' not in before
after=before.replace(line,b'',1);p.write_bytes(after)
assert before[:before.index(line)]+before[before.index(line)+len(line):]==after
unchanged=[k for k in old_sources if k!=rel and (own/k).read_bytes()==Path(old_sources[k]['path']).read_bytes()]
assert len(unchanged)==3
for n in ['build-profile.json']:
 (own/n).write_bytes((prior/n).read_bytes())
(own/'base-refs.json').write_text(json.dumps(list(pins.values()),indent=2)+'\n',encoding='utf-8')
delta={'change':'Remove the sole unused time import only','changed_member':rel,'before':old_sources[rel],'after':ref(p),'removed_bytes_utf8':line.decode(),'removed_byte_count':len(line),'exact_single_deletion':True,'all_function_bodies_and_assertions_byte_unchanged':True,'unchanged_members':{k:{'prior':old_sources[k],'current':ref(own/k)} for k in unchanged},'root_failure_classification':'GO_BUILD_FAILED_ZERO_TESTS_EXECUTED','root_failure_artifacts':[ref(actual/n) for n in ['validation.closed.json','prepared-and-historical-backup-regression.stdout.raw','prepared-and-historical-backup-regression.stderr.raw','prepared-and-historical-backup-regression.invocation.json']],'root_failure_recounted':False,'author_tests_executed':False}
(own/'revision-delta.json').write_text(json.dumps(delta,indent=2)+'\n',encoding='utf-8')
(own/'source.patch').write_text(''.join(difflib.unified_diff(before.decode().splitlines(keepends=True),after.decode().splitlines(keepends=True),fromfile=str(prior/rel),tofile=str(p))),encoding='utf-8')
print(json.dumps({'own':str(own),'changed':ref(p),'unchanged_count':len(unchanged),'input_count':len(pins),'removed_bytes':len(line)},indent=2))

