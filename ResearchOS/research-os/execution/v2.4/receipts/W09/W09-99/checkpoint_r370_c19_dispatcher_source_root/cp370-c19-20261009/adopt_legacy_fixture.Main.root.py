"""Root adopts the independently reviewed single-test delta with owned bytes."""
from pathlib import Path
from datetime import datetime, timezone
import ctypes, hashlib, json, os, sys, types
from ctypes import wintypes

R=Path(r'D:\作品集\ResearchOS\research-os')
N=Path(__file__).resolve().parent
L=N/'legacy-fixture-repair-20261010-01'
V=R/'execution/v2.4/receipts/W09/W09-99/full_w09_actual_native_independent_review_codex/actual-three-20261010-01'
TARGET=R/'internal/domain/retrieval_test.go'
GUARD=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
O=N/'legacy-fixture-Main-adoption-20261010-01'

def pin(p,raw=None):
    p=Path(p);raw=p.read_bytes() if raw is None else raw
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def save(name,value,raw=False):
    data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (O/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    return pin(O/name,data)

proposal=json.loads((L/'proposal.json').read_bytes())
expected=proposal['original_Main_ref'];candidate=proposal['candidate_ref']
assert expected['path']==str(TARGET) and expected['sha256']=='518c6dbd8dbb774b88434138fd3f10f3e231843acf83f086a1ad7a381e2ffe69'
assert candidate['sha256']=='1254f8c7524638cac6bee492fe7d4daf685722250779f86e36e97b0e7a9f1141'
review_ref=pin(V/'legacy-fixture-candidate.independent-review.json')
assert review_ref['sha256']=='0e0dcf8bf793eca059f9b4daed2d7ded6aea2fbdd462ae29d4f57debf230ca49'
review_hdf_ref=pin(V/'HDF.json')
assert review_hdf_ref['sha256']=='8736edead7afeab47341b2f8e484c469e4c24aa86c31244f03109afc96152233'
peer_ref=pin(N/'w09.current-three-native-review.actual-audit.root.json')
assert peer_ref['sha256']=='fb9bdcf4879283397bbade09ec86ca5b4422ed90db4dfbf132050cbc0c7ed2c5'
peer=json.loads(Path(peer_ref['path']).read_bytes())
assert peer['actor_id']=='codex:/root/full_w09_source_review' and peer['binding_sha256']==review_hdf_ref['sha256']
current=[pin(R/'execution/v2.4'/x) for x in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']]
assert current[0]['sha256']=='f34a75bc2d85c64e079cbdff4e54eeb0483514279dbe54a0ae9a242212a6b267'
assert current[1]['sha256']=='8571ee5f91adeacb683e197307628fb300e62c7ff1472b48b9e3468c89569cbd'
guard_ref=pin(GUARD)
assert guard_ref['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
refs=[candidate,proposal['original_copy_ref'],pin(L/'proposal.json'),review_ref,review_hdf_ref,
      pin(V/'MF.json'),peer_ref,peer['original_capture_ref'],*current,
      *[x for x in proposal['input_refs'] if x['path']!=str(TARGET)]]
refs=list({x['path']:x for x in refs}.values())
m=types.ModuleType('root_legacy_adoption_guard');m.__file__=str(GUARD);sys.modules[m.__name__]=m
exec(compile(GUARD.read_bytes(),str(GUARD),'exec'),m.__dict__)
guard=m.SourceReadGuard(per_file_cap=64*1024*1024,total_cap=256*1024*1024)
O.mkdir(exist_ok=False)
handle=None;written=False;closed=None;close_error=None
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
HANDLE=ctypes.c_void_p;DWORD=wintypes.DWORD;BOOL=wintypes.BOOL
def bind(name,args,result):
    f=getattr(kernel,name);f.argtypes=args;f.restype=result;return f
create=bind('CreateFileW',[wintypes.LPCWSTR,DWORD,DWORD,ctypes.c_void_p,DWORD,DWORD,HANDLE],HANDLE)
close=bind('CloseHandle',[HANDLE],BOOL)
size=bind('GetFileSizeEx',[HANDLE,ctypes.POINTER(ctypes.c_longlong)],BOOL)
seek=bind('SetFilePointerEx',[HANDLE,ctypes.c_longlong,ctypes.c_void_p,DWORD],BOOL)
read=bind('ReadFile',[HANDLE,ctypes.c_void_p,DWORD,ctypes.POINTER(DWORD),ctypes.c_void_p],BOOL)
write=bind('WriteFile',[HANDLE,ctypes.c_void_p,DWORD,ctypes.POINTER(DWORD),ctypes.c_void_p],BOOL)
end=bind('SetEndOfFile',[HANDLE],BOOL);flush=bind('FlushFileBuffers',[HANDLE],BOOL)
final=bind('GetFinalPathNameByHandleW',[HANDLE,wintypes.LPWSTR,DWORD,DWORD],DWORD)
def checked(ok):
    if not ok:raise ctypes.WinError(ctypes.get_last_error())
def owned_read():
    length=ctypes.c_longlong();checked(size(handle,ctypes.byref(length)))
    assert 0<length.value<128*1024
    checked(seek(handle,0,None,0));buf=ctypes.create_string_buffer(length.value);got=DWORD()
    checked(read(handle,buf,length.value,ctypes.byref(got),None));assert got.value==length.value
    return buf.raw[:got.value]
try:
    guard.acquire(refs)
    cp=json.loads(Path(current[0]['path']).read_bytes());ow=json.loads(Path(current[1]['path']).read_bytes())
    assert cp['revision']==376 and ow['revision']==180
    assert ow['active_integrator']['id']=='codex:/root' and ow['card_path_bindings']['W09-99']['owner']=='codex:/root'
    hdf=json.loads(Path(review_hdf_ref['path']).read_bytes())
    assert hdf['fixture_source_verdict']=='SOURCE_ACCEPTED_CANDIDATE_ONLY'
    assert hdf['fixture_source_review_ref']==review_ref and hdf['all_guards_closed'] and hdf['retained_handles_count']==0
    before=Path(proposal['original_copy_ref']['path']).read_bytes()
    after=Path(candidate['path']).read_bytes()
    assert pin(candidate['path'],after)==candidate
    mark=b'func TestW09LegacyRootMigrationRevokesUnidentifiedRoot('
    assert before.count(mark)==after.count(mark)==1
    assert before.split(mark)[0]==after.split(mark)[0]
    for ancestor in (TARGET,*TARGET.parents):
        assert not ancestor.is_symlink() and not ancestor.is_junction()
    handle=create(str(TARGET),0x80000000|0x40000000,0,None,3,0x80,None)
    if not handle or handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    name=ctypes.create_unicode_buffer(32768);count=final(handle,name,len(name),0)
    assert 0<count<len(name) and Path(name.value.removeprefix('\\\\?\\'))==TARGET
    original=owned_read();assert original==before and pin(TARGET,original)==expected
    before_ref=save('Main.before.raw',original,True);after_ref=save('Main.after.proposed.raw',after,True)
    save('intent.json',dict(schema='researchos.w09-single-Main-fixture-adoption-intent.v1',
        actor_id='codex:/root',expected_Main_ref=expected,candidate_ref=candidate,
        original_archive_ref=before_ref,proposed_archive_ref=after_ref,
        independent_review_ref=review_ref,independent_HDF_ref=review_hdf_ref,
        real_independent_Final_capture_ref=peer_ref,current_canonical_refs=current,
        mandatory_share_mode=0,production_migration_gates_changed=False,
        automatic_inverse=False,automatic_retry=False,formal_acceptance=False))
    checked(seek(handle,0,None,0));buf=ctypes.create_string_buffer(after);done=DWORD()
    checked(write(handle,buf,len(after),ctypes.byref(done),None));assert done.value==len(after)
    checked(end(handle));checked(flush(handle));written=True
    assert owned_read()==after
    save('committed.while-owned.json',dict(actual_Main_ref=pin(TARGET,after),
        actual_write_complete=True,actual_readback_while_exclusive=True,
        Source21_current_evidence_revalidation_required=True,actual_Go_test='NOT_RUN',
        production_migration_gates_changed=False,formal_case_accepted_delta=0))
except BaseException as exc:
    partial=None
    if handle and handle!=ctypes.c_void_p(-1).value:
        try:partial=save('Main.failed.partial.raw',owned_read(),True)
        except BaseException as pe:partial=dict(observation_error=repr(pe))
    save('failed.json',dict(error=repr(exc),written=written,partial_ref=partial,
        automatic_inverse=False,automatic_retry=False,Root_reconciliation_required=True))
    raise
finally:
    if handle and handle!=ctypes.c_void_p(-1).value:
        if not close(handle):close_error=ctypes.get_last_error()
    closed=guard.close()
    guard_closed_ref=save('source-guard.closed.json',closed)
    save('owned-write.closed.json',dict(target=str(TARGET),CloseHandle_error=close_error,
        target_handle_closed=close_error is None,actual_write_complete=written))
assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0 and close_error is None
assert pin(TARGET)==dict(candidate,path=str(TARGET)) and all(pin(x['path'])==x for x in current)
receipt_ref=save('adoption.closed.json',dict(schema='researchos.w09-legacy-fixture-Main-adoption.v1',
    actor_id='codex:/root',created_at=datetime.now(timezone.utc).isoformat(),
    before_Main_ref=expected,actual_Main_ref=pin(TARGET),independent_review_ref=review_ref,
    real_independent_Final_capture_ref=peer_ref,source_guard_closed_ref=guard_closed_ref,
    all_handles_closed=True,production_gates_unchanged=True,canonical_unchanged=True,
    actual_Go_test='NOT_RUN_PENDING_NEW_QUALIFIED_SOURCE_SCOPE',
    old_Native_and_consumers_retained_historically=True,
    Source21_after_adoption_requires_new_evidence=True,formal_case_accepted_delta=0))
print(json.dumps(dict(adoption_closed_ref=receipt_ref,actual_Main_ref=pin(TARGET),
    all_handles_closed=True,canonical_unchanged=True,formal_acceptance=False),ensure_ascii=False))
