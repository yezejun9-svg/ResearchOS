from pathlib import Path
import json,hashlib,datetime,concurrent.futures,sys,traceback
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent; B=R/'execution/v2.4/receipts/W05/W05-99'; A=B/'integration_codex/provider-g1-readonly-adjudication-r301'; O=B/'provider_whole9_g1_root_executor_codex/788ce69c409b472799ee1389b778f9da'; REG=B/'integration_codex/handler-and-g1-originals-r301'
def sha(x):return hashlib.sha256(x).hexdigest()
def put(p,x):
 with (N/p).open('x',encoding='utf-8') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def facts(p):
 h=hashlib.sha256();count=0
 with p.open('rb') as f:
  while chunk:=f.read(4*1024*1024):h.update(chunk);count+=len(chunk)
 return {'sha256':h.hexdigest(),'bytes':count}
def canon():
 return [{'path':str(R/p),**facts(R/p)} for p in ['execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json']]
try:
 put('canonical.before.json',canon());refs=[]
 source=[*A.iterdir(),*O.iterdir(),REG/'g1.originals.audit.json',REG/'provider_g1_readonly_adjudication_scope.json',R/'execution/toolchains/locked.json']
 audit=json.loads((REG/'g1.originals.audit.json').read_text(encoding='utf-8-sig'))
 source += [R/x['path'] for x in audit['outer_original_refs']]
 for p in dict.fromkeys(source):
  if not p.is_file():continue
  raw=p.read_bytes();dest=N/'snapshots'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);refs.append({'path':str(p),**{'sha256':sha(raw),'bytes':len(raw)},'snapshot':dest.relative_to(N).as_posix()})
 put('receipt.inputs.before.json',refs)
 expected={'adjudicate.py':'0a3a440d3c82f75d3495e7b6e72b0e21d5ac76a9aab1d7281e15927774d59347','result.json':'52ac2375e105d1285601270d66bf004053f79e22dfe33bb9896d9ea566e97e2d'}
 for p,h in expected.items():
  if sha((A/p).read_bytes())!=h:raise RuntimeError('ROOT_AUTHORITY_HASH_DRIFT '+p)
 original=json.loads((O/'compiled-dependencies.before.json').read_text(encoding='utf-8-sig'))
 vectors={p:json.loads((O/p).read_text(encoding='utf-8-sig')) for p in ['inputs.pre-case.json','inputs.failure.current.json']};vectors['RootCurrent']=json.loads((A/'inputs.current.verified.json').read_text(encoding='utf-8-sig'))
 if len(original)!=48392 or any(v!=original for v in vectors.values()):raise RuntimeError('ORIGINAL_OR_ROOT_VECTOR_MISMATCH')
 lock=json.loads((R/'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'))['tools'];allowed=[R.resolve()]+[Path(lock[k]['path']).resolve().parent for k in ['node','python','git']]+[Path(lock['go']['path']).resolve().parent.parent]
 def one(item):
  name,exp=item;p=Path(name).resolve()
  if not (any(p.is_relative_to(x) for x in allowed) or str(p).lower()=='c:\\windows\\system32\\taskkill.exe'):raise RuntimeError('UNEXPECTED_INPUT_ROOT '+name)
  if any(p.is_relative_to((R/x).resolve()) for x in ['.local/resources','vault','.vault']):raise RuntimeError('PRIVATE_INPUT_REFUSED '+name)
  a=facts(p);return name,a,a==exp
 fresh={};mismatches=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
  for i,(name,a,eq) in enumerate(ex.map(one,original.items()),1):
   fresh[name]=a
   if not eq:mismatches.append({'path':name,'expected':original[name],'actual':a})
   if i%5000==0:print(json.dumps({'hashed':i,'total':len(original),'mismatches':len(mismatches)}),flush=True)
 put('compiled-inputs.fresh.json',fresh);put('compiled-inputs.comparison.json',{'count':len(fresh),'old_vectors_and_root_current_equal':True,'mismatches':mismatches,'canonical_paths_present':[x for x in original if x.lower().endswith(('checkpoint.json','path_ownership.json'))]})
 artifacts=json.loads((O/'artifacts.before-case.json').read_text(encoding='utf-8-sig'));checked=[]
 for p,e in artifacts.items():
  if Path(p).name in ['domain.g1.test.exe','mu-worker.mjs','mu-worker.mjs.build.json','_testmain.go']:
   a=facts(Path(p));checked.append({'path':p,'expected':e,'actual':a,'match':a==e})
   if Path(p).name=='_testmain.go':(N/'retained_testmain.go.txt').write_bytes(Path(p).read_bytes())
 put('retained-artifacts.fresh.json',checked)
 after=[{'path':x['path'],**facts(Path(x['path'])),'same':facts(Path(x['path']))=={'sha256':x['sha256'],'bytes':x['bytes']}} for x in refs];put('receipt.inputs.after.json',after);put('canonical.after.json',canon())
 put('hash-result.json',{'status':'HASH_REVIEW_COMPLETE','inputs':len(fresh),'receipt_count':len(refs),'mismatches':len(mismatches),'artifacts':len(checked),'artifacts_match':all(x['match'] for x in checked),'receipt_drift':sum(not x['same'] for x in after),'product_executions':0,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 print(json.dumps({'namespace':str(N),'inputs':len(fresh),'mismatches':mismatches,'artifacts':checked},ensure_ascii=True),flush=True)
except BaseException as e:
 put('failure.origin.json',{'phase':'READONLY_HASH_REVIEW','error':repr(e),'traceback':traceback.format_exc(),'actual_outer_exit':None,'note':'Actual process exit is not known inside error capture; caller records it separately.','retry':False});raise
