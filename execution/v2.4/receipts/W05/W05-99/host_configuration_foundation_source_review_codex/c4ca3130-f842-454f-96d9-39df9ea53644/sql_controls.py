import pathlib,json,subprocess,os,datetime,hashlib
M=pathlib.Path('D:/作品集/ResearchOS/research-os');W=M/'.local/worktrees/codex-w0599-host-config';R=M/'execution/v2.4/receipts/W05/W05-99/host_configuration_foundation_source_review_codex/c4ca3130-f842-454f-96d9-39df9ea53644'
extra=r'''
func TestIndependentFoundationDeferredHeadAndProjection(t *testing.T) {
 for _, mode := range []string{"orphan_head", "wrong_original_projection", "foreign_owner"} {
  t.Run(mode, func(t *testing.T) {
   db,_:=configurationDB(t,23,true);doc:=configurationSchema(t)
   tx,e:=db.Begin();if e!=nil{t.Fatal(e)};defer tx.Rollback()
   if mode=="orphan_head" {
    _,e=tx.Exec(`INSERT INTO host_model_config_heads(owner_host_ref,principal,current_revision,default_model_config_ref) VALUES(?,?,1,?)`,configurationFixtureOwner,configurationFixturePrincipal,"mc-"+strings.Repeat("c",32));if e!=nil{t.Fatal(e)}
    if e=tx.Commit();e==nil{t.Fatal("orphan head committed")};t.Logf("original deferred FK refusal: %v",e);return
   }
   raw,env:=configurationEnvelope(t,doc,"independent-"+mode,1)
   if _,e=reserveClientCommandIdentity(context.Background(),tx,doc,configurationFixturePrincipal,raw,env);e!=nil{t.Fatal(e)}
   r,e:=stageClientConfiguration(context.Background(),tx,doc,configurationFixtureOwner,configurationFixturePrincipal,raw,env);if e!=nil{t.Fatal(e)}
   projection:=clientConfigurationProjection(r);if mode=="wrong_original_projection" {projection["verified_at"]=Now()}
   response:=&Response{ProtocolVersion:strptr(ProtocolV2),CommandID:env.CommandID,Method:env.Method,Status:strptr("COMPLETED"),Result:projection}
   if e=configurationReceipt(tx,configurationFixturePrincipal,env,response);e!=nil{t.Fatal(e)}
   owner:=configurationFixtureOwner;if mode=="foreign_owner"{owner="host-0123456789ab"}
   if _,e=readClientConfiguration(context.Background(),tx,doc,owner,configurationFixturePrincipal,r.Ref);e==nil{t.Fatal("noncanonical authority accepted")};t.Logf("mandatory semantic read refusal: %v",e)
   if e=tx.Rollback();e!=nil{t.Fatal(e)}
   for _,table:=range []string{"host_model_config_heads","host_model_configurations","client_command_identities","idempotency"}{if configurationCount(t,db,table)!=0{t.Fatal("rollback leaked "+table)}}
  })
 }
}
'''
original=W/'internal/domain/client_configuration_test.go';overlay=R/'independent_configuration_test.go';overlay.write_bytes(original.read_bytes()+extra.encode());(R/'overlay.json').write_text(json.dumps({'Replace':{str(original):str(overlay)}}),encoding='utf-8')
go=M/'.local/tools/go1.27.1/go/bin/go.exe';env=os.environ.copy();env.update(GOTOOLCHAIN='local',GOENV='off',GOROOT=str(go.parent.parent),GOPATH=str(M/'.local/gopath'),GOCACHE=str(M/'.local/gocache'),GOPROXY='off',GOSUMDB='off')
argv=[str(go),'test','-json','-count=1','-overlay',str(R/'overlay.json'),'-run','^TestIndependentFoundationDeferredHeadAndProjection$','./internal/domain'];(R/'sql-controls.invocation.json').write_text(json.dumps({'argv':argv,'cwd':str(W),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False,indent=2),encoding='utf-8');p=subprocess.run(argv,cwd=W,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE);(R/'sql-controls.stdout.raw').write_bytes(p.stdout);(R/'sql-controls.stderr.raw').write_bytes(p.stderr);rows=[json.loads(x) for x in p.stdout.splitlines() if x.startswith(b'{')];result={'exit':p.returncode,'pass':sum(x.get('Action')=='pass' and 'Test'in x for x in rows),'fail':sum(x.get('Action')=='fail' and 'Test'in x for x in rows),'skip':sum(x.get('Action')=='skip' for x in rows),'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat()};(R/'sql-controls.result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result)
