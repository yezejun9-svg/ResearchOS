from pathlib import Path
import json, hashlib, collections
R=Path('D:/作品集/ResearchOS/research-os'); O=Path(__file__).parent
def write(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def path(v):
 p=Path(v);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def key(r):return str(path(r['path']).resolve()).casefold()
def normalized(r):return (key(r),r['sha256'],r['bytes'])
checks=[];inputs={}
def check(n,ok,detail=None):checks.append({'name':n,'passed':bool(ok),'detail':detail})
def verify(r):
 actual=ref(r['path']);inputs[key(r)]=actual
 check('pin:'+r['path'],normalized(actual)==normalized(r));return path(r['path']).read_bytes()
def doc(r):return json.loads(verify(r))
d=json.loads((O/'inspection.json').read_bytes());x=json.loads((O/'contract.json').read_bytes())
q=doc(d['qualification_ref']);m=doc(d['manifest_ref']);c=doc(d['completion_ref']);request=doc(c['closure_request_ref'])
check('Root schema',m['schema']=='researchos.root-launch-closure-manifest.v2')
check('Root actor',m['actor']=='codex:/root')
check('Root no source/formal acceptance',m['source_acceptance'] is False and m['formal_increment']==0)
rows=m['members']; actual={key(r):r for r in rows}
check('Root unique canonical members',len(actual)==len(rows))
check('Root excludes itself',key(d['manifest_ref']) not in actual)
for row in rows:verify(row)
expected={}
def add(r):
 if isinstance(r,dict) and set(r)=={'path','sha256','bytes'}:
  k=key(r)
  if k in expected:check('duplicate read unchanged:'+r['path'],normalized(expected[k])==normalized(r))
  expected[k]=r
add(c['closure_request_ref'])
for k,v in request.items():
 if k.endswith('_ref'):add(v)
for v in request['additional_sealed_refs']:add(v)
grant=doc(request['grant_ref']);inv=doc(request['caller_invocation_ref'])
add(grant['scope_ref'])
for v in c['authorization_canonical_copy_refs']:add(v)
for k,v in inv.items():
 if k.endswith('_ref'):add(v)
manifests={}
for k in ('executor_manifest_ref','launcher_manifest_ref'):
 mm=doc(request[k]); manifests[k]=mm
 rr=mm['files'];base=path(request[k]['path']).parent.resolve()
 check(k+':count/self exclusion',mm['count']==len(rr) and mm['excluded_only_self'] is True)
 check(k+':own namespace',all(path(r['path']).resolve().is_relative_to(base) for r in rr))
 for r in rr:add(r)
add(d['completion_ref'])
missing=sorted(set(expected)-set(actual));extra=sorted(set(actual)-set(expected))
check('producer precise member reconstruction',not missing and not extra,{'missing':missing,'extra':extra})
check('producer reconstructed pins',all(normalized(v)==normalized(actual[k]) for k,v in expected.items() if k in actual))
check('run UUID request/completion',request['run_uuid']==c['run_uuid'])
check('source request/completion',request['source_commit']==c['source_commit'])
check('output root matches completion',path(request['new_closure_output_root']).resolve()==path(d['completion_ref']['path']).parent.resolve())
for rk,ck in [('scope_ref','source_scope_ref'),('grant_ref','grant_ref'),('caller_ref','caller_ref'),('caller_invocation_ref','caller_invocation_ref'),('tool_observation_ref','tool_observation_ref'),('executor_manifest_ref','executor_manifest_ref'),('launcher_manifest_ref','launcher_manifest_ref'),('terminal_action_input_ref','terminal_action_input_ref'),('terminal_tool_result_ref','terminal_tool_result_ref')]:
 check('request/completion:'+rk,normalized(request[rk])==normalized(c[ck]))
gate=R/'execution/v2.4/receipts/W13/W13-03/desktop58_root_authority_adapter_revision_preparation_codex/fde71451a31d4404b8e3d57b396f270c/authorization_adapter.v2.proposed.py'
gate_ref=ref(gate); inputs[key(gate_ref)]=gate_ref
gate_lines=gate.read_text(encoding='utf-8').splitlines()
snippet=[{'line':i+1,'text':line} for i,line in enumerate(gate_lines) if 249<=i+1<=261 or 312<=i+1<=321]
base=path(d['manifest_ref']['path']).parent.resolve()
outside=[r for r in rows if not path(r['path']).resolve().is_relative_to(base)]
out={'schema':'researchos.readonly-root-aggregate-diagnostic-audit.v1','checks':checks,'checks_count':len(checks),'failed_checks':[v for v in checks if not v['passed']], 'root_member_count':len(rows),'reconstructed_member_count':len(expected),'outside_manifest_parent_count':len(outside),'inside_manifest_parent_count':len(rows)-len(outside),'parent_counts':dict(collections.Counter(str(path(r['path']).parent) for r in rows)),'request_keys':list(request),'caller_invocation_keys':list(inv),'grant_keys':list(grant),'completion_keys':list(c),'qualification_keys':list(q),'request_additional_sealed_refs_count':len(request['additional_sealed_refs']),'gate_ref':gate_ref,'gate_lines':snippet,'input_refs':list(inputs.values()),'target_execution_performed':False,'new_failure_origins':[]}
write('audit.json',out)
print(json.dumps({k:out[k] for k in ['checks_count','failed_checks','root_member_count','reconstructed_member_count','outside_manifest_parent_count','request_additional_sealed_refs_count','caller_invocation_keys','grant_keys','completion_keys','qualification_keys']},ensure_ascii=False))
