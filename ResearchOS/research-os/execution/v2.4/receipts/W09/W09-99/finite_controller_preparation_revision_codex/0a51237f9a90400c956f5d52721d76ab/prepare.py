"""Own receipt generation: bytes, JSON and AST only; no candidate imports or execution."""
import ast,datetime,difflib,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
O=N.parent/'b9b9b105f8e74cc4a7b39a0c059914b8'
R=ROOT/'execution/v2.4/receipts/W09/W09-99/finite_controller_v2_static_independent_review_codex/f4250aa50b74415a969b56fca0b177b4'
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,b):
 with (N/name).open('xb') as f:f.write(b)
 return ref(N/name)
def doc(name,d):return write(name,(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
old=json.loads((O/'spec.v2.sealed.json').read_bytes())
before=[ref(O/x) for x in ['spec.v2.sealed.json','manifest.complete.json','handoff.complete.json']]
before += [ref(Path(x['path'])) for x in old['controller_refs']]
review=json.loads((R/'review.json').read_bytes())
if ref(R/'review.json')['sha256']!='2834ddaa901327dd84d4329c46a6dc6d2fbbbf7763444ca59eb531a30442b6cc':raise RuntimeError('Review pin')
original=(O/'seal_readonly.v2.sealed.py').read_text(encoding='utf-8')
start=original.index('def check_vector(');end=original.index('def verify_runtime_pair(',start)
changed=original[:start]+(N/'prefix-check.fragment.txt').read_text(encoding='utf-8')+'\n\n'+original[end:]
needle=" root=no_alias(root);resultref=file_ref(root/'result.json')"
if changed.count(needle)!=1:raise RuntimeError('Exact sealer insertion boundary')
changed=changed.replace(needle," root=no_alias(root);prefix_audit=bind_all_prefixes(root,g,s);resultref=file_ref(root/'result.json')")
needle="'python_inventory':'ACTUAL_POINT_IN_TIME_ONLY'"
if changed.count(needle)!=1:raise RuntimeError('Summary exact insertion')
changed=changed.replace(needle,"'stage_prefix_audit':prefix_audit,"+needle)
module_refs=[];preserved=[]
for pin in old['controller_refs']:
 p=Path(pin['path']);b=p.read_bytes()
 if ref(p)!=pin:raise RuntimeError('Old module pin')
 if p.name=='seal_readonly.v2.sealed.py':b=changed.encode('utf-8')
 else:preserved.append({'original_ref':pin,'copy_name':p.name,'identical':True})
 ast.parse(b.decode('utf-8'),filename=p.name)
 module_refs.append(write(p.name,b))
oldrefs={x['path']:x for x in old['controller_refs']};newrefs={x['path']:module_refs[i] for i,x in enumerate(old['controller_refs'])}
def adapt(value):
 if isinstance(value,dict):
  if value.get('path') in newrefs and value==oldrefs[value['path']]:return newrefs[value['path']]
  return {k:adapt(v) for k,v in value.items()}
 if isinstance(value,list):return [adapt(v) for v in value]
 return value
spec=adapt(old)
spec['revision_scope']={'status':'PREPARATION_ONLY_NOT_EXECUTABLE','finding':'W09-CTRL06-VECTOR-PREFIX','old_spec_ref':ref(O/'spec.v2.sealed.json'),'independent_review_ref':ref(R/'review.json'),'changed_module_only':'seal_readonly.v2.sealed.py','unchanged_modules':6,'empty_add_advances_revision':True,'members':'exact path/hash/bytes with casefold collision rule','compile_complete_revision':21,'outer_worker_revision':1,'future_execution':'NOT_RUN','source_acceptance':False}
spec_ref=doc('spec.v3.proposed.json',spec)
write('sealer.unified.diff',''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),fromfile='old/seal_readonly.v2.sealed.py',tofile='new/seal_readonly.v2.sealed.py')).encode('utf-8'))
doc('future-json-controls.NOT_RUN.json',{'status':'NOT_RUN','controls':review['recommended_pure_json_controls_NOT_RUN'],'candidate_imports':0,'candidate_executions':0,'actual_PASS':None})
audit=doc('fix-mapping.audit.json',{'schema':'researchos.w09.sealer-prefix-revision-audit.v1','status':'PREPARATION_ONLY_PENDING_NONAUTHOR_REVIEW','review_ref':ref(R/'review.json'),'requirements':review['required_prefix_contract'],'implementation':['PrefixProof.add matches exact group/new pin delta/total/revision including empty adds','PrefixProof.vector binds every named stage to exact expected revision and members','Controller grammar fixed in bind_all_prefixes; compile revision21; optional junction and each eligible case add1','case allowed_module_files equals ordered full before prefix; worker and outer own exact add1 member sets','timestamp shape/order auxiliary; no lifecycle inference','Original remaining sealer predicates retained; old producer6 modules preserved byte-for-byte'],'preserved':preserved,'AST_modules':7,'AST_errors':0,'candidate_imports':0,'candidate_processes':0,'Go_SQL_HTTP_Model_Node_DLL':0,'cases':{'total':49,'new':41,'old':8,'status':'NOT_RUN'},'grant_authorized':False,'future_tuple_resources':None,'source_before':before,'source_after':[ref(Path(x['path'])) for x in before],'new_failures':[]})
if [ref(Path(x['path'])) for x in before]!=before:raise RuntimeError('Old input drift')
doc('handoff.json',{'schema':'researchos.w09.sealer-prefix-revision-handoff.v1','actor':'codex:/root/command_queue_impl','status':'PREPARATION_REPORTED_NOT_ACCEPTED','spec_ref':spec_ref,'audit_ref':audit,'selected_modules':module_refs,'old_handoff_ref':ref(O/'handoff.complete.json'),'old_manifest_ref':ref(O/'manifest.complete.json'),'independent_review_refs':[ref(R/x) for x in ['review.json','manifest.json','handoff.json']],'source_product_changes':0,'candidate_execution':False,'formal_increment':0,'requires':['Non-author new sealer review','Future real source/resource closure','Actual Root scope/grant and separate execution lease'],'new_failure_origins':[]})
entries=[ref(p) for p in sorted(N.iterdir()) if p.is_file()]
manifest=doc('manifest.json',{'count':len(entries),'entries':entries,'excluded_only':str(N/'manifest.json'),'original_files_mutated':False})
print(json.dumps({'handoff':ref(N/'handoff.json'),'manifest':manifest,'spec':spec_ref,'sealer':ref(N/'seal_readonly.v2.sealed.py')},ensure_ascii=False))
