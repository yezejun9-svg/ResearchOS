import datetime,hashlib,json,pathlib,sys
root=pathlib.Path('D:/作品集/ResearchOS/research-os')
base=pathlib.Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':p.relative_to(root).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def write(name,obj):
 p=base/name
 with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(p)
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
errors=[]; corrections=[]; checked=[]
for name in ['source_review.json','handoff.json','manifest.json']:
 def walk(x,ptr=''):
  if isinstance(x,dict):
   if 'path' in x and 'sha256' in x:
    p=root/x['path']; checked.append({'document':name,'pointer':ptr,'path':x['path']})
    if not p.is_file() or sha(p.read_bytes())!=x['sha256']:errors.append(checked[-1])
    if p.is_file() and 'lines' in x.get('locator',{}):
     n=len(p.read_text(encoding='utf8').splitlines());a,z=x['locator']['lines']
     if a<1 or z>n or a>z:
      corrections.append({'document_ref':ref(base/name),'json_pointer':ptr+'/locator/lines','original':[a,z],'corrected':[max(a,1),min(z,n)],'reason':'Line range ended after EOF; same immutable complete-source snapshot, no evidence bytes or finding changed.'})
   for k,v in x.items():walk(v,ptr+'/'+k)
  elif isinstance(x,list):
   for i,v in enumerate(x):walk(v,ptr+'/'+str(i))
 walk(json.loads((base/name).read_text(encoding='utf8')))
assert not errors
correction_ref=write('locator_corrections.json',{'schema':'researchos.evidence-locator-addendum.v1','original_review_ref':ref(base/'source_review.json'),'status':'LOCATOR_BOUNDS_CORRECTED_WITHOUT_REWRITING_ORIGINAL','corrections':corrections,'finding_or_acceptance_changes':False})
validation=write('final_audit.json',{'schema':'researchos.readonly-receipt-audit.v1','status':'RECEIPT_INTEGRITY_PASS_ONLY','actualargv':[sys.executable,*sys.orig_argv[1:]],'cwd':str(pathlib.Path.cwd()),'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checked_ref_count':len(checked),'hash_errors':errors,'locator_corrections_ref':correction_ref,'prior_original_collector_tool_result':{'tool_chunk_id':'88cec9','actual_exit':0,'raw_output_location':'conversation tool result; not reconstructed as fake shell stdout'},'prior_readonly_ref_audit_tool_result':{'tool_chunk_id':'870419','actual_exit':0,'hash_ref_count':153,'locator_ends_after_EOF':8},'new_product_test_calls':0,'new_product_failures':0,'formal_increment':0})
files=[ref(p) for p in sorted(base.rglob('*')) if p.is_file()]
manifest=write('manifest.final.json',{'schema':'researchos.receipt-manifest.v1','namespace':base.relative_to(root).as_posix(),'files':files,'excludes_self':True,'prior_manifest_preserved':ref(base/'manifest.json')})
print(json.dumps({'final_audit':validation,'locator_corrections':correction_ref,'final_manifest':manifest},ensure_ascii=False))
