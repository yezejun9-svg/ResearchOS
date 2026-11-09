import json,hashlib,ast
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
O=Path(__file__).parent
P=R/'execution/v2.4/receipts/W13/W13-03'
REG=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-72ff32d0d24a42c4a8effd849d54f882'
UID='72ff32d0d24a42c4a8effd849d54f882'
refs=[];checks=[]
def pin(p):
 p=Path(p); b=p.read_bytes(); return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p,sha=None):
 p=Path(p);r=pin(p)
 if sha is not None:assert r['sha256']==sha,(str(p),'SHA mismatch')
 refs.append(r);return json.loads(p.read_bytes())
def verify(r):
 p=Path(r['path']);p=p if p.is_absolute() else R/p
 q=pin(p);assert q['sha256']==r['sha256'] and q['bytes']==r['bytes'];refs.append(q);return p
def save(name,v):
 with (O/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
s=read(REG/'scope_registration.json','230f84674dfdce85f8e29b3a70bab8c8d0b5045ace1c6119c97c7474fa8a6e90')
resume=read(P/'desktop58_root_registration_grant_terminal_closure_codex'/UID/'RESUME.actual-grant.closed.launch-pending.json','c8fe42dd2f2978d03f76e7ca0a9bde1e3f7d68f3eaf6f4f835a53a43908f60bb')
obs=read(P/'desktop58_root_registration_grant_terminal_closure_codex'/UID/'tool-observations.registration-seal-grant.closed.original.json')
grant=read(P/'desktop58_finite_authorization_codex'/UID/'authorization.execute.json','fbf5be877065122136a07c004000a1a0f06a196ebe351bd47c406d13472db5ba')
mfs=[]
for path,sha,count in [
 (REG/'manifest.json','a300db91476f72caac011281fee3345098c412046d417caf12207e491a7243fa',128),
 (P/'desktop58_finite_authorization_codex'/UID/'manifest.json','879e5055fdda5f26441aaf6263de1d04afa1c568fbfac321ee7cf0c25c5cd582',35),
 (P/'desktop58_finite_grant_preflight_codex'/UID/'manifest.json','f47df4d545d8d91008d0fd4b497c12141185d11759141df260f9bfd4c2031b78',32)]:
 m=read(path,sha);assert m['count']==len(m['entries'])==count and m['excluded_only_self'] is True
 mfs.append(dict(ref=pin(path),entries=count,member_bytes_rehashed_in_this_precheck=False))
for key in ['controller_ref','launcher_ref','fixture_evaluator_ref']:
 path=verify(s[key]);ast.parse(path.read_bytes(),filename=str(path))
ro=read(verify(s['roster_ref']));ar=read(verify(s['alias_roster_ref']))
assert len(ro['leaves'])==162 and len(ro['regressions'])==7 and len(ro['go_units'])==3 and len(ar['rows'])==20
assert s['source_commit']=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'
for k,v in dict(node_cases=169,Go_top_cases=3,native_top_command_cap=176,loopback_HTTP_max=390,offscreen_Electron_controls=2,installed_visible_GUI_calls=0,SDK_model_external_paid_calls=0,inner_seconds=7200,outer_seconds=7500,builder_seconds=1800,process_cap=2048,active_job_processes=16,image_cap=64,cleanup_seconds=5,controller_evidence_reserve_seconds=60,launcher_evidence_reserve_seconds=60).items():assert s[k]==v,k
# Current canonical refs are taken from the closed Root snapshot, not any in-flight executor.
assert resume['canonical_actual']==[335,163,580]
canon=resume['canonical_refs']
assert isinstance(canon,list) and len(canon)==4
for x in canon:verify(x)
matrix=[
 {'id':'ROOT_TERMINAL','required':'Original launch input/initial/polls/terminal, actual nullable caller/launcher exits, complete raw refs, aggregate member manifest, first/secondary errors; correlate same once-only UUID.', 'status':'PENDING_CLOSED_ROOT_REFS'},
 {'id':'SOURCE_BUILD','required':'New e2 current639 Gitblob export; full alias instrumentation reverse; exact nine builder operations all0; actual package graph fields/modules/WORK/testmain/importcfg/archives/buildInputDigest/three fresh EXEs and buildinfo; before/after vectors and runtime provenance.', 'status':'PENDING_CLOSED_EXECUTOR'},
 {'id':'GO3','required':'Single go3 invocation with three exact frozen selectors PASS, no FAIL/SKIP, native0 and debug tree complete. Do not count this as the full Go suite.', 'selectors':ro['go_units'],'status':'PENDING_CLOSED_EXECUTOR'},
 {'id':'NODE169','required':'162 exact leaves +7 regression programs/leaf selectors in frozen order; every real native/raw assertion and per-case result. 170 controller rows includes one grouped Go3 row, not 172 Node leaves.', 'status':'PENDING_CLOSED_EXECUTOR'},
 {'id':'OWNED_WINDOWS','required':'Every top invocation request/result/raw, PID and full 100ns creation integers, CREATE/EXIT generations, actual hFile image/module pre/post pins, unknown/rejected events, Job idle, handles closed/remaining0, cleanup errors[], no forced termination or timeout hidden as native0.', 'status':'PENDING_CLOSED_EXECUTOR'},
 {'id':'TRANSPORT','required':'Every observer PID unique and sequence contiguous, request IDs scoped perPID; receive/body/write-end ordinals/finish/close, no orphan/duplicate/prematureclose. Actual raw byte SHA and original harness rows; perleaf caps and total <=390. Preserve socket_bytes/automatic headers/client-outbound UNKNOWN fields.', 'status':'PENDING_CLOSED_EXECUTOR'},
 {'id':'ALIASES','required':'20 exact allocations/run UUID/ordinal/root, 15 potential image paths from frozen scope, actual admissions only authorized case and checked before debug continue, expected CREATE counts; no invented unknown identities.', 'status':'PENDING_CLOSED_EXECUTOR'},
 {'id':'RENDERER','required':'Two actual offscreen Electron controls with original renderer facts, raw HTTP and exit/stdout/stderr closure. Installed visibleGUI/NVDA/real-user shell remain OPEN.', 'status':'PENDING_CLOSED_EXECUTOR'},
 {'id':'BOUNDS_FINAL','required':'Actual <=176 topcommands,7200inner/7500outer plus reserves,2048process/16active/64images/cleanup5; exact final source/canonical vectors and firstcause; all evidence finalization deadlines. Caller OS lifecycle remains false.', 'status':'PENDING_CLOSED_EXECUTOR'},
 {'id':'ACCEPTANCE','required':'Only bounded current58 Desktop169+Go3 evidence may qualify after independent closure; W13-03 formal ownership is separate. Whole58 suite, parent acceptance, source acceptance, GUI, SDK/model, formal42 remain unaccepted.', 'status':'OPEN_SEPARATE_ACCEPTANCE'}
]
save('acceptance-matrix.json',{'schema':'researchos.desktop58-actual-result-review-matrix.v1','reviewer':'codex:/root/w05_merge_review','source_commit':s['source_commit'],'scope_ref':pin(REG/'scope_registration.json'),'go_selectors':ro['go_units'],'expected_controller_rows':170,'node_cases':169,'go_top_cases':3,'matrix':matrix,'inflight_outputs_read':False})
save('report.json',{'schema':'researchos.desktop58-prequalification-readonly-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'ACTUAL_RESULT_REVIEW_PRECONDITIONS_MAPPED_FINAL_RESULT_PENDING','requested_changes':[],'current_canonical_snapshot':[335,163,580],'manifest_shapes':mfs,'input_refs':refs,'matrix_ref':pin(O/'acceptance-matrix.json'),'qualification_issued':False,'actual_result_review_completed':False,'inflight_outputs_read':False,'candidate_execution_count':0,'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'limitations':['Only closed scope/grant/metadata and pinned source contracts read. Manifest shapes/pins checked; all listed member bytes not rehashed here.','No current Desktop runtime result has been inspected or accepted.','Root snapshot absent-output fields are prelaunch historical facts; no present absence assertion.','Prior CLI2 qualified bounded2 is prerequisite only; no Desktop result inherited.']})
print(json.dumps({'report_ref':pin(O/'report.json'),'matrix_ref':pin(O/'acceptance-matrix.json'),'input_refs_count':len(refs),'new_failures':0},ensure_ascii=False))

