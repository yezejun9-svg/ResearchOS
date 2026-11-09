import pathlib,json,hashlib,subprocess,datetime,difflib,re
M=pathlib.Path.cwd();D=M/'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_source_review_codex/3f5dab4d0b1147dcaf2997fe9ba217ab';WT=M/'.local/worktrees/codex-w0599-session-list-proof-r312'
sha=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):return {'path':p.relative_to(M).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def put(name,value):
 p=D/name
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2)
 return p
inputs=json.loads((D/'inputs.before.json').read_text(encoding='utf-8'))
extra=['execution/v2.4/receipts/W05/W05-99/session_list_identity_closedcopy_cause_review_codex/18ceca998ff94984aa58fb304e081453/scope_proposal.json','execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_harness_v4_review_codex/f9a69f9f8122497b9ad037dc3f8c3e4e/review.json','execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-exact1-r312/source_before.json']
for i,name in enumerate(extra):
 p=M/name;b=p.read_bytes();dest=D/('extra-'+str(i)+'-'+p.name);dest.write_bytes(b);inputs.append({'absolute_path':str(p),'sha256':sha(b),'bytes':len(b),'snapshot':dest.relative_to(M).as_posix()})
b=(D/'base22752-api.stdout.raw').read_bytes();old=(D/'base534-api.stdout.raw').read_bytes();cur=(D/'02-v2_sessions_test.go').read_bytes();marker=b'// Only the host binding port is a fixture.';protected=b[b.index(marker):];start=cur.index(marker);suffix=b'func TestSessionListHTTPOriginalContextIdentity(t *testing.T) {'
assert len(protected)==14633 and sha(protected)=='c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1';assert cur[start:start+len(protected)]==protected
pre=cur[:cur.index(b'// readonlyCopyOpen')];opre=old[:old.index(b'func (f *sessionListFixture) closeEvidence')]
assert pre.replace(b'\t"net/url"\n',b'')==opre+b'\n'
assert old[old.index(suffix):]==cur[cur.index(suffix):]
assert (D/'base534-domain.stdout.raw').read_bytes()==(D/'03-client_protocol_sessions.go').read_bytes()
owned=cur[cur.index(b'// readonlyCopyOpen'):cur.index(suffix)]
assert b'os.Remove' not in owned and b'os.Rename' not in owned
call_sites=[m.start() for m in re.finditer(rb'readonlyCopyOpen\(',cur)];assert len(call_sites)==2
names=re.search(rb'names := \[\]string\{([^\n]+)\}',cur[cur.index(suffix):]).group(1);names=re.findall(rb'"([^"]+)"',names);assert len(names)==14
edits=[{'tag':tag,'old_lines':[i+1,j],'current_lines':[k+1,l]} for tag,i,j,k,l in difflib.SequenceMatcher(None,old.splitlines(keepends=True),cur.splitlines(keepends=True),autojunk=False).get_opcodes() if tag!='equal']
audit={'base534':'534857db99fa5e694987f877af74c322eaa2a0b3','base22752':'22752a6a41732c8c158d7d7e1b8932ec958f8cb8','current_API_SHA256':sha(cur),'current_domain_SHA256':sha((D/'03-client_protocol_sessions.go').read_bytes()),'protected_body':{'bytes':len(protected),'sha256':sha(protected),'current_start_byte_zero_based':start,'exact_equal':True},'prefix_delta':'exactly net/url import plus one LF separator immediately before new helper','original14_suffix':{'original_sha256':sha(old[old.index(suffix):]),'current_sha256':sha(cur[cur.index(suffix):]),'exact_equal':True,'names':[x.decode() for x in names]},'original_capture_and_save_helpers_unchanged':True,'domain_equals_base534':True,'no_sidecar_delete_or_move_in_owned_region':True,'readonlyCopyOpen_sites':{'declaration':1,'call':1,'argument':'closedPath = filepath.Join(f.dir, "closed.sqlite")'},'diff_hunks':edits}
put('audit.json',audit)
checks=[
 ('S01','Ownership and protected original bytes','PASS_STATIC','Only net/url import, a separator, new readonlyCopyOpen and closeEvidence differ. Original14633 body and entire original14 case suffix remain exact.', '02-v2_sessions_test.go',762,881),
 ('S02','Original DB closed before copy','PASS_STATIC','Server.Close precedes open row capture, db.Close errors return, original sidecar Lstat requires both absent before ReadFile/copy. No immutable open targets f.dbPath.','02-v2_sessions_test.go',790,853),
 ('S03','Exclusive byte copy','PASS_STATIC','Unchanged sessionListSave uses O_CREATE|O_EXCL|O_WRONLY; writes original closed DB bytes with checked write and successful close. No reuse or delete.', '02-v2_sessions_test.go',354,369),
 ('S04','Escaped read-only immutable URI','PASS_STATIC','filepath.Abs/ToSlash and url.URL.Path preserve encoded path semantics; url.Values adds mode=ro and immutable=1. Actual modernc Windows URI behavior remains for finite14 execution.', '02-v2_sessions_test.go',764,788),
 ('S05','Copy-only before/after sidecars and Close','PASS_STATIC','Copy sidecars checked immediately before opening and after Close; query failures still trigger deferred Close and sidecar recording; Ping failure attempts Close and retains close error.', '02-v2_sessions_test.go',779,878),
 ('S06','Byte/schema/typed-row comparisons','PASS_STATIC','Original full sqlite_schema including SQL/rootpage, table_xinfo, typeof+column value multiset capture is unchanged; open-to-copy DeepEqual plus original raw-to-postread bytes.Equal remain and sidecar failure adds rejection.', '02-v2_sessions_test.go',600,703),
 ('S07','No permission/business/assertion relaxation','PASS_STATIC','Fourteen suffix byte match preserves full typed response/method/context/revision, journal original raw/hash, exact replay/conflict, per-leaf16HTTP and every row-delta assertion. No actual tests performed in this review.', '02-v2_sessions_test.go',883,1060),
 ('S08','Evidence failure propagation','PASS_STATIC','Main close/read and copy close/read errors call Error/Fatal; closed-proof.case_failed reflects t.Failed. A comparison true never clears a previous error. Original protected scanner Rows.Close behavior is unchanged.', '02-v2_sessions_test.go',831,879),
 ('S09','Copy mutation and same-user paths','LIMITATION','Lstat, ReadFile, exclusive create and SQL open are path-based separate operations. No handle-relative anti-reparse/TOCTOU claim is justified; a same-user race or later mutation is not excluded.', '02-v2_sessions_test.go',813,873),
 ('S10','Implicit rowid','LIMITATION','Capture enumerates declared table_xinfo columns; hidden implicit rowid is not separately exported unless represented by a declared column/alias. Exact copy byte equality supports physical-copy fidelity, not an independent before-close rowid invariant.', '02-v2_sessions_test.go',620,699),
 ('S11','Current execution status','NOT_VERIFIED','Root316 author execution is a separate active workflow. This review does not read running outputs, start cases, inherit earlier native0, or certify current14/source commit.', '01-scope_registration.json',1,87)
]
findings=[{'id':i,'subject':s,'status':st,'conclusion':c,'evidence_ref':ref(D/f),'locator':{'start_line':a,'end_line':b}} for i,s,st,c,f,a,b in checks]
put('findings.json',findings)
after=[]
for x in inputs:
 p=pathlib.Path(x['absolute_path']);current=sha(p.read_bytes());assert current==x['sha256'];after.append({**x,'after_sha256':current,'drift':False})
put('inputs.after.json',after)
result={'schema':'researchos.session-list-closedcopy-exact1-independent-source-review.v1','reviewer':'codex:/root/sources_parent_impl','executor':'codex:/root/command_queue_impl','decision':'READY_FOR_INDEPENDENT_FINITE14','decision_level':'STATIC_EXACT1_SOURCE_READINESS_ONLY','source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'prior_0_of_42_unchanged':True,'source_commit_verified':False,'head_observed_ref':ref(D/'current-head.stdout.raw'),'target_API_SHA256':sha(cur),'target_domain_SHA256':sha((D/'03-client_protocol_sessions.go').read_bytes()),'audit_ref':ref(D/'audit.json'),'findings_ref':ref(D/'findings.json'),'before_ref':ref(D/'inputs.before.json'),'after_ref':ref(D/'inputs.after.json'),'requested_changes':[],'mandatory_followup':['Receive exact frozen source commit and sealed v4 actual14 handoff/manifest from Root before evidence acceptance.','Independently verify each original14 native exit/leaf PASS/zero skip, actual raw request/response, closed-main SHA, original/copy sidecars, schema+typedrow multiset and original assertions.','Verify complete new compiler/generated WORK/archive/exe input closure, old failure origins, percaseHTTP<=16/total<=224 and 0 SDK/MODEL/Node/external/paid/private operations.','Keep same-user path TOCTOU and implicit-rowid qualification limitations explicit. Do not promote this helper review to domain/handler/Desktop/formal acceptance.'],'actual_execution':{'Git_read_only':6,'Go':0,'Node':0,'SQL':0,'tests':0,'HTTP':0,'MODEL':0,'private_data':0},'actual_new_native_failures':0,'tool_diagnostics':[{'chunks':['aa2a9d','09dff4','18c218','e8f9d1','4498d0','a5544e','7f30c5','40250d','97b7c4','94e7c2','ac8b4d','fb5e34','fd8069'],'actual_outer_exit':0,'note':'Successful public reads/Git/byte comparisons; no inferred failure from protected-body slice being smaller than whole file.'}],'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
put('source_review.json',result)
put('handoff.json',{'decision':result['decision'],'source_review_ref':ref(D/'source_review.json'),'audit_ref':ref(D/'audit.json'),'findings_ref':ref(D/'findings.json'),'source_acceptance':False,'formal_increment':0,'tests_run':0,'writer_scope':'this new readonly receipt namespace only'})
put('manifest.json',{'files':[ref(p) for p in sorted(D.rglob('*')) if p.is_file()],'self_excluded':True})
print(json.dumps({k:ref(D/k) for k in ['source_review.json','audit.json','findings.json','handoff.json','manifest.json']},ensure_ascii=False))
