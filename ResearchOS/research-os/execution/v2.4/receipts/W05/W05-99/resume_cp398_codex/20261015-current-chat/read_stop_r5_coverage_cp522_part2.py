import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent;S=R/'execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
v=read(S/'coverage.json');print('COVERAGE_WITHOUT_ALREADY_READ_SOURCE19',json.dumps({k:x for k,x in v.items()if k!='source19'},ensure_ascii=False))
out=[]
for name in read(S/'FINAL-manifest.json')['excluded_terminal_envelope']:
 p=S/name;x={'ref':ref(p)}
 if name=='0025.exit.txt':x['native_exit_text']=p.read_text(encoding='utf-8-sig')
 elif name=='0025.stderr.txt':x['stderr_text']=p.read_text(encoding='utf-8-sig')[:800]
 elif name=='0025.stdout.txt':x['stdout_tail']=p.read_text(encoding='utf-8-sig')[-800:]
 out.append(x)
print('EXCLUDED_CLOSED',json.dumps(out,ensure_ascii=False))
p=B/'stop-r5-review-terminal-closed-refs.json';assert not p.exists();p.write_text(json.dumps({'refs':out,'prior_read_full_raw_retained':'read-stop-r5-coverage-cp522.recipe.stdout.raw','no_missing_final_stream':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
