import json,hashlib,difflib
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).resolve().parent
O=N.parent/'c09-a0163b5c32ed44f7aca7730f3834e009'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
scopePath=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/c09-correction-and-progress-r304/c09_corrected_execution_scope.json'
assert sha(scopePath)=='2705297ee492cf72a6d01e70612fa45f05b9bcc6499abb159e0ec6f37d9fb02a'
scope=json.loads(scopePath.read_bytes());assert N==R/scope['new_receipt_namespace']
snap=N/'approved-originals';snap.mkdir(exist_ok=False)
refs=[(scopePath,'scope.json'),(R/'execution/v2.4/checkpoint.json','checkpoint.json'),(R/'execution/v2.4/path_ownership.json','path_ownership.json')]
assert sha(refs[1][0])=='bfe7c0acbe956d6ef36a9b5f30563d8e90e5147fafafb29c51a89b02a05de51b'
assert sha(refs[2][0])=='c93b5f247c44fb2cfa8625befbc8f66ad827d3cacc7f2aa6b06b204a1a0ff514'
assert json.loads(refs[1][0].read_bytes())['revision']==304
assert json.loads(refs[2][0].read_bytes())['revision']==132
for key in ['nonauthor_correction_review_ref','constructor_supplement_ref','previous_failed_cohort']:
 record=scope[key];p=R/record['path'];assert sha(p)==record['sha256'];refs.append((p,key+'.json'))
for p,name in refs:
 with (snap/name).open('xb') as f:f.write(p.read_bytes())
work=R/scope['new_work_namespace'];work.mkdir(parents=True,exist_ok=False)
old=O/'overlay/handler_configuration_independent_review_test.go';assert sha(old)=='e95403f5cebaa2b7cfd466779e3d964cca7fbd66cb489641c5b39af0bf7dbbde'
raw=old.read_text(encoding='utf8');original=raw
def change(a,b):
 global raw
 assert raw.count(a)==1,(a[:100],raw.count(a));raw=raw.replace(a,b,1)
change('\traw := Bytes(env)\n\tdecoded, e := DecodeEnvelope(raw)', '\traw := Bytes(env)\n\tindependentC09Write(t, dir, label+".request.json", Object{"raw_request_base64": base64.StdEncoding.EncodeToString(raw), "raw_sha256": Digest(raw), "raw_bytes": len(raw)})\n\tdecoded, e := DecodeEnvelope(raw)')
change('''	r, replay, e := s.Execute(context.Background(), tx, decoded, principal)
	if e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {''','''	r, replay, e := s.Execute(context.Background(), tx, decoded, principal)
	if e != nil { t.Fatal(e) }
	if r == nil || deref(r.CommandID) != deref(env.CommandID) || deref(r.Method) != deref(env.Method) || deref(r.SessionID) != deref(env.SessionID) { t.Fatal("response original identity mismatch") }
	var generic map[string]any
	if e = json.Unmarshal(Bytes(r), &generic); e != nil { t.Fatal(e) }
	if e = s.Doc.ValidateDef("CommandResponse", generic); e != nil { t.Fatal(e) }
	if e = ValidateResultAgainstMethod(deref(env.Method), r, s.Doc); e != nil { t.Fatal(e) }
	if e = tx.Commit(); e != nil {''')
oldAttach='''			attach := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client, ProjectID: &project, SessionID: &sid, ExpectedRevision: &rev, WriterEpoch: &epoch, Method: strptr("session.attach"), Payload: Bytes(Object{"request_write_owner": true})}'''
newAttach='''			watermark, e := Num(sess, "event_watermark")
			if e != nil || watermark < 0 { t.Fatalf("invalid original watermark: %v", e) }
			attach := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client, ProjectID: &project, SessionID: &sid, ExpectedRevision: &rev, WriterEpoch: nil, Method: strptr("session.attach"), Payload: Bytes(Object{"after_sequence": watermark, "request_write_owner": true})}'''
change(oldAttach,newAttach)
anchor='''			attached := independentC09StateRead(t, db)
			independentC09Write(t, dir, "03.post-attach.fullrows.json", attached)
			tx, e := db.Begin()'''
replacement='''			attached := independentC09StateRead(t, db)
			independentC09Write(t, dir, "03.post-attach.fullrows.json", attached)
			// Actual caller-transaction takeover is ACK only. Prove its real
			// lease/journal and immutable replay; never manufacture COMPLETED.
			if ar.Revision == nil || *ar.Revision != rev+2 || ar.ErrorCode != nil || ar.Error != nil { t.Fatal("attach typed ACK fields") }
			accepted, e := time.Parse(time.RFC3339Nano, Str(ar.Result, "accepted_at")); if e != nil { t.Fatal(e) }
			returnedSequence, e := Num(ar.Result, "after_sequence"); if e != nil || returnedSequence != watermark+1 || ar.Result["operation_id"] != "op-"+deref(attach.CommandID) || ar.Result["related_resource_ref"] != nil { t.Fatal("attach PendingResult") }
			independentC09Exact(t, before, attached, map[string]bool{"client_sessions":true,"outbox":true,"idempotency":true,"client_command_identities":true})
			if len(before["client_sessions"]) != len(attached["client_sessions"]) { t.Fatal("attach changed Session count") }
			for i, old := range before["client_sessions"] {
				want := Object{}; for k,v := range old { want[k]=v }
				if old["id"] == sid { want["writer_epoch"]=epoch+1; want["revision"]=rev+2; want["event_watermark"]=watermark+1; want["lease_expires_at"]=actualAttach["lease_expires_at"]; want["updated_at"]=actualAttach["updated_at"] }
				if !reflect.DeepEqual(want,attached["client_sessions"][i]) { t.Fatal("unexpected actual attach Session field mutation") }
			}
			newAttachEvent := independentC09Append(t,before["outbox"],attached["outbox"],1)[0]
			event, e := Decode([]byte(Str(newAttachEvent,"body"))); if e != nil { t.Fatal(e) }
			if event["kind"] != "CLIENT_HANDOFF" || event["command_id"] != deref(attach.CommandID) || event["session_id"] != sid || event["protocol_version"] != ProtocolV2 || event["core_build_id"] != clientService.Host.CoreBuildID || newAttachEvent["project"] != project { t.Fatal("actual handoff event identity") }
			eventSequence,e := Num(event,"sequence"); if e != nil || eventSequence != returnedSequence { t.Fatal("handoff event sequence") }
			decodedEvent,e := DecodeEvent([]byte(Str(newAttachEvent,"body"))); if e != nil { t.Fatal(e) }; if e=ValidateEventPayload(doc,decodedEvent);e!=nil{t.Fatal(e)}
			handoff := independentC09Object(t,event,"payload"); writer := independentC09Object(t,handoff,"writer")
			previousEpoch,e:=Num(handoff,"previous_epoch");if e!=nil{t.Fatal(e)};newEpoch,e:=Num(writer,"epoch");if e!=nil{t.Fatal(e)}
			if handoff["previous_client_id"] != client || handoff["target_client_id"] != client || previousEpoch != epoch || writer["client_id"] != client || newEpoch != epoch+1 || handoff["effective_at"] != ar.Result["accepted_at"] || writer["expires_at"] != actualAttach["lease_expires_at"] { t.Fatal("actual handoff ownership facts") }
			lease,e:=time.Parse(time.RFC3339Nano,Str(writer,"expires_at"));if e!=nil||!lease.Equal(accepted.Add(clientService.Host.LeaseTTL)){t.Fatal("actual handoff configured TTL")}
			attachJournal:=independentC09Append(t,before["idempotency"],attached["idempotency"],1)[0];attachIdentity:=independentC09Append(t,before["client_command_identities"],attached["client_command_identities"],1)[0]
			if attachJournal["key"] != deref(attach.CommandID) || attachIdentity["command_id"] != deref(attach.CommandID) || attachJournal["principal"] != principal || attachIdentity["principal"] != principal || attachJournal["project"] != project || attachIdentity["project"] != project || attachJournal["operation"] != "v2:session.attach" || attachIdentity["operation"] != "v2:session.attach" || attachIdentity["method"] != "session.attach" || attachJournal["request_hash"] != attachIdentity["request_hash"] || Str(attachJournal,"body") != string(Bytes(ar)) { t.Fatal("attach sole original response/identity") }
			attachHeader,known,e:=readClientCommandEnvelope(doc,Str(attachJournal,"headers"));if e!=nil||!known||attachHeader.hash!=attachJournal["request_hash"]||!bytes.Equal(attachHeader.env.originalRaw,Bytes(attach)){t.Fatal("attach private original bytes/hash")}
			attachMetadataCalls:=metadata.calls
			attachReplay,isAttachReplay:=independentC09Command(t,db,clientService,principal,attach,dir,"03a.exact-attach-replay")
			afterAttachReplay:=independentC09StateRead(t,db);independentC09Write(t,dir,"03b.post-attach-replay.fullrows.json",afterAttachReplay)
			if !isAttachReplay || deref(attachReplay.Status)!="ACKNOWLEDGED" || !bytes.Equal(Bytes(attachReplay),Bytes(ar)) || metadata.calls!=attachMetadataCalls || !reflect.DeepEqual(attached,afterAttachReplay) {t.Fatal("attach replay changed ACK/state/metadata")}
			tx, e := db.Begin()'''
change(anchor,replacement)
(N/'overlay').mkdir()
physical=N/'overlay/handler_configuration_independent_review_test.go'
with physical.open('xb') as f:f.write(raw.encode('utf8'))
with (N/'overlay.pre-gofmt.diff').open('xb') as f:f.write(''.join(difflib.unified_diff(original.splitlines(True),raw.splitlines(True),fromfile=str(old),tofile=str(physical))).encode('utf8'))
driver=(O/'prepare_compile_run.py').read_text(encoding='utf8')
oldSpec="save('execution_spec.json',{'candidate'"
idx=driver.index(oldSpec);end=driver.index('\ncode=invoke(\'gofmt\'',idx)
driver=driver[:idx]+'''save('execution_spec.json',{'candidate':'22752a6a41732c8c158d7d7e1b8932ec958f8cb8','case_order':names,'selector':'^TestIndependentHandlerConfigurationC09$','scope_sha256':'2705297ee492cf72a6d01e70612fa45f05b9bcc6499abb159e0ec6f37d9fb02a','scope_original':str(N/'approved-originals/scope.json'),'AE_cohort_separate':str(A),'old_failed_cohort_preserved':str(N.parent/'c09-a0163b5c32ed44f7aca7730f3834e009'),'changes':['takeover writer_epoch=null','after_sequence actual nonnegative current watermark','exact raw persisted before Decode','strict ACK PendingResult/actual lease/journal/sole identity and exact ACK replay all-row equality'],'first_unexpected_stop':True,'C09_models_HTTP_Node_worker_paid':0,'formal_increment':0})'''+driver[end:]
needle="paths.update([physical,mapping,N/'execution_spec.json'"
at=driver.index(needle)
driver=driver[:at]+"paths.update(p for p in (N/'approved-originals').rglob('*') if p.is_file());paths.update([N/'prepare_corrected.py',N/'overlay.pre-gofmt.diff',N/'preparation.json'])\n"+driver[at:]
assert driver.count("binary=N/'domain-c09.test.exe'")==1
driver=driver.replace("binary=N/'domain-c09.test.exe'","binary=N/'domain-c09-corrected.test.exe'",1)
with (N/'prepare_compile_run.py').open('xb') as f:f.write(driver.encode('utf8'))
save(N/'preparation.json',{'scope_sha256':sha(scopePath),'candidate':scope['candidate'],'old_overlay_sha256':sha(old),'new_overlay_before_gofmt_sha256':sha(physical),'physical':str(physical),'work_namespace':str(work),'read_current_metadata_only_at_initial_preparation':True,'production_writes':0,'tests_executed':0,'case_executions':0,'changed_functions':['independentC09Command','TestIndependentHandlerConfigurationC09 attach construction/immediate assertions'],'original_injection_and_configure_assertions_preserved':True})
print(json.dumps({'prepared_namespace':str(N),'scope_sha256':sha(scopePath),'cases_executed':0}))
