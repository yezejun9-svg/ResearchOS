from pathlib import Path
import ast,json,hashlib,os
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
S=R/'execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_allocationsixth_source_preparation_codex/b4d53db07f1e4ab8b9c0b37e291a6da5'
C=[]
def ck(n,v):C.append({'check':n,'passed':bool(v)})
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def pin(p):
 p=path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(r):
 b=path(r['path']).read_bytes();ck('pin '+r['path'],len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']);return b
def obj(p):return json.loads(path(p).read_bytes())
def save(n,d):
 p=O/n
 with p.open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
h=obj(S/'handoff.json');m=obj(S/'manifest.json');a=obj(S/'audit.json')
ck('manifest given pin',pin(S/'manifest.json')['sha256']=='d9d404835c70b29a65adb512cd2277014572108912cfe2e7d49753c56d56c7b8')
ck('MF3selfexcluded',len(m['members'])==3 and m['self_excluded'] is True)
for r in m['members']:verify(r)
old=verify(a['seed_ref']);new=verify(h['source_ref']);oldtext=old.decode();text=new.decode()
oldid='dc4fe023ed714e74b8d3692b504cf55d';uid='b4d53db07f1e4ab8b9c0b37e291a6da5';oldout='baaf93516e9d42e2b583972e5a30df91';outid='d8a016ddc71e440fb386a11957c098ea'
ck('threeUIDoccurrences',oldtext.count(oldid)==text.count(uid)==3)
ck('REGoneordinal',text.count('desktop58-finite169-go3-r337-')==1 and oldtext.count('desktop58-finite169-go3-r336-')==1)
ck('OUTone',text.count(outid)==oldtext.count(oldout)==1)
back=text.replace(uid,oldid).replace('desktop58-finite169-go3-r337-','desktop58-finite169-go3-r336-').replace(outid,oldout)
ck('wholebyteinverse',back.encode()==old)
ot,nt=ast.parse(old),ast.parse(new);compile(new,'static only','exec')
defs=lambda t:{x.name:ast.dump(x,include_attributes=False) for x in t.body if isinstance(x,ast.FunctionDef)}
ck('threefunctionsASTexact',defs(ot)==defs(nt) and set(defs(nt))=={'need','pin','save'})
anchor="scope_path = REGISTRATION / 'scope_registration.json' "
ck('scopeReadEOFexact',text[text.index(anchor):]==oldtext[oldtext.index(anchor):])
ck('oldreviewedsource6332',a['seed_ref']['sha256']=='6332aeab65da7a8893299ae93f54831eda0fba4da50dc215d07070f4839e24d8')
ck('exactREGliteral',"REGISTRATION = ROOT / '"+a['registry_rel']+"'" in text)
ck('exactAUTHliteral',"AUTH_ROOT = DESKTOP_RECEIPTS / 'desktop58_finite_authorization_codex/"+uid+"'" in text)
ck('exactUID',"RUN_UUID = '"+uid+"'" in text)
ck('exactOUT',"need(OUT == DESKTOP_RECEIPTS / 'desktop58_root_terminal_closure_codex/"+outid+"', 'Fixed Root allocated caller output')" in text)
ck('3arguments',"need(len(sys.argv) == 4" in text and "SCOPE_SHA, GRANT_SHA = sys.argv[1:3]" in text)
ck('explicitSHAvalidation',"len(value) == 64 and all(c in '0123456789abcdef' for c in value)" in text)
ck('unboundSHA',"SCOPE_SHA = None" in text and "GRANT_SHA = None" in text and h['future_scope_and_grant_sha256'] is None)
ck('freshsourceNoAuthority',h['execution_authorized'] is False and h['before_registration_actual'] is None and h['after_registration_actual'] is None)
ck('strictoutempty',"OUT.is_dir() and not any(OUT.iterdir())" in text and "'Canonical caller output'" in text and "'Caller output must be separate from Root execution and preparation leaves'" in text)
ck('oneSubprocessNoRetry',text.count('subprocess.run(')==1 and "'automatic_retry': False" in text)
ck('publicenvNokey',"{'SystemRoot', 'WINDIR', 'ComSpec', 'PATH', 'PATHEXT'}" in text)
ck('isolatedpinnedPY',"argv = [PYTHON, '-I', '-S', '-X', 'utf8', launcher['path']" in text)
ck('timeout7800',"timeout=7800" in text)
for token in ("scope['inner_seconds'] == 7200","scope['outer_seconds'] == 7500","scope['cleanup_seconds'] == 5","scope['controller_evidence_reserve_seconds'] == 60","scope['launcher_evidence_reserve_seconds'] == 60"):ck('strict '+token,token in text)
ck('NULLexitpreserved',"result.returncode if result else None" in text and "'actual_outer_tool_exit': None" in text)
ck('firstcauseSecondaryPreserved',"error = {'error': repr(exc), 'traceback': traceback.format_exc()}" in text and "'secondary': secondary" in text and "'invocation-receipt'" in text)
ck('OSfalse',text.count("'caller_OS_lifecycle_qualification': False")==2)
ck('streamxb',"'root-launch.stdout.raw').open('xb')" in text and "'root-launch.stderr.raw').open('xb')" in text)
p13=R/'execution/v2.4/receipts/W13/W13-03'
roots=[p13/(family+'/'+uid) for family in ('desktop58_finite_executor_codex','desktop58_finite_launcher_codex','desktop58_finite_authorization_codex','desktop58_finite_grant_preflight_codex')]+[R/('.local/desktop58-export-'+uid),path(a['caller_out_rel'])]
for p in roots:ck('freshabsent '+str(p),not os.path.lexists(p))
ck('all6nonoverlap',len(set(roots))==6 and all(not x.is_relative_to(y) for x in roots for y in roots if x!=y))
au=save('audit.json',{'schema':'researchos.readonly-source-audit.v1','checks':C,'passed':sum(x['passed'] for x in C),'total':len(C),'candidate_execution':False,'new_failure_origins':[]})
failed=[x for x in C if not x['passed']]
review={'schema':'researchos.desktop58-root-caller-independent-source-review.v1','reviewer':'codex:/root/w05_merge_review','source_author':'codex:/root','non_author':True,'decision':'READY_SOURCE_PREPARATION_ONLY' if not failed else 'REQUEST_CHANGES','requested_changes':failed,'source_ref':h['source_ref'],'caller_sha256':h['source_ref']['sha256'],'seed_ref':a['seed_ref'],'author_manifest_ref':pin(S/'manifest.json'),'author_handoff_ref':pin(S/'handoff.json'),'audit_ref':au,'actual_integration_executed':False,'candidate_imported':False,'candidate_executed':False,'actual_launch_authorized':False,'source_acceptance':False,'formal_increment':0,'caller_OS_lifecycle_qualification':False,'new_failure_origins':[],'new_failure_count':0,'open_conditions':['Old72ff registered lease must be closed through separately reviewed actual CAS; execution termination evidence alone cannot satisfy metadata_pipeline active-lease guard.','New actual allocation/literal/bound scope independent review and full runtime resource capture remain required.','Future new registration CAS/seal/unique grant and actual scope/grant SHA arguments remain required.','Root must separately allocate exactly d8a016 output as a fresh empty canonical directory; preflight failures before caller try are tool-stderr evidence, not guaranteed caller receipts.','No fifth dc4f prepare or old native retry authorized.'],'status':'STOPPED'}
rr=save('review.json',review)
report=save('report.json',{'decision':review['decision'],'wholebyteinverse':not failed,'changes':'Three UID occurrences, REG ordinal336->337 and one fixed caller-output UUID; all helpers and scope-read-to-EOF preserved.','checks_passed':sum(x['passed'] for x in C),'checks_total':len(C),'future_gates':review['open_conditions'],'new_failure_count':0})
hd=save('handoff.json',{'schema':'researchos.independent-source-review-handoff.v1','review_ref':rr,'report_ref':report,'audit_ref':au,'decision':review['decision'],'new_failure_count':0,'new_failure_origins':[],'status':'STOPPED'})
es=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mf=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':es,'count':len(es),'self_excluded':True,'mutable_after_seal':False})
print(json.dumps({'review':rr,'handoff':hd,'manifest':mf,'checks':len(C),'failed':failed},ensure_ascii=False))

