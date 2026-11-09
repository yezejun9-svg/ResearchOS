"""Continue only the pending control-link token, backup closure and guard tail."""
from pathlib import Path
import ast,hashlib,json,ntpath,re,struct,types,traceback
N=Path(__file__).resolve().parent;R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';C=B/'integration_codex/old21-caller-9c80f2c133f443bb8a2a629680cbba5d'
Q=B/'fresh_main23_programme_actual_independent_review_codex/actual-main23-20261010-01/review_checks.py'
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def save(name,v):
 p=N/name
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
q=types.ModuleType('pending_review_checks');exec(compile(Q.read_bytes(),str(Q),'exec'),q.__dict__)
checks=[]
def need(v,label):q.need(v,label);checks.append(label)
def mod(r,n):
 m=types.ModuleType(n);exec(compile(q.exact(r),r['path'],'exec'),m.__dict__);return m
def refs(x):
 if isinstance(x,dict):
  if set(x)==q.REF_KEYS:return [x]
  return [r for v in x.values() for r in refs(v)]
 if isinstance(x,list):return [r for v in x for r in refs(v)]
 return []
prefixref=pin(N/'facts-review-checks.json');need(prefixref['sha256']=='4c99c92dd7088a92c39ba66feee65dffad170d8a300d4241c1a9fb35d4056346','EXACT_SUCCESSFUL_PREFIX')
prefix=q.doc(prefixref);pg=q.doc(prefix['guard_ref']);q.clean_guard(pg)
need(prefix['error']['type']=='JSONDecodeError' and prefix['check_count']==31132 and prefix['held_ref_count']==19461,'EXACT_ORIGINAL_DIAGNOSTIC_AND_COMPLETED_PREFIX')
need(prefix['checks'][-1]=='EXACT_LINK_IMPORTCFG_control' and 'RECOMPUTED_ORIGINAL_RECURSIVE_GIT_TREE' in prefix['checks'] and 'EXACT_NINE_GO_PHASES' in prefix['checks'],'PREFIX_COMPLETED_BOUNDARY')
state=q.doc(pin(C/'builder-returned-state.root.json'));caller=q.doc(pin(C/'caller-return.root.json'));contract=q.doc(state['contract_ref'])
leaf=mod(contract['builder_ref'],'pending_old21_leaf');common=mod(contract['common_builder_ref'],'pending_old21_common');base=mod(contract['base_helper_ref'],'pending_old21_base');gm=mod(contract['source_guard_ref'],'pending_old21_guard')
request=q.doc(state['request_ref']);plan=leaf.compile_request(contract,request,base);paths=plan['paths'];manifest=q.doc(contract['input_manifest_ref'])
original=q.doc(state['source_before_ref'])['refs'];frozen=q.doc(state['frozen_before_ref'])['refs'];allowed=frozen+[i['ref'] for i in manifest['items'] if i['kind']=='toolchain']
streams={c['phase']:(q.exact(c['stdout_ref']),q.exact(c['stderr_ref'])) for c in state['calls']}
sums={tuple(l.split()[:2]):l.split()[2] for l in (Path(paths['frozen_main'])/'go.sum').read_text().splitlines()}
expectedguards={'original_inputs':original,'frozen_inputs':frozen}
for c in state['calls']:expectedguards['raw_'+c['phase']]=[c['stdout_ref'],c['stderr_ref']]
control=state['target_results']['control'];cp=q.doc(control['declared_closure_ref'])['packages'];ce=q.doc(control['export_closure_ref'])['exports']
expectedguards['exports_control']=[x['ref'] for x in ce];expectedguards['program_control']=[control['program_ref']]
targetfacts={'control':dict(program_ref=control['program_ref'],packages=len(cp),modules=len({x['module']['Path'] for x in cp if x['module']['Path'] and not x['module']['Main']}),exports=len(ce),cache_before=len(q.doc(control['cache_before_build_ref'])['refs']),cache_after=len(q.doc(control['cache_after_build_ref'])['refs']),retained_work=2,binary_metadata_ref=control['binary_metadata_ref'])}
metadata=[pin(__file__),pin(N/'review_facts.py'),prefixref,prefix['guard_ref'],pin(Q),pin(C/'builder-returned-state.root.json'),pin(C/'caller-return.root.json'),state['contract_ref']]+refs(state)+[contract[k] for k in ['builder_ref','common_builder_ref','base_helper_ref','source_guard_ref','input_manifest_ref']]
backup=state['target_results']['backup'];metadata+=q.doc(backup['build_work_ref'])['refs']
metadata+=[x['ref'] for x in q.doc(backup['export_closure_ref'])['exports']]
sumref=next(x for x in frozen if q.canonical(x['path'])==q.canonical(ntpath.join(paths['frozen_main'],'go.sum')));metadata.append(sumref)
live={q.canonical(str(R/'execution/v2.4'/n)) for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']};allrefs={q.canonical(r['path']):r for r in metadata if q.canonical(r['path']) not in live}
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=768*1024*1024);error=None;stages=[];result={}
try:
 guard.acquire(list(allrefs.values()))
 trace=streams['control-build'][1].decode();linkline=next(x for x in trace.splitlines() if x.startswith("GOROOT='' ") and 'link.exe' in x)
 quoted=re.match(r"GOROOT='' (\"(?:\\.|[^\"])*\")",linkline).group(1);linker=json.loads(quoted)
 need(q.canonical(linker)==q.canonical(ntpath.join(contract['goroot'],'pkg/tool/windows_amd64/link.exe')),'CONTROL_ACTUAL_LINK_COMMAND_OFFICIAL_TOKEN')
 need(q.canonical(linker) in {q.canonical(x['path']) for x in pg['entries']},'OFFICIAL_LINKER_HELD_IN_PASSED_FULL_PREFIX')
 tree=ast.parse((N/'review_facts.py').read_bytes());block=next(x for x in tree.body if isinstance(x,ast.Try))
 loopindex=next(i for i,x in enumerate(block.body) if isinstance(x,ast.For) and isinstance(x.target,ast.Tuple) and [y.id for y in x.target.elts]==['target','tr'])
 loop=block.body[loopindex]
 loop.iter=ast.parse("{'backup':state['target_results']['backup']}.items()",mode='eval').body
 pos=next(i for i,x in enumerate(loop.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='quoted' for t in x.targets))
 loop.body[pos:pos+1]=ast.parse('linkline=next(x for x in trace.splitlines() if x.startswith("GOROOT=\'\' ") and "link.exe" in x)\nquoted=[json.loads(re.match(r"GOROOT=\'\' (\\\"(?:\\\\.|[^\\\"])*\\\")",linkline).group(1))]').body
 tail=ast.Module(body=[loop]+block.body[loopindex+1:],type_ignores=[]);ast.fix_missing_locations(tail)
 exec(compile(tail,str(N/'review_facts.py'),'exec'),globals())
 need(set(result['targets'])=={'control','backup'},'BOTH_TARGETS_COMPLETE_USING_PASSED_PREFIX_AND_PENDING_TAIL')
except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
finally:closed=guard.close()
gr=save('facts-tail-Source-guard.closed.json',closed);q.clean_guard(closed)
out=save('facts-tail-review-checks.json',dict(status='FACTUAL_REVIEW_COMPLETED' if error is None else 'REVIEW_DIAGNOSTIC_FAILURE',prefix_ref=prefixref,prefix_guard_ref=prefix['guard_ref'],preserved_successful_prefix_checks=prefix['check_count'],full_source_prefix_rerun=False,error=error,checks=checks,check_count=len(checks),result=result,stage_refs=stages,guard_ref=gr,held_ref_count=len(allrefs),formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(report_ref=out,guard_ref=gr,checks=len(checks),held_refs=len(allrefs),error=error),ensure_ascii=False),flush=True);print('PYTHON_EXIT_CODE='+str(1 if error else 0),flush=True)
raise SystemExit(1 if error else 0)
