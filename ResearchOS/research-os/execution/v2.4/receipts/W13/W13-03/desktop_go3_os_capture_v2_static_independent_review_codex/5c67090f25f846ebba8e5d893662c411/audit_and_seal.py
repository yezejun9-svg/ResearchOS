import ast,hashlib,json,datetime
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
O=R/'execution/v2.4/receipts/W13/W13-03/desktop_go3_os_capture_v2_static_independent_review_codex/5c67090f25f846ebba8e5d893662c411'
N=R/'execution/v2.4/receipts/W13/W13-03/desktop_go3_os_capture_revision_codex/01fc890602df43b89935fdbef4424137'
checks=[]; reads={}
def ref(p):
 p=Path(p); b=p.read_bytes(); v=dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)); reads[str(p)]=v; return v
def check(label,ok):
 checks.append(dict(check=label,passed=bool(ok)))
 if not ok: raise RuntimeError(label)
def write(name,obj):
 b=(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
 with (O/name).open('xb') as f:f.write(b)
 return ref(O/name)
def doc(p):
 ref(p);return json.loads(Path(p).read_bytes())
pins={'manifest.json':'cd68a08d19558ae746207e2125320631d96cb3999120da600fbea9f94bfb6958','handoff.json':'42329afffb3a693d2a13a8334d95e16a42dbb95f018c5bd360361bf0e6da698b','spec.v2.json':'858463e5dd1f5570c372de42476c65042d5e3d675085317711fe377323a4db76','run_go3.v2.final.py':'fe61a605425d17f0ece750e1b843aa3fd88f3d8939db1791055ec0f9125a26e1','windows_debug_owned_process.v2.py':'b60c8826fb13fc24947965579492b6f4aad76d7d95588fdfe2525daa1941f725'}
for name,h in pins.items():check('supplied pin '+name,ref(N/name)['sha256']==h)
mf=doc(N/'manifest.json');check('manifest16',len(mf['entries'])==16)
for row in mf['entries']:
 a=ref(row['path']);check('manifest member '+Path(row['path']).name,a['sha256']==row['sha256'] and a['bytes']==row['bytes'])
for name in ['run_go3.v2.final.py','windows_debug_owned_process.v2.py']:
 raw=(N/name).read_bytes(); tree=ast.parse(raw);check('AST '+name,True);check('no assert '+name,not any(isinstance(x,ast.Assert) for x in ast.walk(tree)))
 with (O/(name+'.original')).open('xb') as f:f.write(raw)
spec=doc(N/'spec.v2.json'); original=doc(N/'original-spec.json')
check('same selectors',spec['selectors']==original['selectors'])
check('same executable',spec['test_exe']==original['test_exe'])
check('same original input vector',spec['input_vector_ref']==original['input_vector_ref'])
check('same expected pass records',spec['expected_pass_records']==original['expected_pass_records'])
for key in ['runner_ref','debug_helper_ref','outer_helper_ref','python_ref','runtime_catalog_ref']:
 x=spec[key];a=ref(x['path']);check('spec ref '+key,a['sha256']==x['sha256'] and a['bytes']==x['bytes'])
guard=doc(N/'original-input-guard.json')
for x in guard['files']:
 row=x['original'];a=ref(row['path']);check('original preserved '+Path(row['path']).name,a['sha256']==row['sha256'] and a['bytes']==row['bytes'])
old=R/'execution/v2.4/receipts/W13/W13-03/desktop_go3_os_capture_static_independent_review_codex/ddbf0097d4bb4b3e89d39bd6aa3b7fe5/review.json'
check('old review pin',ref(old)['sha256']=='d54dae30faea145d14d21ccc4471668f6164c83b04083ead3bfc9e749a5ebf44')
for name,h in pins.items():check('after pin '+name,ref(N/name)['sha256']==h)
audit=write('read-audit.json',dict(schema='researchos.readonly-source-audit.v1',checks=checks,inputs=list(reads.values()),runtime_catalog_members_not_rehashed=True,product_or_helper_execution=False,imports_of_candidate=False,new_nonzero_origins=[]))
review=write('review.json',dict(schema='researchos.desktop-go3-os-capture-static-independent-review.v1',reviewer='codex:/root/w05_merge_review',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),decision='READY_FOR_ROOT_REGISTERED_GO3_DEBUG_PROOF_ONCE',requested_changes=[],runner_sha256=pins['run_go3.v2.final.py'],helper_sha256=pins['windows_debug_owned_process.v2.py'],spec_sha256=pins['spec.v2.json'],proposal_manifest_ref=ref(N/'manifest.json'),prior_review_ref=ref(old),audit_ref=audit,resolved_findings=[{'id':'GO3-01','evidence':'run_go3.v2.final.py:136-286','conclusion':'Exclusive phase marker; first failure saved before independent best-effort after checks; helper result and closed stdio persisted in finally; nullable native exit retained. Pre-output failure remains Root launch receipt responsibility.'},{'id':'GO3-02','evidence':'run_go3.v2.final.py:92-132,157-196,245-266','conclusion':'Required isolated/no_site/UTF8/no optimization; no pyc writes; exact helper bytes compiled into ModuleType; actual Python/controller/grant/spec/authority refs and source/archive/executable inputs included in before/after closure. Runtime catalog excludes unknown/site inputs; additions after before cause qualification failure.'},{'id':'GO3-03','evidence':'windows_debug_owned_process.v2.py:101-104,245-266,459-510; outer runner timeout600','conclusion':'Capture hashes check150s deadline per chunk, termination observation5s, evidence finalization25s. An exclusive outer Job bounds blocked inner/debugged Go to600s plus5s cleanup observation. This does not bound Root shell preflight or outer post-receipt IO, and does not imply Python lifecycle module proof.'},{'id':'GO3-04','evidence':'windows_debug_owned_process.v2.py:266-379,488-506; runner complete and debug guards','conclusion':'Pinned CREATE image, ordered unique primary CREATE/EXIT, held-process exit agreement, total Job processes exactly1, event/file bounds, first-chance primary loader-breakpoint rule and unsupported-event refusal. All existing Job success flags required; pending debug events continued in finally; actual ABI/handle behavior remains a future native observation.'}],mandatory_execution_conditions=['Root must issue a real immutable once grant after registration, binding exact reviewed spec/runner/helpers/Python, nonempty actual sealed registration and independent-review refs. The NOT_AUTHORIZED template cannot be used.','Root must preserve actual outer launch argv/raw/nullable exit including bootstrap failures; run outer once with pinned Python -I -S -X utf8; never manually start --inner.','All8577 source/compiler/WORK/archive inputs and actual runtime subset must pass before and after; current testexe must match983f41306992f162854901cc1ade5b3fc3901ca1894c15f4e1e05e92fd6d210f.','Exactly3 selectors/64 expected PASS records including parent/63 leaves; one debugged process; HTTP/Node/SDK/model/paid0. First unexpected stops, no automatic rerun or new selector.','Any debug handle, event, module-file, cleanup, timeout or runtime qualification failure is retained as failed/incomplete evidence even if native test exit0.'],limitations=['Static bytes/AST review only; helper/DLL/controller/Go/Node/SQL/HTTP/model not executed.','Original Go3 actual0 with missing OS observation remains historical and unqualified by this review. New debug-mode run is a distinct condition, not retroactive evidence.','Python runtime observation is before/after point-in-time, not absence-of-transient-load proof. Go debug event capture also requires actual successful execution.','Catalog1211 constituent bytes not rehashed in this static review; catalog itself pinned and future actual loaded subset checked. Full8577 not rehashed again here.','600+5 covers owned inner/debugged process boundary, not end-to-end Root shell or arbitrary outer evidence filesystem delays.'],source_acceptance=False,Main_integration=False,formal_increment=0,actual_execution_grant=False,future_cases='NOT_RUN',new_failure_origins=[]))
manifest=write('manifest.json',dict(entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file()],self_excluded=True))
handoff=write('handoff.json',dict(decision='READY_FOR_ROOT_REGISTERED_GO3_DEBUG_PROOF_ONCE',review_ref=review,manifest_ref=manifest,actual_execution=False,source_acceptance=False,formal_increment=0,new_failure_origins=[]))
print(json.dumps(dict(review=review,manifest=manifest,handoff=handoff,checks=len(checks)),ensure_ascii=False))