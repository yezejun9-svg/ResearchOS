import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/handler38-post-integration-r322'
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
checks=json.loads((O/'checks.json').read_bytes());p=json.loads((S/'prepared_refs.json').read_bytes());copies=json.loads((O/'canonical-copies.json').read_bytes())
if checks['failed']:raise RuntimeError('Cannot seal positive review')
for original,copy in zip(p['canonical_before'],copies):
 b=(R/original['path']).read_bytes()
 if b!=(R/copy['path']).read_bytes() or hashlib.sha256(b).hexdigest()!=original['sha256']:raise RuntimeError('Canonical drift')
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review',
 'decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','requested_changes':[],
 'actual_registration_executed':False,'expected_before':[321,149,422],'expected_after':[322,150,425],
 'register_sha256':ref(S/'register.py')['sha256'],'wrapper_sha256':ref(S/'run.py')['sha256'],
 'prepared_refs_sha256':ref(S/'prepared_refs.json')['sha256'],'audit_sha256':ref(S/'audit.json')['sha256'],
 'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copies,
 'sealer_sha256':ref(S/'seal.py')['sha256'],'sealer_ref':ref(S/'seal.py'),
 'head_transition':{'canonical_before':'2cdb0d43d5a600eef13c8f1735946a9adf52d079','actual_completed_and_prepared_head':'a5d6d16ffaf129de0361470c3a1570228bd259a2','registered_after':'a5d6d16ffaf129de0361470c3a1570228bd259a2','source_writes_by_registration':0},
 'evidence':{'checks_ref':ref(O/'checks.json'),'reads_ref':ref(O/'reads.json'),'auditor_ref':ref(O/'audit.py'),'tool_chunk':'7e5c74','actual_readonly_auditor_exit':0,'checks_passed':1536,'checks_failed':0,'actual_read_files':291,'target_script_imports':0,'target_script_executions':0},
 'actual_closed_basis':{'completed_ref':p['pins']['main38_completed'],'manifest_ref':p['pins']['main38_manifest'],'source_after_ref':p['pins']['main38_source_after'],'outer_completion_ref':p['pins']['main38_outer_completion'],'manifest_members_byte_verified':179,'saved_owned_Git_invocations':56,'saved_owned_Git_native_exit0':56,'saved_FF_invocations':1,'current_source_after_hashes_verified':38,'separate_Root_launcher_native_exit':None},
 'verified_registration_conditions':[
 'Current CP321/OW149/failure422 four bytes equal prepared pins and prior321 desired/unchanged snapshots; ordered independent copies are inside this review parent.',
 'Wrapper requires exact reviewer/schema/decision/expected tuples/script hashes/canonical pins and four current copies before child launch; pinned actual Python and Git, no optimisation, -I -S -X utf8 retained.',
 'Registrar explicitly distinguishes old canonical head2cdb from actual Git/prepared a5d6, then updates only head metadata forward. Fresh runtime HEAD/status/index checks remain required.',
 'Three unique origins exactly match original per-source payloads. eeed61 nativeNULL, df6aba Python1, d6c6f9 Python1; all product nativeNULL and cases0. Two prior pending refs are linked as registered; no count reset or duplicate.',
 'Old422 failure prefix remains byte-semantically equal and only3 append to425. ST/CM and current effective formal status remain unchanged.',
 'Both desired canonical files, all originals, persistent intent and temporary bytes precede first replace. Before each replace all4 bytes+HEAD/status compare, own expected/cached bytes update after own replacement, phase failure journal preserves recovery evidence.',
 'Root integration source writer is released and state remains source-only FF closed pending fresh combined validation. CLI8/Desktop/W09 compile/test/product execution receives no new grant.',
 'Sealer requires original actual register exit0 and rawstdout/stderr pins, reviewer/script hashes, previous321 original bytes, current322 desired bytes, done hashes and all prepared refs. Output exact researchos.main38-post-integration-registration-audit.v1 binds completed_ref/manifest_ref/registered_head/actual_registration_exit.',
 'Existing outer-completion metadata is correctly labelled a transcription of tool-known fields, with separately observed Root launcher native exitNULL; this is not replaced with invented raw native output.'
 ],
 'execution_conditions':['Root executes exact reviewed run.py once with review path/hash and pinned interpreter; if current live state diverges, runtime guards must refuse.','Only after actual registration0 execute exact reviewed seal.py. No FF rerun is part of this registration.','Any partial metadata failure requires new bounded forward-only recovery against own originals/desired and unchanged external state; no reset/rollback/automatic rerun.'],
 'limitations':['This review checked registration code and the referenced closed source-only evidence. It does not substitute for the separately requested final Main38 closed-execution independent review after322 seal.','No new Git/Go/Node/SQL/HTTP/model/controller/registrar/launcher or product execution occurred during review. Runtime HEAD/status/index were read through existing sealed raw; wrapper/register will freshly query before write.','No fresh Main combined compilation/testing and no source-product/Main/wholeW05/22parent/42formal acceptance.'],
 'new_failure_origins':[],'formal_increment':0}
rr=save('review.json',review)
mf=save('manifest.json',{'entries':[ref(x) for x in sorted(O.iterdir()) if x.is_file()],'excluded':['manifest.json','handoff.json'],'product_executions':0})
h=save('handoff.json',{'decision':review['decision'],'review_ref':rr,'manifest_ref':mf,'sealer_ref':review['sealer_ref'],'actual_registration_executed':False,'new_failure_origins':[],'next':'Root once metadata-only322 registration then exact seal; later independent Main38 closed execution review, no new FF/product execution authority.'})
print(json.dumps({'review':rr,'manifest':mf,'handoff':h},ensure_ascii=True))
