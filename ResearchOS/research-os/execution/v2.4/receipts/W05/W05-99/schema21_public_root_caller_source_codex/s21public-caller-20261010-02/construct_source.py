"""Task105 narrow safe_directory Source revision. No Root stages or products."""
import ast,copy,hashlib,json,ntpath,sys,traceback,types
from pathlib import Path,PureWindowsPath
Q=Path(__file__).resolve().parent
OLD=Q.parent/'s21public-caller-20261010-01'
R=Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
ACTOR='codex:/root/backup_regression_resources'
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
ROOT_AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
GUARD={'path':str(R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'),'sha256':'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','bytes':11404}
WITNESSES=[{'path':str(S/'w09.public21-directory-gate-finding.actual-audit.root.json'),'sha256':'6c2b58214f37292daed60bb860a045a335ed4094cffac9442323b98aef858930','bytes':1121},
 {'path':str(S/'w09.public21-root-helper-original1146.actual-audit.root.json'),'sha256':'0c7c491e043cdf781ff5b54a23ca7e5fbd7175145848d2a67c27e3ed39088d10','bytes':1100}]
def need(ok,code):
    if not ok:raise ValueError(code)
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(r):
    need(pin(r['path'])=={**r,'path':str(Path(r['path']))},'SOURCE_INPUT_PIN');return Path(r['path']).read_bytes()
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
def save(name,v):
    with (Q/name).open('xb')as f:f.write(encoded(v))
    return pin(Q/name)
def write_bytes(name,raw):
    with (Q/name).open('xb')as f:f.write(raw)
    return pin(Q/name)
def check(name,passed,evidence=None):return dict(name=name,passed=bool(passed),evidence=evidence)
def actual_witness(r):
    a=json.loads(read(r));original=a['original_capture_ref'];raw=read(original);lines=raw.splitlines(keepends=True)
    need(len(lines)==3 and all(x.endswith(b'\n')for x in lines),'EXACT_THREE_ORIGINAL_LF_ROWS')
    h,call,result=[json.loads(x)for x in lines]
    need(h['type']=='session_meta'and h['payload']['id']==ROOT_THREAD and a['Root_thread_id']==ROOT_THREAD and a['source_audit_path']==str(ROOT_AUDIT),'ACTUAL_ROOT_HEADER')
    need(a['binding_sha256']=='010b3907632f6e065b9765b880fd57287950e5464d6410415484f8121111bd63','ROOT_FINDING_BASE_CALLER')
    need(a['original_line_sha256']==[hashlib.sha256(x).hexdigest()for x in lines],'ACTUAL_ORIGINAL_LINE_PINS')
    with ROOT_AUDIT.open('rb')as f:
        for at,line in zip(a['source_line_offsets'],lines):
            need(type(at)is int and at+len(line)<=a['source_prefix_size_observed'],'SOURCE_FINITE_OFFSETS')
            f.seek(at);need(f.read(len(line))==line,'TRUE_ROOT_SOURCE_BYTES')
    if a['actor_id']=='codex:/root':
        need(call['payload']['call_id']==result['payload']['call_id']and call['payload']['type']in ('custom_tool_call','function_call')and result['payload']['type']in ('custom_tool_call_output','function_call_output'),'ACTUAL_ROOT_ORIGINAL1146_PAIR')
    else:
        need(a['actor_id']=='codex:/root/full_w09_source_review'and call['type']=='inter_agent_communication_metadata'and result['ordinal']==call['ordinal']+1 and result['payload']['author']=='/root/full_w09_source_review'and result['payload']['recipient']=='/root'and result['metadata']['client_authored']is False,'ACTUAL_TASK102_PEER')
    return dict(witness_ref=r,original_capture_ref=original,actor=a['actor_id'],source_offsets=a['source_line_offsets'],actual_original_verified=True)
def main():
    oldh=pin(OLD/'HDF.json');h=json.loads(read(oldh));oldm=h['manifest_ref'];read(oldm)
    source_ref=h['caller_ref'];source=read(source_ref)
    need(source_ref['sha256']=='010b3907632f6e065b9765b880fd57287950e5464d6410415484f8121111bd63'and source_ref['bytes']==55236,'FIXED_CALLER01_SOURCE')
    tree=ast.parse(source);safe=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='safe_directory')
    lines=source.splitlines(keepends=True);start=sum(map(len,lines[:safe.lineno-1]));end=sum(map(len,lines[:safe.end_lineno]))
    before=source[start:end]
    after=b'''def safe_directory(path,new=False):
    canonical(str(path));p=Path(path)
    for ancestor in (p,*p.parents):
        if ancestor.exists():
            need(not ancestor.is_symlink() and not ancestor.is_junction()
                and not (getattr(ancestor.lstat(),'st_file_attributes',0)&0x400)
                and ntpath.normcase(str(ancestor.resolve(strict=True)))==ntpath.normcase(str(ancestor.absolute())),'DIRECTORY_ALIAS')
    need(p.parent.is_dir() and (not p.exists() if new else p.is_dir()),'DIRECTORY_EXISTENCE')
    return p
'''
    candidate=source[:start]+after+source[end:]
    need(candidate[:start]+before+candidate[start+len(after):]==source,'EXACT_SOURCE_BYTE_INVERSE')
    ntree=ast.parse(candidate);compile(candidate,str(Q/'public21_root.source.py'),'exec')
    oldfunctions={x.name:ast.dump(x,include_attributes=False)for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))and x.name!='safe_directory'}
    newfunctions={x.name:ast.dump(x,include_attributes=False)for x in ntree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))and x.name!='safe_directory'}
    need(oldfunctions==newfunctions,'ALL_OTHER_FUNCTIONS_CLASSES_UNCHANGED')
    current=write_bytes('public21_root.source.py',candidate)
    inverse=save('directory-exact-inverse.json',dict(schema='researchos.public21-directory-root-Source-revision.v1',base_source_ref=source_ref,candidate_ref=current,old_start=start,old_end=end,new_start=start,new_end=start+len(after),before_utf8=before.decode(),after_utf8=after.decode(),restored_Source_sha256=hashlib.sha256(source).hexdigest(),restored_Source_bytes=len(source),exact_inverse=True,business_changes=['safe_directory ancestor directory identity and reparse rejection'],other_function_class_count=len(oldfunctions),other_functions_classes_identical=True,first_file_canonical_statement_unchanged=True,automatic_N_from___file___unchanged=True))
    witnesses=[actual_witness(r)for r in WITNESSES]
    read(GUARD);gm=types.ModuleType('task105_source_guard');gm.__file__=GUARD['path'];exec(compile(read(GUARD),GUARD['path'],'exec'),gm.__dict__)
    env={'Path':Path,'ntpath':ntpath,'need':need,'canonical':gm._canonical}
    node=next(x for x in ntree.body if isinstance(x,ast.FunctionDef)and x.name=='safe_directory')
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<exact-candidate-safe-directory>','exec'),env)
    controls=[]
    existing=R/'execution/v2.4/receipts/W05/W05-99/integration_codex'
    refs=[oldh,oldm,source_ref,h['contract_ref'],h['source_inputs_ref'],h['source_controls_ref'],h['Source_full_closure_ref'],GUARD,current,inverse,*WITNESSES,*[x['original_capture_ref']for x in witnesses],pin(__file__)]
    guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
    try:
        guard.acquire(refs)
        controls.append(check('existing_integration_directory_with_D_drive_ancestor',env['safe_directory'](existing)==existing,dict(directory=str(existing),ancestors=[str(x)for x in existing.parents])))
        fresh=Q/'never-created-directory-boundary-control'
        controls.append(check('new_leaf_under_existing_owned_Source_directory',not fresh.exists()and env['safe_directory'](fresh,new=True)==fresh,dict(path=str(fresh),created=False)))
        for name,p in [('UNC',r'\\server\share\x'),('extended_namespace',r'\\?\D:\x'),('device_namespace',r'\\.\D:\x'),('ADS',r'D:\x\y:stream'),('traversal',r'D:\x\..\y')]:
            error=None
            try:env['safe_directory'](p,new=True)
            except ValueError as exc:error=str(exc)
            controls.append(check('reject_'+name,error is not None,dict(error=error)))
        # Synthetic metadata only, no OS junction, symlink or product fixture is created.
        class FakeDirectory:
            def __init__(self,kind='regular',drive=False):self.kind=kind;self.drive=drive
            def __str__(self):return 'D:\\'if self.drive else 'D:\\synthetic-directory-boundary'
            @property
            def parents(self):return ()if self.drive else (FakeDirectory(drive=True),)
            @property
            def parent(self):return FakeDirectory(drive=True)
            def exists(self):return True
            def is_dir(self):return True
            def is_symlink(self):return self.kind=='symlink'
            def is_junction(self):return self.kind=='junction'
            def lstat(self):return types.SimpleNamespace(st_file_attributes=0x400 if self.kind=='reparse'else 16)
            def absolute(self):return PureWindowsPath(str(self))
            def resolve(self,strict=True):return PureWindowsPath('D:/different-alias')if self.kind=='alias'else self.absolute()
        for kind in ('symlink','junction','reparse','alias'):
            env['Path']=lambda p,kind=kind:FakeDirectory(kind)
            error=None
            try:env['safe_directory']('D:/synthetic-directory-boundary')
            except ValueError as exc:error=str(exc)
            controls.append(check('synthetic_reject_'+kind,error=='DIRECTORY_ALIAS',dict(error=error,synthetic=True,product_fixture=False)))
        env['Path']=Path
        controls.append(check('strict_file_reference_first_statement_preserved',before.splitlines()[1]==after.splitlines()[1]))
        controls.append(check('exact_other_Source_bytes_and_AST_unchanged',oldfunctions==newfunctions and candidate[:start]+before+candidate[start+len(after):]==source))
    finally:closed=guard.close();closedref=save('directory-delta.SourceGuard.closed.json',closed)
    need(closed['closed']is True and closed['verification']=='PASSED'and closed['retained_handles_count']==0 and not closed['errors'],'DIRECTORY_SOURCE_GUARD_CLOSED')
    controlsref=save('directory-delta-controls.json',dict(schema='researchos.public21-directory-delta-Source-controls.v1',controls=controls,passed=sum(x['passed']for x in controls),failed=sum(not x['passed']for x in controls),synthetic_metadata_only=True,actual_products_run=0,actual_Root_stages=[],old58_353_17_4154_controls_replayed=False,guard_ref=closedref))
    need(all(x['passed']for x in controls),'DIRECTORY_DELTA_SOURCE_CONTROLS_FAILED')
    contract=json.loads(read(h['contract_ref']));contract['caller_ref']=current
    contract['directory_gate_revision']=dict(base_caller_ref=source_ref,exact_inverse_ref=inverse,directory_ancestor_comparison='ntpath.normcase(str(resolve(strict=True))) == ntpath.normcase(str(absolute()))',drive_root='Allowed as observed directory ancestor; never treated as a file ref.',file_ref_canonical='Unchanged strict first statement and SourceReadGuard.',reparse='Reject symlink/junction/FILE_ATTRIBUTE_REPARSE_POINT 0x400 at each existing ancestor.',Source_author=ACTOR,source_thread=THREAD,Root_original1146_and_Task102_refs=WITNESSES,new_Source_non_author_review_required=True,new_runtime_qualification_required=True,old_controls_replayed=False,execution_grant=False)
    contractref=save('root-calling-contract.source.json',contract)
    inputs=json.loads(read(h['source_inputs_ref']))
    inputs['references']=[current if x['sha256']==source_ref['sha256']and x['bytes']==source_ref['bytes']and Path(x['path'])==Path(source_ref['path'])else x for x in inputs['references']]
    inputs['directory_revision']=dict(base_hdf_ref=oldh,base_mf_ref=oldm,inverse_ref=inverse,actual_finding_witnesses=witnesses,controls_ref=controlsref,guard_ref=closedref,Source_author=ACTOR,author_thread=THREAD,new_Source_review=None,new_Root_RuntimeScope=None,actual_Root_current4=None)
    inputsref=save('source-inputs.json',inputs)
    save('Source-revision-build.json',dict(schema='researchos.public21-root-caller-directory-Source-build.v1',source_author=ACTOR,author_thread=THREAD,Root_thread=ROOT_THREAD,base_hdf_ref=oldh,base_mf_ref=oldm,base_contract_ref=h['contract_ref'],base_source_inputs_ref=h['source_inputs_ref'],caller_ref=current,contract_ref=contractref,source_inputs_ref=inputsref,inverse_ref=inverse,new_controls_ref=controlsref,new_guard_ref=closedref,reused_base_58_controls_ref=h['source_controls_ref'],Root_finding_witnesses=witnesses,old_Source_unmodified=True,old_Runtime_authority_not_reused=True,Root_stages_run=[],Native_Go_SQL_model_TP_dispatcher_calls=0,Main_written=False,Canon_written=False,formal_acceptance=False,execution_grant=False))
    print(json.dumps(dict(caller_ref=current,contract_ref=contractref,source_inputs_ref=inputsref,passed_controls=len(controls),guard_closed=closed['closed'],retained_handles=closed['retained_handles_count'],actual_Root_stages=[],old_controls_replayed=False),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
