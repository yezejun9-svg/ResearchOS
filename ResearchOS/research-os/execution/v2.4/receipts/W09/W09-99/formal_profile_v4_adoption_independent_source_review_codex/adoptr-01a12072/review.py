import ast, copy, hashlib, json, sys, types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'formal_profile_v4_adoption_source_root/adoptv4-20261009'
N=Path(__file__).resolve().parent
def require(v,c):
    if not v: raise AssertionError(c)
def pin(p):
    p=Path(p).resolve(strict=True); b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,d):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def fixed(p,sha,size):
    v=pin(p); require(v['sha256']==sha and v['bytes']==size,'PIN '+str(p)); return v
sh=fixed(S/'HDF.json','b831260ec029d66ced6b5548c6150f0ac7c33f799d5935faa8051f3108511bbc',1903)
sm=fixed(S/'MF.json','1d6f1adfde71d242943b164f45b3d62dcba7c251fafea4df4c0926e30fdb41f6',1916)
h=json.loads(Path(sh['path']).read_bytes()); manifest=json.loads(Path(sm['path']).read_bytes())
require(h['manifest_ref']==sm,'BOUND_SOURCE_MF')
wr=fixed(S/'adopt_formal_profile.source.py','c5a3e4eae036f6468b8a63c3a4e51a082b1182a6a27484f0bc3393b417bfb668',8759)
src=Path(wr['path']).read_bytes()
writer=types.ModuleType('independent_source_writer');writer.__file__=wr['path'];sys.modules[writer.__name__]=writer
exec(compile(src,wr['path'],'exec'),writer.__dict__)
prepared=writer.prepare()
ph,psh,psm,prh,prm,canon,refs,targets,old,new=prepared
require(h['profile_source_handoff_ref']==psh and h['profile_source_review_handoff_ref']==prh,'EXACT_PREPARED_SOURCE_BINDINGS')
refs += [sh,sm,*manifest['members'],pin(__file__),pin(targets[0])]
prior_guard_path=W/'w09_formal_profile_v4_independent_review_codex/profv4r-01a12c10/sourceguard.final.json'
prior_guard=json.loads(prior_guard_path.read_bytes())
for e in prior_guard['entries']:refs.append({k:e[k] for k in ('path','sha256','bytes')})
refs.append(pin(prior_guard_path))
unique={}
for r in refs:
    writer.read(r);k=r['path'].casefold();require(k not in unique or unique[k]==r,'REF_ALIAS');unique[k]=r
guardmod=types.ModuleType('review_real_source_guard');guardmod.__file__=writer.GP['path'];sys.modules[guardmod.__name__]=guardmod
exec(compile(writer.read(writer.GP),writer.GP['path'],'exec'),guardmod.__dict__)
guard=guardmod.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024)
checks=[]; counterexamples=[]
def check(name,value,detail=None):
    require(value,name);checks.append(dict(name=name,passed=True,detail=detail))
guard.acquire(list(unique.values()))
try:
    check('actual_prepare_fixed_targets_and_Canon_identity',True)
    check('Main_index_exact_before_profile_absent',targets[0].read_bytes()==old and not targets[1].exists())
    check('W07_prefix_51719_bytes',old[:51719]==new[0][:51719])
    oldtree=ast.parse(old);newtree=ast.parse(new[0])
    check('index_original_CLI_guard_retained',ast.dump(oldtree.body[-1])==ast.dump(newtree.body[-1]))
    check('after_pins_qualified_index_profile',[hashlib.sha256(b).hexdigest() for b in new]==['e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b','ec5aefdee5690b5f6df7026b80ee0f185eb740cfbc1837144f54d6bf707e88cd'])
    # Run the exact writer execute function with a read-only in-memory boundary.
    # prepare/receipt reads are supplied; reaching guard source read is a sentinel.
    # No guard or Main publication call can execute in this controlled harness.
    class ReachedGuard(Exception):pass
    ready={'decision':'SOURCE_ACCEPTED_FOR_ROOT_PROFILE_V4_PUBLICATION','actor_role':'INDEPENDENT_NON_AUTHOR','actor_id':'codex:/root/attach_fixture_source_review','writer_ref':wr,'profile_source_handoff_ref':psh,'profile_source_review_handoff_ref':prh}
    execute_ast=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='execute')
    def controlled_receipt(doc,mode='activate',review_ref=True):
        env=dict(writer.__dict__)
        env['prepare']=lambda:(ph,psh,psm,prh,prm,canon,[],targets,old,new)
        env['decode']=lambda ref:doc
        env['pin']=lambda path:wr
        def stop_before_guard(ref):raise ReachedGuard('SOURCE_GATE_PASSED_BEFORE_ANY_MAIN_WRITE')
        env['read']=stop_before_guard
        exec(compile(ast.Module(body=[execute_ast],type_ignores=[]),wr['path'],'exec'),env)
        try:env['execute'](mode,wr if review_ref else None)
        except ReachedGuard:return 'SOURCE_GATE_PASSED_BEFORE_ANY_MAIN_WRITE'
        except (ValueError,KeyError,TypeError) as e:return str(e)
        raise AssertionError('UNEXPECTED_EXECUTE_RETURN')
    success='SOURCE_GATE_PASSED_BEFORE_ANY_MAIN_WRITE'
    check('valid_identified_non_author_gate_accepts',controlled_receipt(ready)==success)
    for actor in ('codex:/root',):
        d=copy.deepcopy(ready);d['actor_id']=actor
        check('exact_Root_self_review_rejected',controlled_receipt(d)=='ROOT_ADOPTER_NONSIGNED_SOURCE_REVIEW')
    for label,actor in [('null',None),('empty_string',''),('false',False),('empty_list',[]),('Root_path_alias','/root')]:
        d=copy.deepcopy(ready);d['actor_id']=actor;result=controlled_receipt(d)
        check('counterexample_actor_'+label,result==success)
        counterexamples.append(dict(label=label,input=d,expected='REJECT_UNIDENTIFIED_OR_ROOT_ALIAS_REVIEWER',actual=result,Main_written=False))
    for field in ('decision','actor_role','writer_ref','profile_source_handoff_ref','profile_source_review_handoff_ref'):
        d=copy.deepcopy(ready);d[field]='incorrect'
        check('wrong_'+field+'_rejected',controlled_receipt(d)!=success)
    check('missing_review_ref_rejected',controlled_receipt(ready,review_ref=False)=='ADOPTER_INDEPENDENT_REVIEW_REQUIRED')
    check('invalid_mode_rejected',controlled_receipt(ready,mode='retry')=='MODE')
    # Extract and evaluate exact target gate against controlled path observations.
    prep_ast=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
    call=next(n for n in ast.walk(prep_ast) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='FIXED_TARGET_NO_ALIAS')
    class Target:
        def __init__(self,parent,symlink=False,junction=False):self.parent=self;self.where=parent;self.symlink=symlink;self.junction=junction
        def resolve(self,strict=True):return self.where
        def is_symlink(self):return self.symlink
        def is_junction(self):return self.junction
    target_code=compile(ast.Expression(call.args[0]),wr['path'],'eval')
    for label,target,expected in [('regular',Target(R/'execution/v2.4'),True),('symlink',Target(R/'execution/v2.4',symlink=True),False),('junction',Target(R/'execution/v2.4',junction=True),False),('parent_alias',Target(R/'outside'),False)]:
        check('target_'+label,eval(target_code,dict(R=R,target=target)) is expected)
    # Exact publication CAS expression rejects drift to either target.
    cas=next(n for n in ast.walk(execute_ast) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='PUBLICATION_LAST_CAS')
    cas_code=compile(ast.Expression(cas.args[0]),wr['path'],'eval')
    class Bytes:
        def __init__(self,b):self.b=b
        def read_bytes(self):return self.b
    for label,values,expected in [('exact',[old,new[1]],True),('index_drift',[b'drift',new[1]],False),('profile_drift',[old,b'drift'],False)]:
        check('last_CAS_'+label,eval(cas_code,dict(targets=[Bytes(b) for b in values],old=old,new=new)) is expected)
    source_text=src.decode()
    check('profile_exclusive_create_before_stage_before_replace',source_text.index("with targets[1].open('xb')")<source_text.index("with stage.open('xb')")<source_text.index('os.replace(stage,targets[0])'))
    check('two_fsync_operations_present',source_text.count('f.flush();os.fsync(f.fileno())')==3)
    check('no_retry_or_rollback_outcome_contract','automatic_retry=False,automatic_rollback=False' in source_text)
    check('two_fixed_Main_targets_only',str(targets[0])==str(R/'execution/v2.4/formal_case_index.py') and str(targets[1])==str(R/'execution/v2.4/formal_profile_w09.py'))
    check('failure_preserved_before_raise',source_text.index("outcome=save('publication.outcome.'")<source_text.index("require(error is None,'PUBLICATION_FAILED_PRESERVE_OUTCOME_AND_RECONCILE')"))
    check('Main_index_profile_unchanged_after_controls',targets[0].read_bytes()==old and not targets[1].exists())
    for ref in canon:writer.read(ref)
    check('four_Canonical_files_exact_unchanged',True)
    controls_ref=save('controls.json',dict(schema='researchos.adopter-source-controls.v1',evidence_kind='NON_AUTHORITATIVE_SOURCE_CONTROLS',checks=checks,counterexamples=counterexamples,actual_Main_publication=False,actual_formal_evidence=False))
finally:
    closure=guard.close();guard_ref=save('sourceguard.final.json',closure)
require(closure['closed'] is True and closure['retained_handles_count']==0 and not closure['errors'],'REAL_GUARD_CLOSED')
findings=[dict(id='ADOPTER-F1',priority='P1',title='Independent review gate accepts absent reviewer identity and Root path alias',source_ref=wr,line=69,evidence_ref=controls_ref,actual='The exact execute gate accepts actor_id null, empty string, false, empty list, and /root. Exact codex:/root is rejected, but this does not establish an identified independent non-author.',expected='Bind actor_id to the canonical independently designated reviewer codex:/root/attach_fixture_source_review; reject wrong types, blanks, and noncanonical identities before source guard/publication.',impact='A malformed or Root-aliased receipt with all other fields exact can authorize entry into the activation publication path. Controlled execution stopped at the guard read sentinel and performed no Main writes.')]
fr=save('findings.json',dict(findings=findings,blocking_count=1,scope='SOURCE_QUALIFICATION_ONLY'))
decision=save('source-decision.json',dict(schema='researchos.adopter-independent-source-decision.v1',decision='REQUEST_CHANGES',actor_role='INDEPENDENT_NON_AUTHOR',actor_id='codex:/root/attach_fixture_source_review',writer_ref=wr,source_handoff_ref=sh,source_manifest_ref=sm,profile_source_handoff_ref=psh,profile_source_review_handoff_ref=prh,findings_ref=fr,controls_ref=controls_ref,actual_SourceGuard_ref=guard_ref,retained_handles_count=0,checks=len(checks),Main_adopted=False,Canonical_writes=False,formal_case_accepted_delta=0,parent_acceptance=False,STOP=True,FINAL=True))
print(json.dumps(dict(decision_ref=decision,findings_ref=fr,controls_ref=controls_ref,guard_ref=guard_ref,checks=len(checks),held_refs=len(unique)),ensure_ascii=False))
