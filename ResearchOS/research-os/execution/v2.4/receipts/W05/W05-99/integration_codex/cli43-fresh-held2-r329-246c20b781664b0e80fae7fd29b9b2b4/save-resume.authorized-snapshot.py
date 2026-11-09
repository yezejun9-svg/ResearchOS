"""Save a forward-only authorized resume snapshot without changing canonical state."""
import datetime
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).absolute().parent
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
sys.dont_write_bytecode=True
def pin(p):
    p=Path(p).absolute(); b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(Path(p).read_bytes())
def save(n,d):
    with (OUT/n).open('xb') as h:h.write((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
scope=read(OUT/'scope_registration.json')
gp=Path(scope['new_authorization_root'])/'authorization.execute.json'
grant=read(gp)
assert pin(gp)['sha256']=='55efa0fbd05a9776fa2fcf5c12f360c8846cd39695c4c0f34a9fea7813631221'
assert grant['binding']['expected_registration']==[329,157,481]
canon=[]
for row in grant['canonical_copies']:
    actual=pin(ROOT/row['canonical_path'])
    assert (actual['sha256'],actual['bytes'])==(row['ref']['sha256'],row['ref']['bytes'])
    canon.append(actual)
old=read(OUT/'RESUME.prepare.snapshot.json')
late=old['outside_fixed_cut']
assert len(late)==3
originp=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_i17_binding_revision_independent_source_review_codex/f55ac9fdfb3d4a929686b6884431f962/origin.metadata-js-parser.json'
origin=read(originp)
assert pin(originp)['sha256']=='c5f4a5b97a61e2f9cab5974ea063649fdbe1590f3aece3a30861437044dfbc7e'
assert origin['native_exit'] is None and origin['outer_exit'] is None and origin['shell_or_target_launched'] is False
late[2]={'origin':origin['id'],'ref':pin(originp),'actual_outer_exit':None,'actual_native_exit':None,'process_launched':False}
for row in late:
    actual=pin(row['ref']['path'])
    assert (actual['sha256'],actual['bytes'])==(row['ref']['sha256'],row['ref']['bytes'])
assert not any(Path(scope[k]).exists() for k in ('new_output_root','new_wrapper_root','new_export_root'))
assert not (OUT/'root-launch.intent.json').exists()
snapshot={'schema':'researchos.root-resume.authorized.v1','actor':'codex:/root',
    'snapshot_stage':'R329_REGISTERED_SEALED_AUTHORIZED_NOT_EXECUTED',
    'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'actual_registered_tuple':[329,157,481],'live_canonical_refs_equal_actual_grant_copies':canon,
    'current_head_by_actual_registration_and_grant':'a510dbef4a7e08fb5c428df44c39b133f3ffa856',
    'scope_ref':pin(OUT/'scope_registration.json'),'binding_ref':pin(OUT/'binding.json'),
    'grant_ref':pin(gp),'grant_driver_manifest_ref':pin(OUT/'grant-driver.manifest.json'),
    'run_driver_manifest_ref':pin(OUT/'registration-run-driver.manifest.json'),
    'seal_driver_manifest_ref':pin(OUT/'registration-seal-driver.manifest.json'),
    'caller_preparation_ref':pin(OUT/'root-caller-preparation.json'),
    'current_caller_ref':pin(OUT/'root-launch-once.v2.py'),
    'completion_reader_ref':pin(OUT/'close-root-launch-observation.v3.py'),
    'actual_metadata_tool_observations_ref':pin(OUT/'root-metadata.tool-observations.after-grant.json'),
    'previous_immutable_snapshot_ref':pin(OUT/'RESUME.prepare.snapshot.json'),
    'fixed_cut_ref':pin(OUT/'failure-origins.cut.json'),'fixed_cut_origins':12,
    'outside_fixed_cut':late,'known_observed_origin_count':484,
    'source_branches':{'driver18_controller_v3':'Source-only tail correction pending non-author review',
        'driver18_partial17':'NOT_RUN; resource authority/source lease/Root adapter+two actual grants OPEN',
        'I17':'b918 REQUEST R01 exact LF/body preservation and R02 genuine single-fact raw counterexamples; new source revision in progress',
        'F08_SQL24':'OPEN_NOT_ACCEPTED','Desktop15':'NOT_IMPORTED; requires qualified current43 and separate Root15-file once scope'},
    'next_action':'Wait actual narrow caller independent review, launch this new caller exactly once, retain actual tool objects and close original native/result facts, request independent qualification.',
    'preserve':old['preserve'],'completion_gate':old['completion_gate'],
    'cleanup_pending':old['cleanup_pending'],'credential_policy':old['credential_policy'],
    'formal_increment':0,'source_acceptance':False,'canonical_writes':0,
    'automatic_retry':False,'counter_reset':False}
save('RESUME.authorized.snapshot.json',snapshot)
md='# ResearchOS r329 authorized 续跑快照\n\n实际已登记 CP329 / OW157 / 481 首因；新授权已封，尚未产品 launch。另3条晚到原始首因在固定cut之外，已观察484；旧 cut、NULL、失败计数和旧scope全部保留。\n\n等待当前 caller 非作者复审后，仅本新scope/grant执行一次；产物和native结果独审前不接受 fresh43，不导入 Desktop15。所有22父任务与42正式用例未全部有效接受，目标继续。\n\n误写临时脚本仍 PENDING_POLICY_REJECTION（blocked by policy），文件保留。\n'
with (OUT/'RESUME.authorized.snapshot.md').open('xb') as h:h.write(md.encode('utf-8'))
save('RESUME.authorized.snapshot.manifest.json',{'members':[pin(OUT/n) for n in ('save-resume.authorized-snapshot.py','RESUME.authorized.snapshot.json','RESUME.authorized.snapshot.md')],'self_excluded':True,'formal_increment':0})
print(json.dumps({'snapshot_ref':pin(OUT/'RESUME.authorized.snapshot.json'),'manifest_ref':pin(OUT/'RESUME.authorized.snapshot.manifest.json'),'canonical_refs':canon},ensure_ascii=False))
