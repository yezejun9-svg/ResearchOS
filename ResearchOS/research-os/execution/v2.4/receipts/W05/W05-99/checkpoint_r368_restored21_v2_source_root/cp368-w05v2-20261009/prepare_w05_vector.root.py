"""After CP368 registration, freeze the same four-document vector for both stages."""
import json
from pathlib import Path
import sys
import types
N=Path(__file__).resolve().parent
w=N/'register_cp368.source.py';m=types.ModuleType('root_w05_vector');m.__file__=str(w);sys.modules[m.__name__]=m
exec(compile(w.read_bytes(),str(w),'exec'),m.__dict__)
def main():
    facts=m.load(m.pin(N/'checkpoint.execution.facts.json'));scope,owner,worker=m.scope_bindings(facts)
    refs=[m.pin(p) for p in m.CANON];cp,ow=[m.load(ref) for ref in refs[:2]]
    m.require(cp['revision']==368 and ow['revision']==172,'CURRENT_CP368_OW172')
    m.require(cp['work_in_progress']['root_next_failure_ordinal_live']==958,'CURRENT_LIVE958')
    m.require(ow['card_path_bindings']['W05-99']['subtasks'][m.KEY]==owner and [v for v in cp['workers'] if v.get('slice_id')==m.SLICE]==[worker],'EXACT_CANONICAL_ROOT_W05_OWNER_AND_WORKER')
    m.require(refs[2:]==facts['canonical_refs'][2:],'SS_COMMANDS_UNCHANGED')
    m.require(ow['card_path_bindings']['W05-99']['owner']==scope['historical_W05_parent_owner'],'HISTORICAL_PARENT_OWNER_RETAINED')
    for k in ('worktree','environment','isolation_output','validation_output'):
        m.require(not Path(scope[k]).exists(),'FRESH_PRIVATE_PATH_'+k)
    vector=dict(schema='researchos.root-restored21-v3-current-canonical-vector.v1',expected_head=cp['head'],checkpoint_revision=368,ownership_revision=172,refs=refs,scope_ref=facts['scope_ref'])
    vr=m.save('W05-current-canonical-vector.actual.root.json',vector)
    base=[cp['head'],refs[0]['sha256'],str(refs[0]['bytes']),'368',refs[1]['sha256'],str(refs[1]['bytes']),refs[2]['sha256'],str(refs[2]['bytes']),refs[3]['sha256'],str(refs[3]['bytes'])]
    prepare=[str(Path(sys.executable).resolve()),'-I','-S','-B','-X','utf8',scope['prepare_caller_ref']['path'],*base]
    validate_prefix=[str(Path(sys.executable).resolve()),'-I','-S','-B','-X','utf8',scope['validator_ref']['path'],*base]
    m.save('W05-two-stage-argv.actual.root.json',dict(scope_ref=facts['scope_ref'],canonical_vector_ref=vr,prepare_argv=prepare,validate_argv_prefix=validate_prefix,validation_requires_actual_ready_pin=True,qualification_ceiling=scope['qualification_ceiling'],formal_case_accepted_delta=0))
    print(json.dumps(dict(canonical_vector_ref=vr,prepare_argv=prepare,validate_argv_prefix=validate_prefix,scope_ref=facts['scope_ref'],checkpoint_ref=refs[0],ownership_ref=refs[1]),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
