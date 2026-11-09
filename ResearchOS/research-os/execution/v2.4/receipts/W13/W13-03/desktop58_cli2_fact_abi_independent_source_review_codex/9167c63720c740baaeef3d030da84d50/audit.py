from pathlib import Path
import ast,json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;P=R/'execution/v2.4/receipts/W05/W05-99';P13=R/'execution/v2.4/receipts/W13/W13-03'
N=P13/'desktop58_cli2_fact_abi_revision_preparation_codex/ddc11e9721a6490baf1f0032c6bf6d16'
D=P13/'desktop58_cli2_fact_abi_independent_diagnostic_codex/0e585dda44741be307e989c5b6749a0d'
QDIR=P/'cli58_successful_execution_independent_review_codex/83c89c410a1744b8b77d121fd44e5c5e'
C=[];READS={}
def path(p):
 p=Path(p);return p if p.is_absolute()else R/p
def pin(p):
 p=path(p);b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};READS[str(p)]=r;return r
def ck(n,v):C.append({'check':n,'passed':bool(v)})
def verify(r):
 a=pin(r['path']);ck('pin '+r['path'],a['sha256']==r['sha256']and a['bytes']==r['bytes']);return path(r['path'])
def read(p):
 p=verify(p)if isinstance(p,dict)else path(p);pin(p);return json.loads(p.read_bytes())
def save(n,d):
 with(O/n).open('xb')as f:f.write((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
h=read(N/'handoff.json');m=read(N/'manifest.json');iv=read(h['inverse']);sa=read(h['static_audit']);prior=read(D/'review.json')
ck('handoff expected SHA',pin(N/'handoff.json')['sha256']=='0afc843c0a4c6d0d23ce5cec5958a5b4568d984ec0ac667ec7414d630718a7e4');ck('manifest expected SHA',pin(N/'manifest.json')['sha256']=='8cd7ba9fe85dfc5be191597e36d6648fd4eca6cd21974b5028dfc518907b12ba')
rows=m['members'];paths=[]
for r in rows:
 p=verify(r);paths.append(str(p));ck('MF exact own namespace '+p.name,p.parent==N and p.name!='manifest.json')
ck('MF unique all source files',len(paths)==len(set(paths))and set(paths)=={str(p)for p in N.iterdir()if p.is_file()and p.name!='manifest.json'})
edits=iv['edits'];inverse=[];unchanged=[]
for name,d in edits.items():
 before=verify(d['before']).read_bytes();after=verify(d['after']).read_bytes()
 if name in ['adapter','pipeline','builder']:
  old=d['old'].encode();new=d['new'].encode();ck('unique replacement '+name,before.count(old)==after.count(new)==1);rebuilt=after.replace(new,old,1);ck('wholebyte inverse '+name,rebuilt==before);inverse.append({'file':name,'before_ref':d['before'],'after_ref':d['after'],'inverse_equal':rebuilt==before})
 elif name=='template':
  b=json.loads(before);a=json.loads(after);key=d['only_field_changed'];ck('template exact linked Gate',a[key]==h['gate']==d['new_field']and b[key]==d['old_field']);a[key]=b[key];ck('template sole field delta',a==b)
 else:
  np=edits['pipeline']['after'];op=edits['pipeline']['before'];newpath=str(path(np['path'])).replace('\\','\\\\').encode();oldpath=str(path(op['path'])).replace('\\','\\\\').encode()
  ck('wrapper two replacements only '+name,after.count(newpath)==after.count(np['sha256'].encode())==1)
  rebuilt=after.replace(newpath,oldpath,1).replace(np['sha256'].encode(),op['sha256'].encode(),1);ck('wholebyte wrapper inverse '+name,rebuilt==before);inverse.append({'file':name,'before_ref':d['before'],'after_ref':d['after'],'inverse_equal':rebuilt==before})
 if name!='template':
  at=ast.parse(after);bt=ast.parse(before);compile(after,str(d['after']['path']),'exec');ck('AST compilation '+name,True)
  if name in ['adapter','pipeline','builder']:
   aa={x.name:x for x in at.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};bb={x.name:x for x in bt.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};ck('definition names same '+name,set(aa)==set(bb))
   for key in aa:
    if name=='adapter'and key=='validate_cli2':continue
    eq=ast.dump(aa[key],include_attributes=False)==ast.dump(bb[key],include_attributes=False);ck('unchanged def '+name+'.'+key,eq);unchanged.append(name+'.'+key)
for k in ['gate','pipeline','builder','template']:verify(h[k])
for k,r in h['wrappers'].items():verify(r);ck('wrapper handoff links '+k,r==edits[k]['after'])
ck('pipeline exact new gate SHA once',verify(h['pipeline']).read_bytes().count(h['gate']['sha256'].encode())==1);ck('builder exact new gate SHA once',verify(h['builder']).read_bytes().count(h['gate']['sha256'].encode())==1)
gate=verify(h['gate']).read_bytes();oldgate=verify(edits['adapter']['before']).read_bytes()
ck('Reader.verify original byte return',b'return raw' in gate and b"raw_streams[stream] = reader.verify(ex[str(raw_path)])"in gate)
ck('no absent fact raw keys after local change',"fact['stdout_ref']"not in gate.decode()and"fact['stderr_ref']"not in gate.decode()and "['invocation_ref','verified_ref','stdout_ref','stderr_ref']"not in gate.decode())
ck('raw fixed map and verified exact result guards',all(x in gate.decode()for x in ["require(stage['label'] == label and stage['result_ref'] == fact['invocation_ref']", "require(verified == case_result", "raw_path = invocation_path.with_name(label+'.'+stream+'.raw')", "require(str(raw_path) in ex", "require(proof_path == expected_proof"]))
q=read(QDIR/'qualification.json');qm=read(QDIR/'manifest.json');ck('actual Q unchanged624',pin(QDIR/'qualification.json')['sha256']=='624607c5589a2210254ed4cae8208b5a2251fe09be62117938c2ac5ad9e3b1bc');ck('Q MF dynamic19 unchanged027',pin(QDIR/'manifest.json')['sha256']=='027ac6e548548754487475605546e935a349ea79c06db0ea5893075b7f780d20'and qm['count']==len(qm['entries'])==19)
e=q['evidence_refs'];em=read(e['executor_manifest_ref']);lm=read(e['launcher_manifest_ref']);rm=read(e['root_closed_manifest_ref']);ck('E125 L7 Root169 preserved',em['count']==len(em['files'])==125 and lm['count']==len(lm['files'])==7 and len(rm['members'])==169)
ex={str(path(r['path'])):r for r in em['files']};ck('Eunique125',len(ex)==125)
result=read(e['result_ref']);scope=read(e['scope_ref']);cases=[]
for i,case in enumerate(q['qualified_case_ids']):
 f=q['case_facts'][i];s=result['stages'][-2+i];c=result['cases'][i];label='case-%02d'%i;ip=path(f['invocation_ref']['path']);vp=path(f['verified_ref']['path'])
 ck('actual exactdict stage/fact '+label,s['label']==label and s['result_ref']==f['invocation_ref'])
 ck('actual two fact refs no raw '+label,'stdout_ref'not in f and 'stderr_ref'not in f and ip.name==label+'.invocation.json'and vp==ip.with_name(label+'.verified.json'))
 for k in ['invocation_ref','verified_ref']:ck('actual sealed fact '+label+k,ex[str(path(f[k]['path']))]==f[k]);verify(f[k])
 v=read(f['verified_ref']);inv=read(f['invocation_ref']);ck('verified exact full result '+label,v==c);ck('E root '+label,ip.parent==path(e['executor_manifest_ref']['path']).parent)
 raw={};pins={}
 for stream in ['stdout','stderr']:
  rp=ip.with_name(label+'.'+stream+'.raw');r=ex[str(rp)];raw[stream]=verify(r).read_bytes();pins[stream]=r
 def unique_pairs(items):
  z={}
  for k,v in items:
   if k in z:raise ValueError('duplicate key in original sealed JSONL')
   z[k]=v
  return z
 events=[json.loads(line.decode('utf-8',errors='strict'),object_pairs_hook=unique_pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))for line in raw['stdout'].splitlines()]
 leaf='TestCLIProtocolInteractiveAuthority/'+case;run=sum(x.get('Action')=='run'and x.get('Test')==leaf for x in events);passed=sum(x.get('Action')=='pass'and x.get('Test')==leaf for x in events);bad=sum(x.get('Action')in ['fail','skip']for x in events)
 ck('new exact JSONL leaf counts '+label,run==passed==1 and bad==0 and all(type(x)is dict for x in events));ck('real empty stderr '+label,raw['stderr']==b'')
 pp=path(c['proof_ref']['path']);expected=path(scope['new_export_root'])/'.cli43-build'/'case-evidence'/label/('TestCLIProtocolInteractiveAuthority_'+case)/'closed-proof.json';ck('original exact exported proof '+label,pp==expected);verify(c['proof_ref'])
 ck('native0 CLI0/3 semantic unchanged '+label,f['native_test_exit']==inv['actual_exit']==inv['result']['actual_exit']==0 and f['CLI_exit']==[0,3][i]and [g['independent_exit']for g in inv['result']['debug_capture']['process_generations']]==([0,0,0]if i==0 else[0,0,3]))
 cases.append({'case_id':case,'label':label,'stage_ref':s['result_ref'],'verified_ref':f['verified_ref'],'raw_refs':pins,'raw_line_count':len(events),'leaf_RUN':run,'leaf_PASS':passed,'FAIL_SKIP':bad,'expected_CLI_exit':[0,3][i],'native_test_exit':inv['actual_exit'],'proof_ref':c['proof_ref'],'new_fields_requirements_satisfied':True})
author_origins=[]
for r in h['failure_origins']:author_origins.append({'ref':r,'original_payload':read(r)})
out={'schema':'researchos.desktop58-cli2-fact-abi-independent-source-audit.v1','checks':C,'failed_checks':[c for c in C if not c['passed']],'wholefile_inverses':inverse,'unchanged_definitions':unchanged,'actual_case_raw_semantics':cases,'source_manifest_shape':{'keys':list(m),'member_count':len(rows)},'source_refs':{k:h[k]for k in ['gate','pipeline','builder','template','wrappers']},'prior_diagnostic_ref':pin(D/'review.json'),'prior_full_ABI_audit_ref':pin(D/'abi-audit.json'),'prior_predicate_correction_ref':pin(D/'audit-supplement.json'),'source_author_origins_preserved_not_recounted':author_origins,'input_refs':list(READS.values()),'candidate_imported':False,'candidate_executed':False,'product_calls':0,'new_failure_origins':[]}
save('audit.json',out)
print(json.dumps({'checks':len(C),'failed':out['failed_checks'],'case_facts':cases,'audit_ref':pin(O/'audit.json'),'new_failures':0},ensure_ascii=False))
