import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,ast,importlib.util
P=pathlib.Path
O=P(__file__).resolve().parent;R=P('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
S=B/'integration_codex/attach-fixture-two-parent-sparse-root-source-1791516205000/revision-exact-paths'
A=B/'integration_codex/attach-fixture-current-two-parent-root-source-t11-1a11e7f5205729390aaee9f47b28ce6'
V=B/'attach_fixture_two_parent_caller_independent_review_codex/t11r-20261009-source-review'
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
D=P('C:/Program Files/Git/mingw64/share/doc/git-doc')
def pin(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def dump(n):return ast.dump(n,include_attributes=False)
checks=[]
def ck(n,v,detail=None):checks.append(dict(name=n,passed=bool(v),detail=detail))
paths=[p for p in S.iterdir() if p.is_file()]+[A/x for x in ['HDF.json','MF.json','prepare_attach_fixture_two_parent.actual_owned.py','validate_attach_fixture_two_parent.actual_owned.py','source.integration.choice.json']]+[V/x for x in ['HDF.json','MF.json','report.md','guard.final.json','checks.json']]+[D/x for x in ['git-read-tree.adoc','git-sparse-checkout.adoc','gitignore.adoc']]+[G,P(__file__)]
refs=[pin(p) for p in paths]
assert pin(G)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
spec=importlib.util.spec_from_file_location('sparse_r2_review_guard',G);gm=importlib.util.module_from_spec(spec);spec.loader.exec_module(gm)
guard=gm.SourceReadGuard();guard.acquire(refs)
def raw(p):return guard.get_buffer(str(P(p)))
def obj(p):return json.loads(raw(p))
def verify(r):
 p=P(r['path']);b=raw(p);return hashlib.sha256(b).hexdigest()==r['sha256'].removeprefix('sha256:') and len(b)==r['bytes']
try:
 save('input-pins.json',refs)
 ck('new-HDF-exact',pin(S/'HDF.json')['sha256']=='3ab44bbce5a496436d187b21840684c48ce98fedf7adf2efb180f3d3a973f291' and len(raw(S/'HDF.json'))==935)
 ck('new-MF-exact',pin(S/'MF.json')['sha256']=='337f849f20000cc041e06453d0b7db5aaaf02036add71906cc37dd8d33b8a73d' and len(raw(S/'MF.json'))==2562)
 for r in obj(S/'MF.json')['members']:ck('manifest:'+P(r['path']).name,verify(r))
 vh=obj(V/'HDF.json')
 for k in ['source_handoff','source_manifest','prepare_ref','validate_ref','choice_ref','manifest_ref','report_ref','checks_ref','guard_ref']:ck('prior-review-binding:'+k,verify(vh[k]))
 ck('prior-status-and-scope',vh['status']=='SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL' and vh['source_members']==58 and vh['preserved_parent_count']==54 and vh['nonselected_parent_count']==52 and vh['all_source_declared_parent_count']==132 and not vh['formal_acceptance'] and vh['ordinary_history20_full_release_program_rehearsal_authority']=='BLOCKED')
 oldguard=obj(V/'guard.final.json');ck('prior-review-file-pins-unchanged',oldguard['unchanged'] and oldguard['before']==oldguard['after'])
 prov=obj(S/'adaptation.provenance.json')
 for change in prov['changes']:
  name=change['name'];old=raw(A/name).decode();new=raw(S/name).decode();trans=old
  ck(name+':old-ref',verify(change['old_ref']));ck(name+':new-ref',verify(change['new_ref']))
  for i,item in enumerate(change['sequential_replacements']):
   ck(name+':forward-count:'+str(i),trans.count(item['before'])==item['count'])
   trans=trans.replace(item['before'],item['after'])
  ck(name+':forward-equal',trans.encode()==raw(S/name))
  for i,item in enumerate(reversed(change['sequential_replacements'])):
   ck(name+':inverse-count:'+str(i),trans.count(item['after'])==item['count'])
   trans=trans.replace(item['after'],item['before'])
  ck(name+':inverse-equal',trans.encode()==raw(A/name))
  ot=ast.parse(old);nt=ast.parse(new)
  of={n.name:n for n in ast.walk(ot) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
  nf={n.name:n for n in ast.walk(nt) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
  ck(name+':all-functions-AST-identical',of.keys()==nf.keys() and all(dump(of[k])==dump(nf[k]) for k in of),sorted(of))
  oldfinally=[dump(ast.Module(body=n.finalbody,type_ignores=[])) for n in ast.walk(ot) if isinstance(n,ast.Try) and n.finalbody]
  newfinally=[dump(ast.Module(body=n.finalbody,type_ignores=[])) for n in ast.walk(nt) if isinstance(n,ast.Try) and n.finalbody]
  ck(name+':all-finally-AST-identical',oldfinally==newfinally)
 ck('choice-byte-identical',raw(S/'source.integration.choice.json')==raw(A/'source.integration.choice.json'))
 choice=obj(S/'source.integration.choice.json')
 ck('choice-58-2-52',choice['expected_source_count']==58 and len(choice['source_preserved_parent_names'])==54 and set(choice['exact_parent_names'])==set(vh['selected_parent_names']) and len(set(choice['source_preserved_parent_names'])-set(choice['exact_parent_names']))==52)
 prep=raw(S/'prepare_attach_fixture_two_parent.actual_owned.py').decode();val=raw(S/'validate_attach_fixture_two_parent.actual_owned.py').decode()
 pt=ast.parse(prep);vt=ast.parse(val)
 def assigned(tree,name):
  return [n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
 def literal_path(tree,name):
  vals=assigned(tree,name);assert len(vals)==1
  return P(ast.literal_eval(vals[0].args[0]))
 expT=R/'.local/worktrees/t11s-1791516205000';expI=B/'integration_codex/attach-fixture-two-parent-sparse-isolation-root-1791516205000';expO=B/'integration_codex/attach-fixture-two-parent-sparse-target-root-1791516205000'
 ck('paths-correct',literal_path(pt,'T')==literal_path(vt,'T')==expT and literal_path(pt,'O')==literal_path(vt,'ISO')==expI and literal_path(vt,'O')==expO)
 scratch=literal_path(vt,'scratch')
 states=[dict(path=str(p),exists=p.exists()) for p in [expT,expI,expO,scratch]]
 ck('all-worktree-output-and-unused-scratch-absent',all(not x['exists'] for x in states),states)
 ck('fresh-scratch-mkdir-noexistok',"scratch=Path(" in val and ");scratch.mkdir()\n" in val)
 ck('no-old-isolation-or-target-literals',not any(x in prep+val for x in ['attach-fixture-current-two-parent-isolation-root-t11-','attach-fixture-current-two-parent-targeted-root-t11-']))
 calls=[n for n in ast.walk(pt) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='invoke'];calls.sort(key=lambda n:n.lineno)
 labels=[ast.literal_eval(n.args[0]) for n in calls]
 ck('six-sequential-owned-Git-jobs',labels==['head-before','tracked-status','staged-status','create-worktree','checkout-product-source','head-after'],labels)
 ck('create-no-checkout-before-sparse-file', '"worktree","add","--no-checkout","--detach",str(T),expected' in prep and prep.index('create=invoke(')<prep.index('git_file=')<prep.index('with sparse.open(')<prep.index('checkout=invoke('))
 ck('checkout-command-scoped-noncone', '"-C",str(T),"-c","core.hooksPath="+str(scratch/"empty-hooks"),"-c","core.sparseCheckout=true","-c","core.sparseCheckoutCone=false","read-tree","-mu","HEAD"' in prep)
 ck('metadata-under-worktrees-and-backpointer', 'metadata.is_relative_to((R/".git/worktrees").resolve())' in prep and '(metadata/"gitdir").read_text' in prep and '==str(T/".git")' in prep)
 ck('new-pattern-file-exclusive-only', 'sparse=metadata/"info/sparse-checkout";assert not sparse.exists()' in prep and 'with sparse.open("x",encoding="utf-8",newline="\\n")' in prep)
 ck('no-shared-config-mutation', '"config",' not in prep and 'write_text' not in prep and 'write_bytes' not in prep)
 dirs=ast.literal_eval(assigned(pt,'product_dirs')[0])
 required={'apps','internal','adapters','evaluation','ops','migrations','spec'}
 ck('all-original-compiler-product-directories-selected',required.issubset(set(dirs)) and '"/execution/toolchains/\\n"' not in prep)
 pattern=assigned(pt,'patterns')[0]
 expected=ast.parse('patterns="/*\\n!/*/\\n"+"".join("/"+name+"/\\n" for name in product_dirs)+"/execution/\\n!/execution/*/\\n/execution/toolchains/\\n"').body[0].value
 ck('pattern-expression-exact-correct-escapes',dump(pattern)==dump(expected))
 pattern_value="/*\n!/*/\n"+"".join("/"+name+"/\n" for name in dirs)+"/execution/\n!/execution/*/\n/execution/toolchains/\n"
 ck('patterns-real-LF-no-literal-backslash-n','\\n' not in pattern_value and len(pattern_value.splitlines())==20)
 save('sparse-pattern-reviewed.json',{'patterns':pattern_value,'interpretation':'Root regular files; recursively selected 15 product top-level directories; execution root regular files plus execution/toolchains recursively. Other execution subdirectories, including v2.4 receipts and verifier, are excluded. Last matching non-cone pattern wins; parent execution is re-included before selecting toolchains.','actual_Git_probe':False,'official_local_docs':[pin(D/x) for x in ['git-read-tree.adoc','git-sparse-checkout.adoc','gitignore.adoc']]})
 ov=raw(A/'validate_attach_fixture_two_parent.actual_owned.py').decode()
 start=' success("tagged-compiler-input-list"';end=' selector='
 ck('complete-compiler-embed-product-and-tools-byte-identical',val[val.index(start):val.index(end)]==ov[ov.index(start):ov.index(end)])
 ck('all-five-guard-closures-preserved','((binary_guard,"binary"),(compiler_guard,"compiler"),(candidate_guard,"candidate"),(runtime_guard,"runtime"),(input_guard,"input"))' in val)
 ck('checkpoint-ready-pins-still-required','assert len(sys.argv)==4' in prep and 'assert len(sys.argv)==8' in val and 'ISOLATION_READY_SHA256 ISOLATION_READY_BYTES' in val and 'assert pin(canonical[0])["sha256"]==checkpoint_sha' in prep and 'assert pin(canonical[0])["sha256"]==checkpoint_sha' in val)
 ck('sparse-ready-binds-six-receipts','invocation_refs=[verify,tracked,staged,create,checkout,verify_after]' in prep and 'owned_jobs=6' in prep)
 save('checks.json',checks)
finally:
 closure=guard.close();save('guard.final.json',closure)
ck('review-guard-closed',closure['closed'] and closure['retained_handles_count']==0 and not closure['errors'] and closure['verification']=='PASSED')
decision='SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES'
save('review.json',{'decision':decision,'checks':checks,'guarded_input_count':len(refs),'fresh_dependency_revalidation_scope':'Changed caller package, old accepted caller bytes and selected independent review bindings. No reread of all 833 transitive prior inputs and no execution of actual Git/Go/native/SQL. Runtime input guards remain mandatory.','authority':'SOURCE_REVIEW_ONLY','formal_acceptance':False,'production_ready':False,'no_global_or_original_trial_provider_claim':True,'actual_entrypoints_run':False,'new_mechanical_errors':0,'stop':True})
print(json.dumps({'decision':decision,'checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'failed':[x for x in checks if not x['passed']],'guarded_input_count':len(refs),'all_guards_closed':closure['closed'],'ROOT_PYTHON_EXIT':0},ensure_ascii=False))

