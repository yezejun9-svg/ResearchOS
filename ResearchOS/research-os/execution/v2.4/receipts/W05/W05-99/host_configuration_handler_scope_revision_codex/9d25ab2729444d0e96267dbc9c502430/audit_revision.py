import pathlib,json,hashlib,datetime,sys
R=pathlib.Path('D:/作品集/ResearchOS/research-os'); O=pathlib.Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def put(n,v):
 p=O/n
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(p)
refs=0;locators=0
def walk(x):
 global refs,locators
 if isinstance(x,dict):
  if set(('path','sha256','bytes')).issubset(x):
   p=R/x['path'];b=p.read_bytes();assert sha(b)==x['sha256'] and len(b)==x['bytes'],x['path'];refs+=1
   if 'locator' in x:
    a,z=x['locator']['lines'];assert 0<a<=z<=len(b.decode('utf8').splitlines());locators+=1
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
for name in ['manifest.json','scope_proposal.json','case_matrix30.json','potential_test_impacts.json','handoff.json']:walk(json.loads((O/name).read_bytes()))
p=json.loads((O/'scope_proposal.json').read_bytes());assert p['exact_source_count']==len(p['exact_scope'])==27
assert len({s['path'] for s in p['exact_scope']})==27
for s in p['exact_scope']:
 assert (R/s['path']).exists()!=s['expected_absent'],s['path']
assert len(json.loads((O/'case_matrix30.json').read_bytes())['cases'])==30
after=json.loads((O/'input.after.json').read_bytes());assert all(x['same'] for x in after['entries'])
assert (O/'raw/protected-wt-before.stdout').read_bytes()==(O/'raw/protected-wt-after.stdout').read_bytes()==b''
a=put('audit.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'DESIGN_RECEIPT_INTEGRITY_ONLY','actualargv':[sys.executable,*sys.orig_argv[1:]],'verified_refs':refs,'verified_line_locators':locators,'exact_paths':27,'primary_case_groups':30,'captured_public_inputs':len(after['entries']),'source_input_drift':0,'protected_configuration_WT_tracked_clean':True,'product_tests':0,'source_mutations':0,'formal_increment':0})
m=put('manifest.final.json',{'schema':'researchos.receipt-manifest.v1','files':[ref(f) for f in sorted(O.rglob('*')) if f.is_file()],'excludes_self':True})
print(json.dumps({'audit':a,'final_manifest':m},ensure_ascii=False))
