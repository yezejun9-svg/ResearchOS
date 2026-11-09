"""Finite Source-only preparation. Does not call actual Canon/product commands."""
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import types

N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
W=R/'execution/v2.4/receipts/W09/W09-99'
writer=N/'register_cp368.source.py'
m=types.ModuleType('cp368_source_writer');m.__file__=str(writer);sys.modules[m.__name__]=m
exec(compile(writer.read_bytes(),str(writer),'exec'),m.__dict__)

def fixed(path,sha,size):
    ref=dict(path=str(Path(path).resolve(strict=True)),sha256=sha,bytes=size);m.read(ref);return ref
def hp(n,sha,size):return fixed(n/'HDF.json',sha,size)

def main():
    a=B/'restored21_session_runtime_caller_v3_source_codex/r21v3caller-20261009-01'
    ar=B/'restored21_runtime_v3_caller_independent_review_codex/review-1a11fa1'
    d=W/'main_c19_adoption_decision_supplement_codex/adoptsupp-01a11fea'
    reject=W/'main_c19_root_producer_independent_review_codex/review-1a11fa1'
    sh=hp(a,'72df2851c4c8fe5f8db37c283dad9cfcaba0921554606f4b3d0b51f0c6e856fd',4821);s=m.load(sh)
    rh=hp(ar,'64f3bd714e1bb1811961f12eba2ecf9c238558e5efafd1a51ce8892aba590550',2608);review=m.load(rh)
    ah=hp(d,'c9a2924d4c6fb8656b1beebbfa8b1de03e12af9310c4cd8e718656dbf13c81a8',4288);adopt_h=m.load(ah)
    xh=hp(reject,'caa970f551f80b647fb31b5453910c9aa9cc75d3ec21a0e07f81a4a6797f0c29',2371);rejected=m.load(xh)
    contract=m.load(s['contract_ref']);guidance=m.load(review['root_execution_guidance_ref'])
    scope=dict(schema='researchos.root-restored21-v3-development-scope.v1',status='ROOT_AUTHORIZED_SINGLE_BOUNDED_RESTORED21_DEVELOPMENT_RUN',issued_by=m.ACTOR,executor=m.ACTOR,source_handoff_ref=sh,source_manifest_ref=s['manifest_ref'],source_review_handoff_ref=rh,source_review_manifest_ref=review['manifest_ref'],root_execution_guidance_ref=review['root_execution_guidance_ref'],contract_ref=s['contract_ref'],prepare_caller_ref=m.pin(a/'prepare_root_actual.py'),validator_ref=m.pin(a/'validate_root_actual.py'),exact_source_roster_ref=m.normalized(contract['exact_source_roster']),historical_W05_parent_owner='codex:/root/w1102_impl',maximum_unique_tests=13,maximum_actual_attempts=1,qualification_ceiling=guidance['max_qualification'],formal_dispatcher=False,formal_acceptance=False,Main_adoption=False,production_DB_writes=False,external_model_calls=False,automatic_retry=False,parent_acceptance=False,formal_case_accepted_delta=0)
    for k in ('worktree','environment','isolation_output','validation_output'):scope[k]=contract[k]
    sr=m.save('scope-registration.root.json',scope)
    diag=fixed(W/'w09_c19_main_root_producer_source_codex/mainc19p-1a11fbc/failure952.original-tool-io.json','a7b5854ed63594d0362bbe902f7101f7ce92c7b8005b479c60e95619df19a935',31394)
    adr=adopt_h['actual_decision_ref'];ad=m.load(adr)
    canon=[dict(path=str(p.resolve(strict=True)),sha256=sha,bytes=size) for p,(sha,size) in zip(m.CANON,m.BEFORE)]
    for ref in canon:m.read(ref)
    facts=dict(schema='researchos.root-cp368-w05-development-registration-facts.v1',issued_by=m.ACTOR,created_utc=datetime.now(timezone.utc).isoformat(),canonical_refs=canon,scope_ref=sr,formal_acceptance=False,adoption_review_handoff_ref=ah,adoption_review_manifest_ref=adopt_h['manifest_ref'],adoption_review_decision_ref=adr,adoption_outcome_ref=ad['adoption_outcome_ref'],W09_producer_request_changes_handoff_ref=xh,W09_producer_request_changes_manifest_ref=rejected['manifest_ref'],pairs=[dict(handoff_ref=h,manifest_ref=o['manifest_ref']) for h,o in ((sh,s),(rh,review),(ah,adopt_h),(xh,rejected))],input_refs=[s['contract_ref'],scope['prepare_caller_ref'],scope['validator_ref'],scope['exact_source_roster_ref'],scope['root_execution_guidance_ref'],adr,*ad['source21'],*ad['final_target_refs']],diagnostic=dict(ordinal=952,origin_ref=diag,actual_outer_exit=1,actual_python_exit=None,actual_native_exit=None,description='Read-only Main-native Source inspection used one nonexistent guessed seal_source.py path; outer shell exit1, Python/Go/Native/model unexecuted NULL. Exact original tool call and result preserved; later successful export is a distinct event.',origin_selector='original tool invocation b2f026',exit_qualification='Only original outer shell exit1 was observed; Python/Go/Native/model were not invoked, remain NULL.'),checkpoint_note='CP368: retain CP367/Main7 independent actual acceptance as Source adoption only, record original952 exactly once, register Root bounded W05 restored21 v3 development tests. Main C19 producer Source v1 rejected for cleanup repair; no Main Native/dispatcher/formal/parent acceptance.')
    # Resolve canonical owner/worker from exact scope values without self-referential hashes.
    owner={k:copy.deepcopy(scope[k]) for k in ('source_handoff_ref','source_manifest_ref','source_review_handoff_ref','source_review_manifest_ref','worktree','environment','isolation_output','validation_output')}
    owner.update(owner=m.ACTOR,current_source_writer=None,state=m.STATE,scope_ref=sr,formal_case_accepted_delta=0,parent_acceptance=False)
    facts.update(owner=owner,worker=dict(step_id='W05-99',slice_id=m.SLICE,owner=m.ACTOR,state=m.STATE,scope_ref=sr,source_handoff_ref=sh,source_review_handoff_ref=rh,worktree=scope['worktree']))
    fr=m.save('checkpoint.execution.facts.json',facts)
    live=dict(schema='researchos.root-postseal-live-diagnostic-context.v1',issued_by=m.ACTOR,created_utc=datetime.now(timezone.utc).isoformat(),source_cutoff=dict(highest_ordinal=952,next_failure_ordinal=953),next_original_failure_ordinal=954,pending=[dict(ordinal=953,origin_ref=dict(path=str((B/'checkpoint_r368_w05_independent_review_codex/cp368r-01a11fea/failure953.original-tool-io.json').resolve(strict=True)),sha256='5526df6a460b1541612533ba44dca285bb756180568d1cc5766efb13d11f0015',bytes=1375),description='Original independent Source read c3b898 guessed one missing filename; outer1, Python/Native/model NULL; original evidence preserved.')])
    lr=m.save('live-context.source-check.root.json',live)
    proof=m.execute('check',fr,lr)
    controls=[]
    old_c,old_o=[m.load(v) for v in canon[:2]]
    for label,field,value in [('reject counter reset','next_original_failure_ordinal',952),('reject boolean live','next_original_failure_ordinal',True),('reject skipped pending','pending',[dict(ordinal=954,origin_ref=diag,description='negative control')])]:
        bad=copy.deepcopy(live);bad[field]=value
        try:m.validate_live(bad)
        except ValueError:controls.append(dict(control=label,rejected=True))
        else:raise AssertionError(label)
    for label,change in [('preserve two parents',lambda c,o:c['work_in_progress'].update(construction_active_parents=['W05','W09','W10'])),('preserve historical W05 owner',lambda c,o:o['card_path_bindings']['W05-99'].update(owner=m.ACTOR)),('reject duplicate execution worker',lambda c,o:c['workers'].append(copy.deepcopy(facts['worker'])))]:
        c,o=copy.deepcopy(old_c),copy.deepcopy(old_o);change(c,o)
        try:m.transform(c,o,facts,fr,c,o,live)
        except ValueError:controls.append(dict(control=label,rejected=True))
        else:raise AssertionError(label)
    controls_ref=m.save('source-controls.json',dict(controls=controls,product_commands_run=0,canonical_mutations=0,formal_case_accepted_delta=0))
    members=[m.pin(p) for p in (writer,Path(__file__).resolve(),N/'scope-registration.root.json',N/'checkpoint.execution.facts.json',N/'live-context.source-check.root.json',N/'source_guard.cleanup.check.json',N/'canonical_pair.check.json',N/'source-controls.json',N/'v1-to-v2.diff',N/'source-byte-inverse.json')]
    mf=m.save('MF.json',dict(schema='researchos.root-cp368-registration-source-manifest.v1',members=members))
    hdf=m.save('HDF.json',dict(schema='researchos.root-cp368-registration-source-handoff.v1',actor_id=m.ACTOR,status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW_NO_CANON_WRITE',manifest_ref=mf,facts_ref=fr,scope_ref=sr,writer_ref=m.pin(writer),source_proof_ref=proof,controls_ref=controls_ref,formal_acceptance=False,formal_case_accepted_delta=0,registered_original_cutoff=952,next_at_cutoff=953,actual_executed=False,all_handles_closed=True))
    print(json.dumps(dict(handoff_ref=hdf,manifest_ref=mf,facts_ref=fr,scope_ref=sr,proof_ref=proof,source_controls=len(controls),actual_executed=False),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
