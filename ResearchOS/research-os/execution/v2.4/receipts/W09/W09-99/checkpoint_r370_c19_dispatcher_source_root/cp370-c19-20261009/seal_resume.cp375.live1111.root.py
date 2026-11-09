"""Continue the retained failed resume writer without overwriting its outputs."""
from pathlib import Path
source=Path(__file__).with_name('seal_resume.cp375.live1110.root.py').read_text(encoding='utf-8')
old="""    with (N/('historical.cp375.before-native.'+name+'.json')).open('xb') as f:
        f.write(Path(ref['path']).read_bytes());f.flush();os.fsync(f.fileno())"""
new="""    archived=N/('historical.cp375.before-native.'+name+'.json')
    assert archived.read_bytes()==Path(ref['path']).read_bytes()"""
assert source.count(old)==1;source=source.replace(old,new)
old="pair=capture(AUDIT,1109,match,root=True);assert pair"
new="""pair=(pin(N/'original1109.actual-host.raw.jsonl'),pin(N/'original1109.actual-host.binding.root.json'))
assert pair[0]['sha256']=='ad003e1d84f94baf770504e140867f5ea2391a605f9471e2d82eccebb930cf3e'
bound=json.loads(Path(pair[1]['path']).read_bytes());lines=Path(pair[0]['path']).read_bytes().splitlines(keepends=True)
with AUDIT.open('rb') as f:
    for off,line in zip(bound['source_line_offsets'],lines):f.seek(off);assert f.readline()==line"""
assert source.count(old)==1;source=source.replace(old,new)
assert source.count("'ROOT_SOURCE_PYTHON_EXIT=1'")==1
source=source.replace("'ROOT_SOURCE_PYTHON_EXIT=1'","'ROOT_ACTUAL_PYTHON_EXIT=1'")
source=source.replace('live1110','live1111').replace('next1110','next1111')
source=source.replace('next_original_failure_ordinal=1110','next_original_failure_ordinal=1111')
old="pending=save('pending-diagnostics.cp375.live1111.root.json',dict("
new="""def failure1110(call,result):return any(x.get('chunk_id')=='8199f4' for x in outputs(result['payload'].get('output')))
pair1110=capture(AUDIT,1110,failure1110,root=True);assert pair1110
host1110=[x for x in outputs(json.loads(Path(pair1110[0]['path']).read_bytes().splitlines()[-1])['payload']['output']) if x.get('chunk_id')=='8199f4']
assert len(host1110)==1 and host1110[0]['exit_code']==1 and 'ROOT_SOURCE_PYTHON_EXIT=1' in host1110[0]['output']
binding1110=save('original1110.standard-binding.live1111.root.json',dict(
    schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',original_capture_ref=pair1110[0],
    original_source_binding_ref=pair1110[1],original_source_binding_selector='$',original_ordinal=1110,
    original_bytes_unchanged=True,formal_authority=False))
row1110=dict(ordinal=1110,origin_ref=pair1110[0],origin_selector='$',capture_binding_ref=binding1110,
    description='Root resume writer checked the Source Python marker for an actual product-stage invocation whose real marker is ROOT_ACTUAL_PYTHON_EXIT. Original assertion retained; full CP375 archives and original1109 capture preserved; no Canon or product process writes.',
    capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=1,actual_python_exit=1,
    actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
pending=save('pending-diagnostics.cp375.live1111.root.json',dict("""
assert source.count(old)==1;source=source.replace(old,new)
source=source.replace('pending=[row],','pending=[row,row1110],').replace('pending_diagnostic_ordinals=[1109]','pending_diagnostic_ordinals=[1109,1110]')
source=source.replace('original1109 pending','original1109 and1110 pending')
exec(compile(source,str(Path(__file__)),'exec'),globals())
