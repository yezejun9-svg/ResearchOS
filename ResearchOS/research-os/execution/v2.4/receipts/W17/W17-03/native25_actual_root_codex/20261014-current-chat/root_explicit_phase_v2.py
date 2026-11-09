"""Root invokes this only after reviewing the exact snapshot and inspection.

Per invocation: one explicitly selected phase, one sign, verify actual signed
bytes/exit/closure, one separate publish. Never selects or approves a next phase.
"""
import datetime,hashlib,json,subprocess,sys
from pathlib import Path
def read(p):return json.loads(p.read_text(encoding='utf8'))
def ref(p):return {'path':str(p),'sha256':'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
assert len(sys.argv)==4
sp=Path(sys.argv[1]).resolve(); expected=sys.argv[2]; phase=sys.argv[3]
assert phase in ['release','grant'] and ref(sp)['sha256']=='sha256:'+expected
E=sp.parent.parent; assert sp.parent.name=='controller' and E.parent==Path(__file__).parent
assert ref(E/'root_concrete_operation.py')['sha256']=='sha256:5e469c5bbe6534a9c9c51f36b9775a56df7dbbbff46ea69bd4e5ba2964efaffa'
s=read(sp); assert s['phase']==phase
inspection=read(E/('root-'+phase+'-inspection.json'))
assert inspection['snapshot_ref']==ref(sp) and inspection['payload_ref']==s['payload_ref']
assert inspection['formal_increment']==0 and not inspection['private_credentials_read']
assert inspection['all_original_typed_tables_equal'] if phase=='release' else inspection['all_binding_fields_match']
payload=Path(s['payload_ref']['path']); assert ref(payload)==s['payload_ref']
a={'Schema':'researchos.root-native-concrete-approval.v1','Action':'SIGN_EXACT_REVIEWED_PUBLIC_PAYLOAD','ConfigSHA256':s['config_ref']['sha256'],'Snapshot':ref(sp),'Payload':s['payload_ref'],'SignedDestination':s['signed_destination'],'SignKind':s['sign_kind']}
sign=E/('root-sign-'+phase+'.approval.json');publish=E/('root-publish-'+phase+'.approval.json')
assert not sign.exists() and not publish.exists()
started=datetime.datetime.now(datetime.timezone.utc).isoformat();new(sign,a)
subprocess.run([sys.executable,'-B','-X','utf8',str(E/'root_concrete_operation.py'),'sign',str(sign)],check=True)
rp=E/('controller/sign-'+phase+'.receipt.json');r=read(rp);signed=Path(r['signed_ref']['path']);raw=signed.read_bytes();j=json.loads(raw)
assert r['phase']==phase and r['payload_ref']==s['payload_ref'] and r['result']['actual_exit']==0
assert r['result']['job_cleanup']['job_idle_confirmed'] and r['result']['job_cleanup']['handles_closed'] and r['source_guard_cleanup']['closed']
assert r['success'] and r['error_type'] is None and r['result']['error'] is None and not r['result']['timed_out']
jc=r['result']['job_cleanup']
assert jc['active_processes_last_observed']==0 and jc['primary_exit_confirmed'] and not jc['errors'] and not r['source_guard_cleanup']['errors']
assert r['config_ref']==s['config_ref'] and r['sign_kind']==s['sign_kind'] and signed==Path(s['signed_destination'])
assert ref(signed)==r['signed_ref'] and len(bytes.fromhex(j['signature']))==64
assert raw[raw.index(b'{',raw.index(b'"payload"')):raw.rindex(b',"signature"')]==payload.read_bytes()
assert j['payload']==read(payload)
new(E/('root-'+phase+'-signed-byte-inspection.json'),{'started':started,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_ref':ref(Path(__file__).resolve()),'snapshot_ref':ref(sp),'signed_ref':ref(signed),'signing_receipt_ref':ref(rp),'actual_exit':0,'exact_payload_bytes':True,'signature_bytes':64,'signer_job_closed':True,'formal_increment':0})
a.update(Action='PUBLISH_REVIEWED_SIGNED_DOCUMENT',SignedDocument=ref(signed),SigningReceipt=ref(rp));new(publish,a)
subprocess.run([sys.executable,'-B','-X','utf8',str(E/'root_concrete_operation.py'),'publish',str(publish)],check=True)
print(json.dumps({'phase':phase,'explicit_snapshot_ref':ref(sp),'signed_ref':ref(signed),'actual_signed_bytes_checked_by_root':True,'published':True,'no_next_phase_selected':True,'formal_increment':0}))
