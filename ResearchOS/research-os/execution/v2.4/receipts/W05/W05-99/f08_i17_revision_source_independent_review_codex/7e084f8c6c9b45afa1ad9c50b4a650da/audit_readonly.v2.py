import base64, copy, difflib, hashlib, json, pathlib, re, sys, traceback
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
R=ROOT/'execution/v2.4/receipts/W05/W05-99'
P=R/'f08_i17_binding_revision_preparation_codex/66ec5753ea3249d0940b157e51a87968'
OLD=R/'f08_i17_binding_revision_preparation_codex/b918c16361bb4744bc7fffb6434d6849'
SRC=R/'f08_i17_binding_source_mapping_codex/83077264f7f748daa7c9452e22c5c2d0/source-snapshots'
OUT=pathlib.Path(__file__).parent
reads={}; checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=pathlib.Path(p);b=p.read_bytes();reads[str(p.as_posix())]={'path':p.as_posix(),'sha256':sha(b),'bytes':len(b)};return b
def doc(p):return json.loads(read(p))
def check(ok,name):checks.append({'check':name,'passed':bool(ok)})
def verify(ref):
 b=read(ref['path']);check(sha(b)==ref['sha256'] and len(b)==ref['bytes'],'pin:'+ref['path']);return b
def save(n,d):
 with (OUT/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def vector_raw_elements(b):
 s=b.decode();m=re.search(r'"vectors"\s*:\s*\[',s);pos=m.end();out=[];dec=json.JSONDecoder()
 while True:
  while s[pos].isspace() or s[pos]==',':pos+=1
  if s[pos]==']':return out
  _,end=dec.raw_decode(s,pos);out.append(s[pos:end].encode());pos=end
def refs(x):
 if isinstance(x,dict):
  if {'path','sha256','bytes'}<=x.keys():yield x
  for v in x.values():yield from refs(v)
 elif isinstance(x,list):
  for v in x:yield from refs(v)
def apply_patch_data(b,patch):
 lines=b.splitlines(keepends=True);p=patch.splitlines(keepends=True);out=[];cursor=0;i=2
 while i<len(p):
  m=re.match(rb'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',p[i])
  if not m:raise ValueError('invalid data diff header')
  start=int(m[1]);count=int(m[2] or b'1');idx=start-1 if count else start
  out.extend(lines[cursor:idx]);cursor=idx;i+=1
  while i<len(p) and not p[i].startswith(b'@@'):
   tag=p[i][:1];data=p[i][1:]
   if i+1<len(p) and p[i+1]==b'\\ No newline at end of file\n':
    data=data[:-1];i+=1
   if tag in (b' ',b'-'):
    if lines[cursor]!=data:raise ValueError('data patch source mismatch')
    cursor+=1
   if tag in (b' ',b'+'):out.append(data)
   i+=1
 out.extend(lines[cursor:]);return b''.join(out)
def main():
 hand=read(P/'handoff.json');check(sha(hand)=='d839367c136c37fba64b60186f45bf597c85a83007b68cb702ab044b5e818083','handoff authority')
 mf=doc(P/'manifest.json');check(reads[str((P/'manifest.json').as_posix())]['sha256']=='d2a97d049bdd1523b1abd231283435c06d7cd9989cd250540a955805e07b5ad0','manifest authority')
 check(len(mf['members'])==81 and sum(x['bytes'] for x in mf['members'])==5004113,'81 members total bytes')
 for r in mf['members']:verify(r)
 actual={f.as_posix() for f in P.rglob('*') if f.is_file() and f!=P/'manifest.json'}
 check(actual=={x['path'] for x in mf['members']},'exact manifest membership')
 prior=R/'f08_i17_binding_revision_independent_source_review_codex/f55ac9fdfb3d4a929686b6884431f962'
 for n in ['source-review.json','REVIEW.md','minimum-source-fact-plan.json']:read(prior/n)
 a=doc(P/'static-byte-audit.json');v5=read(P/'client_cancel_finalization_test.v5.go.proposed.txt');v4=read(OLD/'client_cancel_finalization_test.v4.go.proposed.txt');v3=read(SRC/'02-client_cancel_finalization_test.v3.go.proposed.txt')
 check(v5==v4.replace(b'\r\n',b'\n') and b'\r\n' not in v5,'R01 exact LF-only wholefile correction')
 rows=a['R01']['raw_body_records'];check(len(rows)==28,'28 original tests')
 for x in rows:
  old=v3[x['before_start_byte']:x['before_start_byte']+x['bytes']];new=v5[x['after_start_byte']:x['after_start_byte']+x['bytes']]
  check(old==new and sha(old)==x['sha256_before']==x['sha256_after'] and old.startswith(('func '+x['name']+'(').encode()),'raw body exact:'+x['name'])
 for c in doc(P/'changes.json'):
  before=verify(c['before']);after=verify(c['after']);f=verify(c['forward']);i=verify(c['inverse'])
  check(apply_patch_data(before,f)==after and apply_patch_data(after,i)==before,'whole byte forward/inverse:'+c['name'])
 oldraw=read(OLD/'vector-manifest.json');newraw=read(P/'vector-manifest.json');ov=json.loads(oldraw);nv=json.loads(newraw)
 check(len(ov['vectors'])==109 and len(nv['vectors'])==114,'109 plus 5')
 check(ov['vectors']==nv['vectors'][:109],'parsed original vector prefix')
 check(vector_raw_elements(oldraw)==vector_raw_elements(newraw)[:109],'raw original vector element prefix')
 blobrefs=[]
 for v in nv['vectors']:
  for kind in ['valid','corrupt']:
   for arg in v[kind]:
    if arg['kind']=='BLOB':verify(arg['ref']);blobrefs.append(arg['ref'])
 check(len(blobrefs)==257,'actual BLOB argument occurrences257')
 framepaths={x['path'] for x in blobrefs if '.go-producer-frame.json' in x['path']};check(len(framepaths)==100,'100 original producer frames rehashed')
 source=read(SRC/'01-client_cancel_finalization.v3.go.proposed.txt').decode();rules={}
 for cat,mask,uk in re.findall(r'"([a-z_]+)":\s*\{mask:"([sihSIH]+)",\s*unique:\[\]\[\]int\{(.*?)\}\}',source):
  rules[cat]=(mask,[list(map(int,k.split(','))) for k in re.findall(r'\{([0-9,]+)\}',uk)])
 check(len(rules)==34,'34 actual source masks')
 cases=doc(P/'source-fact-cases.json')['cases'];check(len(cases)==5,'five source fact cases')
 pairreports=[]
 for c in cases:
  good=verify(c['baseline_ref']);bad=verify(c['bad_ref']);g=json.loads(good);b=json.loads(bad);m=c['mutation'];changed=copy.deepcopy(g);path=m['path'].strip('/').split('/');dest=changed
  for bit in path[:-1]:dest=dest[int(bit)] if isinstance(dest,list) else dest[bit]
  last=int(path[-1]) if isinstance(dest,list) else path[-1]
  if m['operation']=='remove_one_tuple':del dest[last]
  elif m['operation']=='replace_one_header_scalar':
   oh=json.loads(bytes.fromhex(g['row'][7]));nh=json.loads(bytes.fromhex(b['row'][7]));oe=json.loads(base64.b64decode(oh['raw_envelope_base64'],validate=True));ne=json.loads(base64.b64decode(nh['raw_envelope_base64'],validate=True));expected=copy.deepcopy(oe);expected['expected_revision']=8
   check(ne==expected and oe['expected_revision']==7,'only legal envelope revision7to8');h=copy.deepcopy(oh);h['raw_envelope_base64']=nh['raw_envelope_base64'];check(h==nh,'only base64 payload changed');dest[last]=b['row'][7]
  else:dest[last]=m['after']
  check(changed==b,'single fact exact:'+c['id']);check(set(g)==set(b)=={'action','old','row','sources'} and g['action']==b['action']==c['action_before']==c['action_after'],'legal unchanged action:'+c['id'])
  for label,frame in [('good',g),('bad',b)]:
   seen=set();shape=True
   tuples=frame['sources']+[['commits' if frame['action']=='commit.insert' else 'idempotency',frame['row']]]
   for n,(cat,row) in enumerate(tuples):
    mask,keys=rules[cat];shape &= len(row)==len(mask)
    for k,val in zip(mask,row):
     if val is None and k.isupper():continue
     if k.lower()=='s':shape &= isinstance(val,str)
     elif k.lower()=='i':shape &= type(val) is int and -(2**63)<=val<2**63
     else:shape &= isinstance(val,str) and len(val)%2==0 and bool(re.fullmatch('[0-9A-F]*',val))
    if n<len(frame['sources']):
     for index,key in enumerate(keys):
      vals=[row[z] for z in key]
      if None in vals:continue
      encoded=(cat,index,json.dumps(vals,ensure_ascii=False));shape &= encoded not in seen;seen.add(encoded)
   check(shape,'source34 mask/key static shape:'+c['id']+':'+label)
  v=nv['vectors'][-5+cases.index(c)];check(v['valid'][0]==v['corrupt'][0]=={'kind':'INTEGER','integer':5} and v['fixed_callback_error']=='F08_ORIGINAL_BINDING' and v['expected_sqlite_primary_code']==1,'mode5/error inference:'+c['id'])
  pairreports.append({'id':c['id'],'predicate':c['source_branch'],'qualification':'SOURCE_INFERENCE_NOT_RUN','actual_callback':None,'actual_SQL':None})
 before=read(P/'inputs.before.json');after=read(P/'inputs.after.json');check(before==after and len(json.loads(before))==928,'author928 snapshots exact identical; no full source rescan claimed')
 origins=[]
 for n in ['origin.rg-absent-specs.json','origin.metadata-membership.json','origin.metadata-vector-newline.json','origin.metadata-BLOB-occurrence-count.json']:
  o=doc(P/n);origins.append({'ref':reads[(P/n).as_posix()],'outer_exit':o['outer_exit'],'actual_native_exit':o['actual_native_exit'],'chunk_id':o['chunk_id']})
 check([x['actual_native_exit'] for x in origins]==[None,1,1,1],'four origins preserve nullable native')
 save('checks.json',{'checks':checks,'failed':[x for x in checks if not x['passed']],'source_fact_pairs':pairreports,'original_origins':origins,'target_executions':0,'scope':'static data audit; not evaluator or SQL execution'})
 save('inputs.before.json',list(reads.values()));drift=[]
 for r in list(reads.values()):
  b=pathlib.Path(r['path']).read_bytes()
  if len(b)!=r['bytes'] or sha(b)!=r['sha256']:drift.append(r['path'])
 save('inputs.after.json',{'checked':len(reads),'drift':drift})
 print(json.dumps({'checks':len(checks),'failed':len([x for x in checks if not x['passed']]),'inputs':len(reads),'drift':drift,'target_executions':0}))
 return 0 if all(x['passed'] for x in checks) and not drift else 2
if __name__=='__main__':
 try:code=main()
 except BaseException as e:
  save('audit.v2.error.json',{'error':repr(e),'traceback':traceback.format_exc(),'actual_native_exit':None,'target_executions':0});raise
 sys.exit(code)
