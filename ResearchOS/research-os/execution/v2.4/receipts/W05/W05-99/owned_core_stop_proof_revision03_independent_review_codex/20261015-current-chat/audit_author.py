from pathlib import Path
import json,hashlib,collections
r=Path(r'D:\作品集\ResearchOS\research-os');a=r/'execution/v2.4/receipts/W05/W05-99/owned_core_stop_proof_revision03_source_codex/20261015-current-chat';e=r/'execution/v2.4/receipts/W05/W05-99/owned_core_stop_proof_revision03_independent_review_codex/20261015-current-chat'
m=json.loads((a/'candidate-2816daac-final/manifest.json').read_text(encoding='utf-8'))
refs={}
def walk(v):
 if isinstance(v,dict):
  if 'path' in v and 'sha256' in v and 'bytes' in v:refs[v['path']]=v
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
walk(m)
checked=[]
for p,v in refs.items():
 raw=Path(p).read_bytes(); match=len(raw)==v['bytes'] and hashlib.sha256(raw).hexdigest()==v['sha256'];checked.append({'path':p,'match':match});assert match,p
ledger=json.loads((a/'candidate-2816daac-final/failure-and-gap-ledger.json').read_text(encoding='utf-8'))
rows=ledger['root_command_nonzero'];counts=collections.Counter(x['classification'] for x in rows)
seen=set(); records=[]
for item in rows:
 cap=Path(item['capture']);assert str(cap) not in seen;seen.add(str(cap));before=json.loads((cap/'before.json').read_text(encoding='utf-8'));after=json.loads((cap/'after.json').read_text(encoding='utf-8'));assert before['argv']==item['argv'];assert after['native_exit']==item['native_exit'] and item['native_exit']!=0
 out=(cap/'stdout.bin').read_text(encoding='utf-8',errors='replace');err=(cap/'stderr.bin').read_text(encoding='utf-8',errors='replace')
 records.append({**item,'raw_exit_matches':True,'stderr_excerpt':err[:1400],'stdout_excerpt':out[:1400]})
 if item['classification']=='DIAGNOSTIC_ERROR_RETAINED':print(cap.name,'EXIT',after['native_exit'],'STDOUT',out[:600],'STDERR',err[:900])
print('REFERENCES_VERIFIED',len(checked),'AUTHOR_NONZERO_COUNTS',dict(counts),'UNIQUE',len(seen));print('CAPTURE_GAPS',ledger['capture_gaps']);print('LIMITS',ledger['limits'])
cases=[]
for case in m['case_rows']:
 p=Path(case['case_result']['path']);d=json.loads(p.read_text(encoding='utf-8'));cases.append(d);print('AUTHOR_CASE',d.get('mode'),json.dumps(d,ensure_ascii=False)[-2300:])
(e/'author-evidence-audit.json').write_text(json.dumps({'verified_reference_count':len(checked),'references':checked,'nonzero_count':len(rows),'nonzero_counts':dict(counts),'prior_63_recounted':False,'raw_matched_nonzero_records':records,'cases':cases,'retained_capture_gaps':ledger['capture_gaps'],'retained_limits':ledger['limits']},ensure_ascii=False,indent=2),encoding='utf-8')
