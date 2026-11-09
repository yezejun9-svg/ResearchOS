from pathlib import Path
import ast,json,hashlib,os
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;P13=R/'execution/v2.4/receipts/W13/W13-03';N=P13/'desktop58_root_caller_new_allocation_preparation_codex/f6efabc714224607b566b29dbf2cb7cc'
C=[];REF={}
def ref(p):
 p=Path(p);b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};REF[str(p)]=r;return r
def ck(k,v):C.append({'check':k,'passed':bool(v)})
def verify(r):
 p=Path(r['path']);a=ref(p);ck('pin '+str(p),a['sha256']==r['sha256']and a['bytes']==r['bytes']);return p
def read(p):
 p=verify(p)if isinstance(p,dict)else Path(p);ref(p);return json.loads(p.read_bytes())
def save(n,d):
 with(O/n).open('xb')as f:f.write((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
h=read(N/'handoff.json');mf=read(N/'manifest.json');iv=read(h['inverse_ref']);allocation=read(h['allocation_ref']);canonical=read(h['canonical_before_ref']);read(h['static_audit_ref'])
ck('sourceMF exact count',mf['member_count']==len(mf['members'])==4 and mf['self_excluded']is True)
for r in mf['members']:p=verify(r);ck('MF own member '+p.name,p.parent==N and p.name!='manifest.json')
ck('MF whole inventory',{r['path']for r in mf['members']}=={str(p)for p in N.iterdir()if p.is_file()and p.name!='manifest.json'})
before=verify(h['old_source_ref']).read_bytes();after=verify(h['candidate_ref']).read_bytes();old=h['old_uid'];new=h['new_uid'];rebuilt=after.replace(new.encode(),old.encode())
ck('3 exact UUID substitutions',after.count(new.encode())==before.count(old.encode())==3 and new=='429e1734d9da4efba276680e78e2510b'and old=='dc00ad52f46c49acacc8058a58500820')
ck('wholebyte inverse',rebuilt==before);ck('AST inverse',ast.dump(ast.parse(rebuilt),include_attributes=False)==ast.dump(ast.parse(before),include_attributes=False));compile(after,h['candidate_ref']['path'],'exec');ck('static compilation only',True)
changed=[i+1 for i,(a,b)in enumerate(zip(before.splitlines(),after.splitlines()))if a!=b];ck('only lines11/13/14',changed==[11,13,14]and len(before.splitlines())==len(after.splitlines()))
source=after.decode();reg=Path(allocation['registration_namespace']);auth=Path(allocation['roots']['new_authorization_root'])
ck('actual allocation identity',allocation['schema']=='researchos.desktop58-root-allocation.v1'and allocation['owner']=='codex:/root'and allocation['run_uuid']==new and allocation['before']==[334,162,532])
ck('actual registration literal',"REGISTRATION = ROOT / '"+reg.relative_to(R).as_posix()+"'"in source)
ck('actual auth literal',"AUTH_ROOT = DESKTOP_RECEIPTS / '"+auth.relative_to(P13).as_posix()+"'"in source)
ck('actual UUID literal',"RUN_UUID = '"+new+"'"in source)
ck('future parameters remain unknown',all(h[k]is None for k in ['future_scope_sha','future_grant_sha','future_caller_output'])and all(x in source for x in ['OUT = None','SCOPE_SHA = None','GRANT_SHA = None']))
ck('allocation not execution/cut',allocation['after_failure_count']is None and allocation['execution_authorized']is False and allocation['native_target_calls']==allocation['canonical_writes']==allocation['execution_leaves_created']==allocation['formal_increment']==0)
ck('5 disjoint roots',len(allocation['roots'])==5 and len(set(allocation['roots'].values()))==5)
fresh=[]
for k,v in allocation['roots'].items():
 p=Path(v);fresh.append({'key':k,'path':v,'lexists':os.path.lexists(p)});ck('future root absent '+k,not os.path.lexists(p));ck('future root inside current workspace '+k,p.is_relative_to(R)and new in p.name)
ck('future scope absent',not os.path.lexists(reg/'scope_registration.json'))
ck('budget and qualification preserved','timeout=7800'in source and "'caller_OS_lifecycle_qualification': False"in source and "scope['inner_seconds'] == 7200"in source and "scope['outer_seconds'] == 7500"in source)
expected=['execution/v2.4/'+s+'.json'for s in ['checkpoint','path_ownership','step_state','commands']]
ck('4canonical ordered',[r['canonical_path']for r in canonical['entries']]==expected and canonical['tuple']==[334,162,532]);docs=[]
for row in canonical['entries']:
 p=verify(row['ref']);raw=p.read_bytes();actual=R/row['canonical_path'];ref(actual);ck('live canonical equals original copy '+row['canonical_path'],raw==actual.read_bytes());docs.append(json.loads(raw))
cp,ow=docs[:2];ck('actual334162532 E2',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[334,162,532]and cp['head']=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7')
head=(R/'.git/HEAD').read_text().strip();ref(R/'.git/HEAD')
if head.startswith('ref: '):p=R/'.git'/head[5:];head=p.read_text().strip();ref(p)
ck('direct actual Main head',head==cp['head'])
audit={'schema':'researchos.desktop58-root-caller-allocation-independent-audit.v1','checks':C,'failed_checks':[x for x in C if not x['passed']],'changed_lines':changed,'before_ref':h['old_source_ref'],'candidate_ref':h['candidate_ref'],'allocation_ref':h['allocation_ref'],'canonical_before_ref':h['canonical_before_ref'],'fresh_roots_point_in_time':fresh,'current_tuple':[334,162,532],'actual_Main_head':head,'input_refs':list(REF.values()),'actual_candidate_import_or_execution':False,'new_failure_origins':[]};save('audit.json',audit)
if audit['failed_checks']:print(json.dumps({'failed_checks':audit['failed_checks'],'audit_ref':ref(O/'audit.json')},ensure_ascii=False));raise SystemExit(0)
review={'schema':'researchos.desktop58-root-caller-allocation-independent-source-review.v1','reviewer':'codex:/root/w05_merge_review','non_author':True,'decision':'READY_SOURCE_PREPARATION_ONLY','requested_changes':[],'caller_sha256':h['candidate_ref']['sha256'],'candidate_ref':h['candidate_ref'],'original_source_ref':h['old_source_ref'],'source_handoff_ref':ref(N/'handoff.json'),'source_manifest_ref':ref(N/'manifest.json'),'inverse_ref':h['inverse_ref'],'allocation_ref':h['allocation_ref'],'canonical_before_ref':h['canonical_before_ref'],'audit_ref':ref(O/'audit.json'),'tool_observations_ref':ref(O/'tool-observations.json'),'checks_passed':len(C),'changed_source_lines':[11,13,14],'summary':'Exactly REGISTRATION/AUTH_ROOT/RUN_UUID substitutions to429 allocation. Complete byte/AST inverse matches originaldc00 caller. Other source bytes,7800 timeout,7200/7500 inner/outer limits,public environment,nullable exits/firstcause/secondary/raw retention and caller_OSfalse unchanged. Actual allocation and original4copies match live334/162/532; five execution leaves absent at read time.','future_scope_sha':None,'future_grant_sha':None,'future_caller_output':None,'required_future_inputs':['Actual newly reviewed bound Scope SHA','Actual sealed unique Grant SHA after Root registration','Root separately allocated fresh empty caller output and exact three-argument launch composition reviewed before once-only call'],'actual_candidate_imported':False,'actual_candidate_executed':False,'actual_CAS_calls':0,'actual_product_calls':0,'actual_execution_authorized':False,'source_acceptance':False,'formal_increment':0,'old_dc00_failed_input_unchanged':True,'counter_mutations':False,'new_failure_origins':[],'new_failed_tool_count':0,'status':'STOPPED'};save('review.json',review)
save('handoff.json',{'schema':'researchos.independent-source-review-handoff.v1','reviewer':'codex:/root/w05_merge_review','decision':review['decision'],'review_ref':ref(O/'review.json'),'audit_ref':ref(O/'audit.json'),'candidate_ref':h['candidate_ref'],'allocation_ref':h['allocation_ref'],'source_manifest_ref':ref(N/'manifest.json'),'checks_passed':len(C),'new_failure_origins':[],'new_failed_tool_count':0,'actual_execution_authorized':False,'status':'STOPPED'})
rows=[ref(p)for p in sorted(O.iterdir())if p.is_file()and p.name!='manifest.json'];save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':rows,'count':len(rows),'self_excluded':True})
print(json.dumps({'review':ref(O/'review.json'),'manifest':ref(O/'manifest.json'),'handoff':ref(O/'handoff.json'),'checks':len(C),'new_failures':0,'status':'STOPPED'},ensure_ascii=False))
