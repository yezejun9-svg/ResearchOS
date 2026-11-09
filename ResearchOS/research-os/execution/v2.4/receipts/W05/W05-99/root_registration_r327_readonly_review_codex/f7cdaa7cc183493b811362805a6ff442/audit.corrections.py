from pathlib import Path
import ast, hashlib, json
R=Path('D:/作品集/ResearchOS/research-os'); O=Path(__file__).parent
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r327-efa7776ec48e4a7abaa92ce85eb0dace'
def path(p):
 p=Path(p); return p if p.is_absolute() else R/p
def ref(p):
 p=path(p); raw=p.read_bytes(); return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p): return json.loads(path(p).read_bytes())
def write(n,obj):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
a=read(O/'audit.json'); b=read(N/'binding.json'); p=read(N/'prepared_refs.json')
module=path(b['metadata_code_refs'][6]['path']); tree=ast.parse(module.read_bytes())
wip=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='WIP_KEYS' for t in n.targets))
allowed={str(path(x['path'])).casefold():(x['sha256'],x['bytes']) for x in read(b['runtime_resources_ref']['path'])['files']}
for x in b['metadata_code_refs']+[b[k] for k in ['runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref','debug_tree_helper_ref']]:allowed[str(path(x['path'])).casefold()]=(x['sha256'],x['bytes'])
observed=read(N/'prepare.runtime.json')['files']
replacements={'WIP keys present exactthree': wip==('cli43_fresh_compiler_held2_scope_ref','cli43_fresh_compiler_current_source_authority_ref','cli43_fresh_compiler_controller_review_ref')}
for x in observed:
 name='observed runtime pin '+x['path']
 if any(z['check']==name and not z['passed'] for z in a['checks']):replacements[name]=allowed.get(str(path(x['path'])).casefold())==(x['sha256'],x['bytes'])
assert len(replacements)==2 and {x['check'] for x in a['failed_checks']}==set(replacements)
corrections=[]
for x in a['checks']:
 if x['check'] in replacements:
  corrections.append({'original_check':dict(x),'corrected_passed':replacements[x['check']]});x['passed']=replacements[x['check']]
for x in p['canonical_before']:
 current=ref(x['path']);a['checks'].append({'check':'final live canonical '+x['path'],'passed':current['sha256']==x['sha256'] and current['bytes']==x['bytes']})
for name in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']:
 a['checks'].append({'check':'final absent '+name,'passed':not path(b[name]).exists()})
a['failed_checks']=[x for x in a['checks'] if not x['passed']]
a['static_predicate_corrections']={'original_audit_ref':ref(O/'audit.json'),'original_auditor_ref':ref(O/'audit.py'),'original_actual_outer_exit':0,'original_actual_Python_native_exit':0,'new_native_failure_origin':False,'scope_or_candidate_changed':False,'corrections':corrections,'basis':'Actual immutable v7 WIP_KEYS tuple at lines23-25; runtime producer rows +5 controller refs +metadata8 at117; same gate295-304. No target execution or broad resource rehash.'}
write('audit.corrected.json',a)
print(json.dumps({'checks':len(a['checks']),'failed_checks':a['failed_checks'],'corrected_audit_ref':ref(O/'audit.corrected.json')},ensure_ascii=False))
