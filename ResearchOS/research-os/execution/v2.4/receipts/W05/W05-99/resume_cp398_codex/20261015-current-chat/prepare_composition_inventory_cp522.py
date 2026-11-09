import hashlib,json,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99';B=Path(__file__).parent
base='4f4023c956f84d65743f39ce77d6c8899a21ada1';a='f48fca0e4013bda19913a34d91da0cd23157a08b'
# Read the authoritative exact SHA from the accepted A manifest rather than use an abbreviated remembered identifier.
am=json.loads((E/'qualification_failure_b_revision02_independent_review_codex/20261015-current-chat/review.json').read_text(encoding='utf-8-sig'));a=am['base']
commits={'A_accepted':(base,a),'B_r2_rejected_reference_only':(a,am['candidate']),'STOP_r5_author_not_accepted':(base,'37a1f6d3e9d1c64b0d5fab5d30bc8000dd4ac373'),'schema25_source53_plus_historical_fixture_accepted_source_only':(base,'6802628826dcc4b79a16ced20a8e26f7e5494a1b')}
git=['git','-c','maintenance.auto=false','-c','gc.auto=0']
def g(*args):return subprocess.check_output(git+list(args),cwd=R)
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
lanes={k:{'base':v[0],'candidate':v[1],'tree':g('rev-parse',v[1]+'^{tree}').decode().strip(),'paths':g('diff','--name-only',v[0],v[1]).decode().splitlines()}for k,v in commits.items()}
q=E/'qualification_boot_supplement_independent_design_review_codex/20261015-current-chat/design-review.json';review=json.loads(q.read_text(encoding='utf-8-sig'));raw=review['source_paths'];cp=[x if isinstance(x,str)else x['path']for x in raw];assert len(cp)==57
lanes['C_conditional_planned_not_issued']={'paths':cp,'design_ref':ref(q),'status':'NO_SOURCE_CARD_BEFORE_B_ACCEPTED_AND_EXACT_COMPOSITE'}
overlaps=[];keys=list(lanes)
for i,k in enumerate(keys):
 for l in keys[i+1:]:
  paths=sorted(set(lanes[k]['paths'])&set(lanes[l]['paths']))
  if paths:overlaps.append({'left':k,'right':l,'paths':paths,'count':len(paths)})
allpaths={p for x in lanes.values()for p in x['paths']};pins={}
for p in sorted(allpaths):
 x={}
 for k,v in lanes.items():
  if 'candidate'not in v or p not in v['paths']:continue
  data=g('show',v['candidate']+':'+p);x[k]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
 pins[p]=x
out={'schema':'researchos.provisional-source-composition-inventory.v1','status':'PROVISIONAL_READONLY_NO_SOURCE_INTEGRATION_AUTHORITY','lanes':lanes,'overlaps':overlaps,'source_file_pins':pins,'limits':['B-r2 is independently rejected; this inventory grants no acceptance and must be refreshed to frozen accepted B-r3+future exact revisions.','STOP-r5 independent review pending; no Main integration from author freeze.','C57 is a conditional design proposal; no Source C card or original operation.','Schema25 Source53+fixture source-only acceptance must be adapted after schema24 qualification repair, no premature migration/integration.','Main old dirty20/protected9 are not candidate Source bytes; Root must preserve them separately.'],'actual_authority':False,'formal_increment':0}
p=B/'provisional-composition-inventory-cp522.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'output':ref(p),'lane_counts':{k:len(v['paths'])for k,v in lanes.items()},'overlaps':overlaps,'unique_paths':len(allpaths),'status':out['status']},ensure_ascii=False))
