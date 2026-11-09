"""Append the complete actual diagnostic suffix; retain all preceding counters."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,sys,types
S=Path(__file__).resolve().parent;V=S.parents[4];W=S.parents[1];B=V/'receipts/W05/W05-99'
A=B/'public23_to24_root_integration_preparation_codex/prepare-20261010-01'
CORE=W/'w09_nf6_root_registration_source_codex/register-20261010-01/adoption_core.source.py'
GUARD=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
O=S/'cp395-diagnostics1245-br8-assembly-closed-live1246'
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(p,v):
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
def module(p,n):
    m=types.ModuleType(n);m.__file__=str(p);sys.modules[n]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
current=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert current[0]['sha256']=='d397414b9552e6bce821309257d3123d35b9088987fd3fd43c494e1fbaac995b' and current[1]['sha256']=='b949831cc4827ae2cadae77235188dfff0776a0c8074a57714c1445e16c32a86'
descriptions={1237:'Read-only metadata GetType called on two null case fields; successful reads and rg retained.',1238:'Read-only capture helper guessed wrong parent directory; earlier manifest and source reads retained.',1239:'Metadata capture parser missed truncation-prefixed host output; prior generated composition and first capture retained.',1240:'Root role-extras helper used execution as repository parent; no extras or grant written, v2 changed only path constant.',1241:'Root Source review capture rejected actual peer timestamp jitter; original review and actual records unchanged.',1242:'Second Source review capture in same tool invocation rejected the same timestamp jitter; all original facts retained.',1243:'Postseal PowerShell hash-display foreach pipe parse error; previously sealed recipe unchanged.',1244:'Source review redelivery rejected actual one millisecond peer timestamp jitter; later new genuine delivery accepted.',1245:'Read-only optional helper query used nonexistent filename; successful closed-caller read prefix retained.'}
spec={1237:(A/'diagnostic-appendix/original-1237.binding.json','83dd39',0,None),1238:(A/'diagnostic-appendix/original-1238.binding.json','d9c645',1,None),1239:(A/'diagnostic-appendix/original-1239.binding.json','84c5b7',0,1),1240:(S/'original1240.fixed-actual.binding.root.json','ef501d',1,1),1241:(S/'original1241.fixed-actual.binding.root.json','f317c0',1,1),1242:(S/'original1242.fixed-actual.binding.root.json','5b42cf',1,1),1243:(A/'postseal-diagnostic-1243/binding.json','603011',1,None),1244:(S/'original1244.fixed-actual.binding.root.json','d9e281',1,1),1245:(S/'original1245.fixed-actual.binding.root.json','3ebb2c',1,None)}
rows=[];refs=[pin(CORE),pin(GUARD),pin(TP),*current[2:]]
for ordinal,(p,chunk,outer,pyexit) in spec.items():
    br=pin(p);d=json.loads(p.read_bytes());r=d['original_capture_ref'];rp=Path(r['path']);assert pin(rp)==r
    lines=rp.read_bytes().splitlines(keepends=True);assert len(lines)==3 and all(x.endswith(b'\n') for x in lines)
    digests=d.get('original_line_sha256',d.get('source_line_sha256'));assert digests==[hashlib.sha256(x).hexdigest() for x in lines]
    ev=[json.loads(x) for x in lines];assert ev[0]['type']=='session_meta' and ev[1]['payload']['call_id']==ev[2]['payload']['call_id']==d['original_call_id']
    assert chunk in lines[2].decode('utf-8')
    with Path(d['source_audit_path']).open('rb') as f:
        for off,line in zip(d['source_line_offsets'],lines):f.seek(off);assert f.readline()==line
    row=dict(ordinal=ordinal,origin_ref=r,origin_selector='actual_host_chunk_id='+chunk,capture_binding_ref=br,description=descriptions[ordinal],capture_completeness='ACTUAL_ORIGINAL_HEADER_CALL_RESULT_3LF_WITH_EXACT_SOURCE_OFFSETS',source_fact_refs=[br,r],actual_outer_exit=outer,actual_python_exit=pyexit,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
    rows.append(row);refs.extend((br,r))
pending=dict(schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',counter_reset=False,registered_in_current_canon=False,current_canonical_refs=current,source_cutoff_original_failure_ordinal=1236,next_original_failure_ordinal=1246,pending=rows)
assert not O.exists();O.mkdir();(O/'canonical-journal').mkdir();pending_ref=save(O/'pending.root.json',pending)
refs.append(pending_ref);refs=list({r['path']:r for r in refs}.values())
g=module(GUARD,'root_diagnostics_guard').SourceReadGuard(per_file_cap=64*1024*1024,total_cap=256*1024*1024)
try:
    g.acquire(refs);core=module(CORE,'root_diagnostics_core');tp=module(TP,'root_diagnostics_tp');now=datetime.now(timezone.utc).isoformat()
    def transform(cp,ow):
        assert cp['revision']==394 and ow['revision']==197
        c=copy.deepcopy(cp);ops=[]
        def change(path,value):
            exists,before=core.value_at(c,path);ops.append(dict(path=path,before_exists=exists,before=copy.deepcopy(before),after=copy.deepcopy(value)));core.put(c,path,value)
        merged,end=core.merge_pending(cp,pending,current);assert end==1246 and merged[:len(cp['failure_counters'])]==cp['failure_counters']
        change(['failure_counters'],merged);change(['work_in_progress','root_next_failure_ordinal_live'],end)
        change(['work_in_progress','cp395_diagnostics_and_br8_assembly'],dict(pending_ref=pending_ref,registered_through=1245,next_original_failure_ordinal=1246,formal_acceptance=False,counter_reset=False))
        for key,value in dict(revision=395,expected_previous_revision=394,updated_at=now,updated_by='codex:/root').items():change([key],value)
        assert core.inverse_operations(c,ops)==cp
        save(O/'complete-changes-and-inverse.root.json',dict(checkpoint_operations=ops,ownership_operations=[],complete_structural_inverse=True))
        return c,copy.deepcopy(ow)
    result=tp.update_pair(current[:2],transform,str(O/'canonical-journal'),'close')
    receipt=save(O/'committed.root.json',dict(result,registered_through=1245,next_original_failure_ordinal=1246,counter_reset=False,formal_acceptance=False))
finally:closed=g.close();guard_ref=save(O/'source-guard.closed.root.json',closed)
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
assert current[2:]==[pin(V/n) for n in ('step_state.json','commands.json')]
print(json.dumps(dict(receipt_ref=receipt,guard_ref=guard_ref,current4=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')],formal_acceptance=False),ensure_ascii=False))
