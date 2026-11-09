"""Public signed-document and migration-binding verification; no authority actions."""
import ast,collections,datetime as dt,hashlib,json,os,re,sqlite3,struct,sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
E=Path(__file__).parent/'grant-review';E.mkdir(exist_ok=False)
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W17/W17-03/native25_actual_root_codex/20261014-current-chat/positive-replay-02';C=P/'controller';H=P/'harness'
# Reuse only the reviewed read-only utility definitions, not its execution body.
tree=ast.parse((E.parent/'check_release.py').read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'reviewed-public-utilities','exec'))
cfg=read(P/'controller.public.config.json');hc=read(P/'harness.public.config.json');fixture=read(H/'fixture.public.json')
S=C/'review-snapshot-grant-2f2d7d9948394f3981815ac86a165f48.json';s=read(S);g=read(check(s['payload_ref']));b=g['binding']
assert s['phase']=='grant' and s['sign_kind']=='pause-migration-grant' and s['job_binding_id']=='dbfaee8e699447c0addd66b8b3dd7567'
assert s['payload_ref']['sha256']=='sha256:e9315ab9b0f96ce85dfa456088449a69881dc3834833a4da77cbc3a23d562726'
assert g['schema']=='researchos.pause-schema-migration-grant.v1' and g['purpose']=='RESEARCHOS_RUNTIME_PAUSE_SCHEMA24_TO25_V1' and g['stage']=='APPLY_ORIGINAL'
assert len(bytes.fromhex(g['nonce']))==32
start=dt.datetime.fromisoformat(g['issued_utc'].replace('Z','+00:00'));end=dt.datetime.fromisoformat(g['expires_utc'].replace('Z','+00:00'))
assert (end-start).total_seconds()==240
assert b['plan_id']=='schema24-to25-runtime-pause-v1' and b['owner_root']=='fixture-author' and b['project_id']==fixture['project_id']
assert b['root']==fixture['root'] and b['database']==fixture['database']
assert s['measured_native_ids']=={'root':b['root_identity'],'database':b['database_identity']}
assert b['source_release_sha256']==hc['SourceBackupProgram']['sha256'] and b['target_release_sha256']==hc['ControlProgram']['sha256']
assert b['sql_sha256']=='sha256:6f3f90671170df80dcb4a8f6e8c8679f85cd03802399e821ed5478dde49e2ac0'
pre=read(E.parent/'release-review/sqlite-readonly-summary.json')
assert b['original_rows_sha256']==pre['source24']['typed_rows_sha256'] and b['source_schema_sha256']==pre['source24']['schema_sha256'] and b['target_schema_sha256']==pre['restored25']['schema_sha256']
roles={p['role']:p for p in g['pins']};assert len(roles)==len(g['pins'])==76
for p in g['pins']:check(p)
for p in s['evidence_refs']:check(p)
for name,root,n in [('source',hc['SourceReleaseRoot'],24),('target',hc['BuildRoot'],25)]:
 inv={k.removeprefix(name+'-inventory:'):v['sha256'] for k,v in roles.items() if k.startswith(name+'-inventory:')}
 assert len(inv)==n+5 and digest(canonical(inv))==b[name+'_inventory_sha256']
 for rel,sha in inv.items():assert ref(Path(root)/rel)['sha256']==sha
 assert len([p for p in inv if re.match(r'migrations/sqlite/\d{4}_',p)])==n
assert roles[b['backup']['role']]==b['backup'] and roles[b['rehearsal']['role']]==b['rehearsal']
assert {Path(v['path']).name for k,v in roles.items() if k.startswith('encrypted-backup-payload:')}=={p.name for p in Path(b['backup']['path']).parent.glob('*.enc')}
options=g['options'];rh=read(H/'rehearsal.public.json');assert options==rh['options']
assert options['upgrade']['Source']==fixture['database'] and options['upgrade']['SourceRoot']==hc['SourceReleaseRoot'] and options['upgrade']['TargetRoot']==hc['BuildRoot']
# Exact RawMessage bytes, not a reserialized mapping.
raw=Path(s['payload_ref']['path']).read_text(encoding='utf8');i=raw.index('"options":')+len('"options":');_,j=json.JSONDecoder().raw_decode(raw,i)
assert digest(raw[i:j].encode())==b['options_sha256']
public_source=Path(hc['BuildRoot'])/'internal/recoveryauthority/types.go';public_text=public_source.read_text(encoding='utf8')
issuer=re.search(r'const enrolledIssuerPublicKeyHex = "([a-f0-9]{64})"',public_text).group(1)
verifier=Ed25519PublicKey.from_public_bytes(bytes.fromhex(issuer));signatures=[]
for phase,purpose in [('release','RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1/release'),('grant',g['purpose']+'/grant')]:
 receipt=read(C/('sign-'+phase+'.receipt.json'));signed=check(receipt['signed_ref']);signedtext=signed.read_text(encoding='utf8');doc=json.loads(signedtext)
 i=signedtext.index('"payload":')+len('"payload":');_,j=json.JSONDecoder().raw_decode(signedtext,i);payloadbytes=signedtext[i:j].encode()
 assert payloadbytes==Path(check(receipt['payload_ref'])).read_bytes()
 verifier.verify(bytes.fromhex(doc['signature']),purpose.encode()+b'\0'+payloadbytes)
 result=receipt['result'];job=result['job_cleanup'];guard=receipt['source_guard_cleanup']
 assert receipt['success'] and result['actual_exit']==0 and not result['timed_out'] and result['error'] is None
 assert all(job[k] for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and job['active_processes_last_observed']==0 and not job['errors']
 assert guard['closed'] and not guard['errors'] and all(x['verified'] and x['closed'] and x['final_path_match'] for x in guard['entries'])
 assert receipt['private_path_recorded'] is False and receipt['private_key_read_by_controller'] is False
 consumed=read(C/('sign-'+phase+'.consumed.json'));approval=read(check(receipt['approval_ref']))
 assert approval['Payload']==receipt['payload_ref'] and approval['SignedDestination']==str(signed)
 signatures.append({'phase':phase,'signature_verified':True,'signed_ref':receipt['signed_ref'],'receipt_ref':ref(C/('sign-'+phase+'.receipt.json')),'signer_pid':result['owned_child_pid'],'signer_exit':0,'job_closed':True,'guard_entries_closed':len(guard['entries']),'consumed_ref':ref(C/('sign-'+phase+'.consumed.json'))})
assert g['release_sha256']==signatures[0]['signed_ref']['sha256']
report={'state':'PUBLIC_SIGNED_RELEASE_AND_GRANT_VERIFIED','snapshot_ref':ref(S),'payload_ref':s['payload_ref'],'pins_checked':len(roles),'binding_matches_independently_read_pre_migration_fixture':True,'interval_seconds':240,'public_issuer_source_ref':ref(public_source),'signatures':signatures,'key_contents_read':False,'fixture_key_read':False,'root_authority_actions':0,'formal_increment':0,'at':dt.datetime.now(dt.timezone.utc).isoformat()}
save('GRANT-report.json',report);print(json.dumps({'state':report['state'],'report_ref':ref(E/'GRANT-report.json')}))
