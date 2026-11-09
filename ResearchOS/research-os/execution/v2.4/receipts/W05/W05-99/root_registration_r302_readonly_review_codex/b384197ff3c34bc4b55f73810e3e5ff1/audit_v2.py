from pathlib import Path
import json,hashlib,subprocess,ast,datetime
R=Path.cwd();S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/handler-resource-and-diagnostics-r302';N=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
def save(n,o):(N/n).write_bytes((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def ref(p):b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':H(b),'bytes':len(b)}
pins={'register.py':'6b5d004b5e046ec6ca7de40bf9d283317c48ca13f4b635f96c4f5edb9caedf6e','prepared_refs.json':'15756f25757480950491b508ebf7f6983f6ddf41f06f86beb1539c7284505b42','audit.json':'08bfa673a21a32c8ec4f0b79b888c22210999bea35be6b5dea9f7c7cb8aa69d5','run.py':'ddf1e1e895037105b3b191122db92576153fdd9aec8d559cd00f78c6bcf3309b'};blobs={}
for name,sha in pins.items():
 raw=(S/name).read_bytes();assert H(raw)==sha;blobs[name]=raw;(N/(name+'.byte-exact')).write_bytes(raw)
for name in ['register.py','run.py']:ast.parse(blobs[name].decode('utf-8-sig'))
p=json.loads(blobs['prepared_refs.json']);a=json.loads(blobs['audit.json']);before={x:(R/'execution/v2.4'/x).read_bytes() for x in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']}
for name,raw in before.items():(N/(name+'.before')).write_bytes(raw)
read_checks=[]
for row in p['all_verified_refs']:
 path=R/row['path'];actual=ref(path);read_checks.append({'ref':row,'actual':actual,'match':actual['sha256']==row['sha256'] and actual['bytes']==row['bytes']})
state_checks=[]
for row in p['canonical_before']:
 name=Path(row['path']).name;raw=before[name];state_checks.append({'ref':row,'match':H(raw)==row['sha256'] and len(raw)==row['bytes']})
cp=json.loads(before['checkpoint.json']);ow=json.loads(before['path_ownership.json']);keys={x.get('origin_key') for x in cp['failure_counters']};origins=[{'origin_key':x['origin_key'],'already_registered':x['origin_key'] in keys,'evidence_ref':x['evidence_ref']} for x in a['origins']]
# Match all manifest listed references to already independently hashed prepared refs.
by_path={x['ref']['path']:x for x in read_checks};manifest_checks=[]
for item in a['manifests']:
 path=R/item['manifest_ref']['path'];obj=json.loads(path.read_bytes());entries=obj if isinstance(obj,list) else obj.get('files',obj.get('entries',[]));bad=[]
 for row in entries:
  rel=row.get('path',row.get('relative_path','')); direct=rel;relative=(path.parent/rel).relative_to(R).as_posix() if not Path(rel).is_absolute() else ''
  found=by_path.get(direct) or by_path.get(relative)
  if not found or found['ref']['sha256']!=row.get('sha256') or not found['match']:bad.append({'path':rel,'cause':'not covered by frozen independently verified ref'})
 manifest_checks.append({'manifest':item['manifest_ref'],'listed':len(entries),'expected_count':item['verified_listed_count'],'bad':bad})
lock=json.loads((R/'execution/toolchains/locked.json').read_bytes())['tools'];tools=[{'tool':name,'path':lock[name]['path'],'actual_sha256':H(Path(lock[name]['path']).read_bytes()),'expected_sha256':lock[name]['sha256']} for name in ['python','git']]
git=lock['git']['path'];status=subprocess.check_output([git,'status','--porcelain=v1','--untracked-files=no'],cwd=R);head=subprocess.check_output([git,'rev-parse','HEAD'],cwd=R).decode().strip();(N/'git-status.before.raw').write_bytes(status)
g1=json.loads((R/p['pins']['g1_result']['path']).read_bytes());chain=cp['failure_chains']['W05-99/provider-whole9-g1-alias-preparation'];fields=['original_outer_actual_exit','original_termination_actual_exit','original_Go3_actual_exit','original_JS3_actual_exit']
canonical_after={x:H((R/'execution/v2.4'/x).read_bytes()) for x in before};unchanged=all(canonical_after[x]==H(v) for x,v in before.items());source_after={x:H((S/x).read_bytes()) for x in pins}
save('reference_audit.json',{'refs':read_checks,'count':len(read_checks),'bad':[x for x in read_checks if not x['match']],'manifest_expansion':manifest_checks})
save('state_origin_audit.json',{'expected_before':[301,129,322],'actual_before':[cp['revision'],ow['revision'],len(cp['failure_counters'])],'metadata_pins':state_checks,'metadata_before_refs':[ref(N/(x+'.before')) for x in before],'metadata_after_sha256':canonical_after,'metadata_unchanged':unchanged,'head':head,'status_sha256':H(status),'expected_status_sha256':p['git_status_sha256'],'status_rows':len(status.splitlines()),'old_deletions':sum(x[:2]==b' D' for x in status.splitlines()),'origins':origins,'proposed_after':len(cp['failure_counters'])+len(origins),'original_G1_facts':{k:g1[k] for k in fields},'G1_chain_before':chain,'excluded_pending_origins':['844373','30c440','dba1ed'],'tools':tools,'new_failed_invocations':0})
bad=any(not x['match'] for x in read_checks+state_checks) or any(x['bad'] or x['listed']!=x['expected_count'] for x in manifest_checks)
ready=not bad and unchanged and source_after==pins and len(origins)==len({x['origin_key'] for x in origins})==8 and not any(x['already_registered'] for x in origins) and [cp['revision'],ow['revision'],len(cp['failure_counters'])]==[301,129,322] and H(status)==p['git_status_sha256'] and head==p['head'] and all(x['actual_sha256']==x['expected_sha256'] for x in tools)
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' if ready else 'REQUEST_CHANGES','register_sha256':pins['register.py'],'wrapper_sha256':pins['run.py'],'prepared_refs_sha256':pins['prepared_refs.json'],'audit_sha256':pins['audit.json'],'expected_before':[301,129,322],'expected_after':[302,130,330],'actual_registration_executed':False,'canonical_writes':0,'product_execution':0,'formal_increment':0,'checks':[
 'All493 prepared refs independently hashed; five manifests listed entries independently mapped to those refs. Four canonical before bytes copied verbatim in this own namespace and matched prepared pins.',
 'Wrapper validates all four metadata pins before launch, fixed plan/spec, locked Python/Git SHA, HEAD/status; pins register and prepared refs bytes; isolates child Python with -I and optimize0 check, captures actual stdout/stderr and child exit without retry.',
 'Register validates same four before pins and all493 cached reference bytes; head and exact13row status SHA fixed. Before every replace it compares all four expected_live bytes, HEAD and exact status; after replacing updates both expected_live[path] and READS[path]=raw. Later handoff ref returns new checkpoint/ownership hashes, not stale cached original.',
 'Old322 failure array is exact prefix; eight unique original invocations add8, original archive128/outer563fb1 counted once. Pending844373/30c440/dba1ed are not imported. No failed registrar retry is authorized.',
 'Originals, both desired bytes, Git status and intent precede temp/replace; done/exception/verified refs retain phases/current hashes. Recovery is Root-only forward against own original/desired and unchanged other metadata/head/status; external edits stop, no rollback/reset.',
 'step_state/commands and current formal status unchanged. G1 child0 evidence and outer1/termination128 preserved, chain actual_failed2/same_cause1 unchanged; whole9 false. F08 SQL24, G2 product edit/execution and CLI execution leases remain absent; no new formal acceptance.',
 'Resource change is exactly previously reviewed15pathspec+12publiccompile files; frozen38 A-E+6C09 unchanged. This review does not itself execute correction or registry.'
 ],'execution_conditions':[
 'Root invokes reviewed run.py with locked Python -I and this review absolute path plus actual SHA. Preserve actual wrapper/child raw and byte-check pinned source before execution.',
 'Wrapper hashes review but does not independently parse its decision fields; Root must supply THIS positive review and honor REQUEST_CHANGES if inputs drift. This is approval of exact current Root operation, not a generic untrusted review gateway.',
 'Any exception seals phase/current bytes and stops; do not rerun register.py. Use only explicit bounded forward recovery against saved own intent if needed.'
 ],'requested_changes':[] if ready else ['See reference/state audits; do not execute until mismatches resolved.'],'read_audit_ref':ref(N/'reference_audit.json'),'state_audit_ref':ref(N/'state_origin_audit.json'),'source_after_sha256':source_after,'limitations':['Read-only source review; no fault injection, no registration, no product or SQL test executed.']}
save('review.json',review);save('manifest.json',{'files':[{'path':x.relative_to(N).as_posix(),'sha256':H(x.read_bytes()),'bytes':x.stat().st_size} for x in sorted(N.rglob('*')) if x.is_file() and x.name not in ['manifest.json','handoff.json']]});save('handoff.json',{'decision':review['decision'],'review_ref':ref(N/'review.json'),'manifest_ref':ref(N/'manifest.json'),'expected_before':[301,129,322],'expected_after':[302,130,330],'register_sha256':pins['register.py'],'wrapper_sha256':pins['run.py'],'actual_registration_executed':False});print(json.dumps({'decision':review['decision'],'reference_count':len(read_checks),'manifest_bad':[x for x in manifest_checks if x['bad']],'review':ref(N/'review.json'),'manifest':ref(N/'manifest.json'),'handoff':ref(N/'handoff.json')},ensure_ascii=True))
