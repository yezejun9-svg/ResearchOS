from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-host-configuration-handler')
def edit(name,fn):
 p=R/name;s=p.read_text(encoding='utf8');s=fn(s);p.write_text(s,encoding='utf8',newline='\r\n')
def once(s,a,b):assert s.count(a)==1,a;s=s.replace(a,b);return s
def direct(s,needle,var='env'):
 return once(s,needle, '\t'+var+' = handlerDecode(t,'+var+')\n'+needle)
def atomic(s):
 s=once(s,'type rejectingClientPort struct{}','type rejectingClientPort struct { calls, inserted int }')
 s=s.replace('(rejectingClientPort)', '(p *rejectingClientPort)')
 s=once(s,'\treturn Fail(503, "MODEL_UNAVAILABLE", "fixture refusal after an intermediate write")','\tp.calls++\n\tif err := tx.QueryRowContext(ctx,"SELECT count(*) FROM rejected_command_probe").Scan(&p.inserted); err != nil { return err }\n\treturn Fail(503, "MODEL_UNAVAILABLE", "fixture refusal after an intermediate write")')
 a=s.index('\tb := WorkspaceBinding');z=s.index('\tfor attempt :=',a)
 s=s[:a]+''' svc,sid,_ := handlerTypedSession(t,f,"atomic-client")
 port:=&rejectingClientPort{}
 svc.SessionRuntime=port
 env:=handlerDecode(t,&Envelope{ProtocolVersion:strptr(ProtocolV2),CommandID:strptr(ID()),ClientID:strptr("atomic-client"),ProjectID:&f.project,SessionID:&sid,ExpectedRevision:revPtr(1),WriterEpoch:revPtr(1),Method:strptr("session.send"),Payload:Bytes(Object{"text":"reject after write","attachment_artifact_ids":Empty(),"delivery":"NORMAL"})})
'''+s[z:]
 s=once(s,'\tvar count int','\tif port.calls != 1 || port.inserted != 1 { t.Fatalf("rejection did not reach actual intermediate write: calls=%d inserted=%d",port.calls,port.inserted) }\n\tvar count int')
 return s
edit('internal/domain/client_protocol_atomic_test.go',atomic)
def controls(s):
 s=s.replace('svc.Execute(context.Background(), tx, env, f.owner)','svc.Execute(context.Background(), tx, handlerDecode(t,env), f.owner)')
 return s
edit('internal/domain/client_protocol_control_windows_test.go',controls)
def transcript(s):
 a=s.index('\tdoc, sid := clientHistoryDoc');z=s.index('\tsourceTx(t, f.db,',a)
 s=s[:a]+''' service,sid,_ := handlerTypedSession(t,f,"mixed-client")
 doc:=service.Doc
'''+s[z:]
 s=once(s,'\treturn svc, env','\tsvc.ConfigurationAuthority=handlerMetadataFixture{f.owner}\n\treturn svc, handlerDecode(t,env)')
 if 'time.' not in s:s=s.replace('\n\t"time"','')
 return s
edit('internal/domain/client_transcript_test.go',transcript)
edit('internal/domain/client_workspace_test.go',lambda s:once(s,'\tvar res *Response\n\tvar replay bool','\tenv=handlerDecode(t,env)\n\tvar res *Response\n\tvar replay bool'))
edit('internal/domain/runtime_tool_integration_windows_test.go',lambda s:once(s,'\tvar reply *Response\n\tsourceTx','\tenv=handlerDecode(t,env)\n\tvar reply *Response\n\tsourceTx'))
edit('internal/domain/runtime_model_windows_test.go',lambda s:once(s,'svc.Execute(context.Background(), tx, env, r.f.owner)','svc.Execute(context.Background(), tx, handlerDecode(t,env), r.f.owner)'))
edit('internal/domain/runtime_permission_windows_test.go',lambda s:once(s,'service.Execute(context.Background(), tx, stale, f.owner)','service.Execute(context.Background(), tx, handlerDecode(t,stale), f.owner)'))
edit('internal/domain/client_command_queue_test.go',lambda s:once(s,'svc.Execute(context.Background(), tx, env, f.owner)','svc.Execute(context.Background(), tx, handlerDecode(t,env), f.owner)'))
edit('internal/domain/client_configuration_test.go',lambda s:once(s,'''// The new private primitives do not change the existing public envelope gate.
	hostRaw, _ := configurationEnvelope(t, doc, "public-unwired", 1)
	if _, e = DecodeEnvelope(hostRaw); e == nil {
		t.Fatal("public host configure unexpectedly wired")
	}''','''// Valid default scope is decoded; trusted Host authority is checked by Execute.
	hostRaw, _ := configurationEnvelope(t, doc, "public-unwired", 1)
	if _, e = DecodeEnvelope(hostRaw); e != nil {
		t.Fatalf("public default configure decode: %v",e)
	}'''))
