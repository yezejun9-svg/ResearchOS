import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/fresh-handler38-source-integration-r321-v2'
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
checks=json.loads((O/'checks.json').read_bytes());p=json.loads((S/'prepared_refs.json').read_bytes());copies=json.loads((O/'canonical-copies.json').read_bytes())
if checks['failed']:raise RuntimeError('Cannot approve failed audit')
for original,copy in zip(p['canonical_before'],copies):
 b=(R/original['path']).read_bytes()
 if b!=(R/copy['path']).read_bytes() or hashlib.sha256(b).hexdigest()!=original['sha256']:raise RuntimeError('Canonical current mismatch')
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review',
 'decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','requested_changes':[],
 'actual_registration_executed':False,'expected_before':[320,148,417],'expected_after':[321,149,422],
 'register_sha256':ref(S/'register.py')['sha256'],'wrapper_sha256':ref(S/'run.py')['sha256'],
 'prepared_refs_sha256':ref(S/'prepared_refs.json')['sha256'],'audit_sha256':ref(S/'audit.json')['sha256'],
 'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copies,
 'sealer_ref':ref(S/'seal.py'),'sealer_sha256':ref(S/'seal.py')['sha256'],
 'scope_ref':p['pins']['scope'],'controller_review_ref':p['pins']['integration_controller_review'],
 'integration_launcher_ref':p['pins']['integration_launcher'],
 'evidence':{'checks_ref':ref(O/'checks.json'),'reads_ref':ref(O/'reads.json'),'auditor_ref':ref(O/'audit.py'),'audit_tool_chunk':'4b60c0','actual_readonly_auditor_exit':0,'checks_passed':303,'checks_failed':0,'actual_read_files':63,'target_script_imports':0,'target_script_executions':0,'native_product_executions':0},
 'verified':[
 'Actual current orderedCP/OW/ST/CM bytes equal prepared4 pins and original Root320 desired/unchanged files; exact copies reside under this review parent.',
 'Register/run/seal AST and actual byte hashes frozen. Wrapper checks review schema/identity/decision/four script-data hashes/four current metadata copies before launching pinned Python register.',
 'Only CP/OW desired JSON is constructed; ST/CM unchanged. Four originals/two desired bytes and intent persist before first replace. Every replace first compares all4 live bytes plus HEAD/status; expected_live and cached READS update only after own replacement.',
 'Five unique original tool-origin records match their exact original payloads and evidence bytes. Their actual_native_exit is [1,null,null,null,1], actual_native_product_exit null throughout. No invented product failures.',
 'Original417 prefix preserved and only5 appended to422. Sourceeeed61 and Cmddf6aba pinned separately as pending; observed lowerbound424 does not overwrite registered422.',
 'Root14 bounded list source state and Go3 DEBUG component evidence close only their declared scope; W09 source writer released with compilation/tests still NOT_RUN. No formal or wholeW05 status promotion.',
 'Root exact38 future controller/scope/launcher READY review is pinned. Registration itself performs no FF; actual seal and new exclusive grant remain mandatory.',
 'Main2cdb, 13-row status with11 original deletions and empty index checked by runtime registrar; G2 original source/HEAD/status guard retained. No product source writes in registrar.',
 'Exception phase/currentsha/intent preserved for forward-only recovery, no rollback/external overwrite/automatic rerun. Postwrite tuple/prefix/formal/STCM/HEAD/status must verify before completion receipt.',
 'Sealer verifies actual wrapper/child0, rawstdout/stderr hash, exact reviewed executable hashes, original Root320 four bytes, current desired tuple, done hashes and all prepared refs. Registration output shapes match already reviewed producer/controller authority reader.'
 ],
 'runtime_conditions':['Root must invoke this exact reviewed wrapper once with this review path and SHA under locked Python -I -S -X utf8; runtime guards remain authoritative if live state changes.','Root must use the exact seal.py pin after actual register exit0; only thereafter exact reviewed launcher.v2 may issue actual321 once grant and attempt source-only FF.','A partial canonical failure is not approval to rerun; inspect persisted original/desired/intent and obtain a new bounded forward-only recovery scope.'],
 'limitations':['Read-only review only: no registrar/wrapper/sealer/launcher/controller or Git/Go/Node/SQL/HTTP/model execution.','HEAD/status/index were not independently queried again in this narrow review; fresh runtime verification is mandatory in wrapper/registrar and remains fail-closed.','This is metadata registration review, not independent acceptance of reviewed integration execution, Main combined behavior,22parents or42formal cases.'],
 'new_failure_origins':[],'formal_increment':0}
rr=save('review.json',review)
mf=save('manifest.json',{'entries':[ref(x) for x in sorted(O.iterdir()) if x.is_file()],'excluded':['manifest.json','handoff.json'],'product_executions':0})
h=save('handoff.json',{'decision':review['decision'],'review_ref':rr,'manifest_ref':mf,'sealer_ref':review['sealer_ref'],'actual_registration_executed':False,'new_failure_origins':[],'next':'Root may execute the exact reviewed registration wrapper once, then pinned seal on actual0; integration requires its subsequent actual once grant.'})
print(json.dumps({'review':rr,'manifest':mf,'handoff':h},ensure_ascii=True))
