package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/store"
)

type nativeOriginFixture struct{db *sql.DB;s *Service;client *ClientService;token,project,workspace,model string;proof *nativeOriginFixtureAuthority}
type nativeOriginFixtureAuthority struct{calls int;mutate func(*VerifiedNativeCreateOrigin);inject func(*sql.Tx)error}
func(p *nativeOriginFixtureAuthority) VerifyNativeCreate(_ context.Context,tx *sql.Tx,q NativeCreateProofQuery)(VerifiedNativeCreateOrigin,error){
	p.calls++;if p.inject!=nil{if e:=p.inject(tx);e!=nil{return VerifiedNativeCreateOrigin{},e}}
	now:=time.Now().UTC();expires:=now.Add(time.Minute);if q.CredentialExpiresAt.Before(expires){expires=q.CredentialExpiresAt}
	v:=VerifiedNativeCreateOrigin{WitnessRef:q.AttestationRef,WitnessSHA256:Digest([]byte("synthetic-witness")),ClientInstanceRef:"nci-"+strings.Repeat("1",32),HostInstanceID:"host-123456789abc",HostGenerationRef:Digest([]byte("synthetic-generation")),OSSubjectRef:"synthetic-os-peer",Principal:q.Principal,AuthorityRoot:q.AuthorityRoot,CredentialHash:q.CredentialHash,CommandID:q.CommandID,ClientID:q.ClientID,ProjectID:q.ProjectID,Method:q.Method,ActualRawSHA256:q.ActualRawSHA256,IssuedAt:now.Add(-time.Second),ExpiresAt:expires}
	if p.mutate!=nil{p.mutate(&v)};return v,nil
}
type nativeOriginConfigFixture struct{}
func(nativeOriginConfigFixture) ConfigurationMetadata(_ context.Context,p,_ string,c *string)(ClientConfigurationMetadata,error){if p!="native-owner"||c!=nil{return ClientConfigurationMetadata{},Fail(403,"FORBIDDEN","synthetic metadata")};return ClientConfigurationMetadata{OwnerHost:"host-123456789abc",Principal:p},nil}

func newNativeOriginFixture(t *testing.T,addon bool)*nativeOriginFixture{
	t.Helper();ctx:=context.Background();db,e:=store.Open(filepath.Join(t.TempDir(),"native-origin.sqlite"));if e!=nil{t.Fatal(e)};t.Cleanup(func(){db.Close()})
	if e=store.Bootstrap(ctx,db,"../../migrations/sqlite/0001_bootstrap.sql");e!=nil{t.Fatal(e)}
	s,e:=New(db,"../../spec/v2.0/contracts","../../migrations/sqlite/0002_domain.sql");if e!=nil{t.Fatal(e)}
	raw,e:=os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql");if e!=nil{t.Fatal(e)};if _,e=db.Exec(string(raw));e!=nil{t.Fatal(e)};if e=EnsureClientSessionFence(ctx,db);e!=nil{t.Fatal(e)}
	if addon{if e=InstallClientNativeWriterOriginPreparedSchema(ctx,db);e!=nil{t.Fatal(e)}}
	if e=s.ProvisionPrincipal(ctx,Principal{ID:"native-owner",Roles:[]string{"OWNER"},CanCreateProject:true});e!=nil{t.Fatal(e)}
	token,e:=s.IssueCredential(ctx,"native-owner",10*time.Minute);if e!=nil{t.Fatal(e)}
	profile:=Object{"name":"Native origin fixture","intent":"One fresh session","facts":Empty(),"accepted_scope":[]any{"fixture"},"constraints":Empty(),"source_configs":Empty(),"source_document_refs":Empty(),"read_snapshot_ids":Empty()}
	req:=httptest.NewRequest("POST","/v1/projects",bytes.NewReader(Bytes(profile)));req.Header.Set("Authorization","Bearer "+token);req.Header.Set("Idempotency-Key",ID());r:=httptest.NewRecorder();s.Handler().ServeHTTP(r,req)
	if r.Code!=201{t.Fatalf("project fixture: %d %s",r.Code,r.Body.Bytes())};var project Object;if e=json.Unmarshal(r.Body.Bytes(),&project);e!=nil{t.Fatal(e)}
	proto,e:=os.ReadFile("../../internal/api/contracts/client.protocol.schema.json");if e!=nil{t.Fatal(e)};external,e:=os.ReadFile("../../internal/api/contracts/domain.schema.json");if e!=nil{t.Fatal(e)};doc,e:=LoadSchemaWithExternals(proto,map[string][]byte{"domain.schema.json":external});if e!=nil{t.Fatal(e)}
	f:=&nativeOriginFixture{db:db,s:s,token:token,project:Str(project,"project_id"),workspace:"native-workspace",proof:&nativeOriginFixtureAuthority{}}
	f.client=&ClientService{Doc:doc,Domain:s,ConfigurationAuthority:nativeOriginConfigFixture{},NativeCreateAuthority:f.proof,Host:ClientHostInfo{InstanceID:"host-123456789abc",CoreBuildID:"fixture-native-core",OperatingMode:"LOCAL_USER_HOST",LeaseTTL:90*time.Second}}
	binding:=WorkspaceBinding{AuthorizedRef:f.workspace,DisplayName:"fixture",DisplayPath:"fixture",RealPath:t.TempDir(),Access:"READ_ONLY",ProjectID:&f.project,Revision:1,Status:WorkspaceActive,PrincipalID:"native-owner",ClientID:"native-client",HostPrincipalRef:"synthetic-os-peer",CreatedAt:Now()}
	if _,e=db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`,KindWorkspaceBinding,f.workspace,string(Bytes(binding)));e!=nil{t.Fatal(e)}
	configure:=f.env(t,"host.configure","configure-native",Object{"config_revision":1,"provider_id":"fixture-provider","base_url":"https://fixture.invalid/v1","model_id":"fixture-model","credential_ref":nil});configure.ProjectID=nil
	// Re-decode after editing fields to preserve the exact original-envelope gate.
	configure=f.decode(t,Bytes(configure));res,e:=f.execute(t,configure,"");if e!=nil||deref(res.Status)!="COMPLETED"{t.Fatalf("configure fixture: %v %s",e,Bytes(res))};f.model=Str(res.Result,"model_config_ref")
	return f
}
func(f *nativeOriginFixture) decode(t *testing.T,raw []byte)*Envelope{t.Helper();e,err:=DecodeEnvelope(raw);if err!=nil{t.Fatal(err)};return e}
func(f *nativeOriginFixture) env(t *testing.T,method,key string,payload Object)*Envelope{return f.decode(t,Bytes(Object{"protocol_version":ProtocolV2,"command_id":key,"client_id":"native-client","project_id":f.project,"session_id":nil,"expected_revision":nil,"writer_epoch":nil,"method":method,"payload":payload}))}
func(f *nativeOriginFixture) create(t *testing.T,key string)*Envelope{return f.env(t,"session.create",key,Object{"workspace_ref":f.workspace,"model_config_ref":f.model,"title":"fresh native fixture"})}
func(f *nativeOriginFixture) execute(t *testing.T,env *Envelope,ref string)(*Response,error){
	t.Helper();ctx:=context.Background();tx,e:=f.db.BeginTx(ctx,nil);if e!=nil{t.Fatal(e)};defer tx.Rollback()
	ctx,p,e:=AuthenticateCommandTx(ctx,tx,f.token,f.client);if e!=nil{return nil,e};if ref!=""{ctx,e=WithNativeCreateAttestationReference(ctx,ref);if e!=nil{return nil,e}}
	r,_,e:=f.client.Execute(ctx,tx,env,p.ID);if e!=nil{return r,e};if e=tx.Commit();e!=nil{return nil,e};return r,nil
}
func fixtureNativeRef()string{return "natt-"+strings.Repeat("1",64)}
func nativeFixtureCount(t *testing.T,db *sql.DB,query string,args ...any)int{t.Helper();var n int;if e:=db.QueryRow(query,args...).Scan(&n);e!=nil{t.Fatal(e)};return n}

func TestNativeWriterOriginCreateReplayAndColdHistory(t *testing.T){
	f:=newNativeOriginFixture(t,true);env:=f.create(t,"native-create-one");res,e:=f.execute(t,env,fixtureNativeRef());if e!=nil||deref(res.Status)!="COMPLETED"{t.Fatalf("create: %v %s",e,Bytes(res))}
	if nativeFixtureCount(t,f.db,`SELECT count(*) FROM client_native_writer_origins`)!=1||f.proof.calls!=1{t.Fatal("missing or duplicate origin")}
	root,e:=ValidateClientNativeWriterOriginHistory(context.Background(),f.db,f.client.Doc);if e!=nil||root==""{t.Fatal(e)}
	f.client.NativeCreateAuthority=nil // Cold/live-map absence is not historical corruption.
	again,e:=f.execute(t,env,"");if e!=nil||!bytes.Equal(Bytes(res),Bytes(again)){t.Fatalf("sealed replay: %v",e)}
	if f.proof.calls!=1||nativeFixtureCount(t,f.db,`SELECT count(*) FROM client_native_writer_origins`)!=1{t.Fatal("replay consumed again")}
	if _,e=f.db.Exec(`UPDATE auth_credentials SET revoked=1`);e!=nil{t.Fatal(e)}
	if _,e=ValidateClientNativeWriterOriginHistory(context.Background(),f.db,f.client.Doc);e!=nil{t.Fatal("historical validation required a live credential",e)}
	if _,e=f.execute(t,env,"");e==nil{t.Fatal("replay bypassed current bearer authentication")}
}

func TestNativeWriterOriginRejectsMismatchedAuthority(t *testing.T){
	cases:=[]struct{name string;change func(*VerifiedNativeCreateOrigin)}{
		{"wire",func(v *VerifiedNativeCreateOrigin){v.ActualRawSHA256=Digest([]byte("different bytes"))}},
		{"credential",func(v *VerifiedNativeCreateOrigin){v.CredentialHash=Digest([]byte("other credential"))}},
		{"principal",func(v *VerifiedNativeCreateOrigin){v.Principal="other-owner"}},
		{"root",func(v *VerifiedNativeCreateOrigin){v.AuthorityRoot="other-root"}},
		{"client",func(v *VerifiedNativeCreateOrigin){v.ClientID="other-client"}},
		{"project",func(v *VerifiedNativeCreateOrigin){v.ProjectID="other-project"}},
		{"command",func(v *VerifiedNativeCreateOrigin){v.CommandID="other-command"}},
		{"expired",func(v *VerifiedNativeCreateOrigin){v.ExpiresAt=time.Now().Add(-time.Second)}},
	}
	for _,tc:=range cases{t.Run(tc.name,func(t *testing.T){f:=newNativeOriginFixture(t,true);f.proof.mutate=tc.change;env:=f.create(t,"native-bad");r,e:=f.execute(t,env,fixtureNativeRef());if e==nil&&deref(r.Status)=="COMPLETED"{t.Fatal("mismatched witness granted")};if nativeFixtureCount(t,f.db,`SELECT count(*) FROM client_sessions`)!=0||nativeFixtureCount(t,f.db,`SELECT count(*) FROM client_native_writer_origins`)!=0{t.Fatal("mismatch left state")}})}
}

func TestNativeWriterOriginRollbackAtCommitBoundaries(t *testing.T){
	for _,phase:=range []string{"origin-insert","marker-cas-zero","pair-check"}{t.Run(phase,func(t *testing.T){
		f:=newNativeOriginFixture(t,true)
		f.proof.inject=func(tx *sql.Tx)error{
			ddl:=`CREATE TRIGGER fixture_origin_fault BEFORE INSERT ON client_native_writer_origins BEGIN SELECT RAISE(FAIL,'injected origin insert'); END`
			if phase=="marker-cas-zero"{ddl=`CREATE TRIGGER fixture_origin_fault BEFORE UPDATE OF headers ON idempotency WHEN NEW.operation='v2:session.create' BEGIN SELECT RAISE(IGNORE); END`}
			if phase=="pair-check"{ddl=`CREATE TRIGGER fixture_origin_fault AFTER UPDATE OF headers ON idempotency WHEN NEW.operation='v2:session.create' BEGIN UPDATE client_sessions SET project_id='wrong-project' WHERE id=json_extract(NEW.body,'$.session_id'); END`}
			_,e:=tx.Exec(ddl);return e
		}
		env:=f.create(t,"native-fault");r,e:=f.execute(t,env,fixtureNativeRef());if e==nil||r!=nil{t.Fatalf("fault did not abort: %v %s",e,Bytes(r))}
		for _,query:=range []string{`SELECT count(*) FROM client_sessions`,`SELECT count(*) FROM client_native_writer_origins`,`SELECT count(*) FROM client_command_identities WHERE command_id='native-fault'`,`SELECT count(*) FROM idempotency WHERE key='native-fault'`}{if nativeFixtureCount(t,f.db,query)!=0{t.Fatal("partial transaction survived",query)}}
	})}
}

func TestNativeWriterOriginForeignLeaseBarrierAndLegacy(t *testing.T){
	for _,lease:=range []string{"live","expired","null"}{t.Run(lease,func(t *testing.T){
		f:=newNativeOriginFixture(t,true);created,e:=f.execute(t,f.create(t,"native-owner-create"),fixtureNativeRef());if e!=nil{t.Fatal(e)};sid:=deref(created.SessionID)
		if lease!="live"{var value any;if lease=="expired"{value=time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano)};if _,e=f.db.Exec(`UPDATE client_sessions SET lease_expires_at=? WHERE id=?`,value,sid);e!=nil{t.Fatal(e)}}
		env:=f.env(t,"session.attach","foreign-attach",Object{"request_write_owner":true,"after_sequence":0});env.SessionID=&sid;env.ExpectedRevision=int64ptr(1);env.ClientID=strptr("foreign-client");env=f.decode(t,Bytes(env));r,e:=f.execute(t,env,"")
		if e!=nil||deref(r.Status)!="REJECTED"||r.Error==nil||r.Error.Code!="WRITER_BUSY"{t.Fatalf("foreign writer entered: %v %s",e,Bytes(r))}
		var owner string;var epoch int64;if e=f.db.QueryRow(`SELECT writer_client_id,writer_epoch FROM client_sessions WHERE id=?`,sid).Scan(&owner,&epoch);e!=nil{t.Fatal(e)};if owner!="native-client"||epoch!=1{t.Fatal("foreign handoff occurred")}
	})}
	f:=newNativeOriginFixture(t,true);r,e:=f.execute(t,f.create(t,"ordinary-legacy-create"),"");if e!=nil||deref(r.Status)!="COMPLETED"{t.Fatal(e)};if nativeFixtureCount(t,f.db,`SELECT count(*) FROM client_native_writer_origins`)!=0{t.Fatal("legacy label was backfilled")}
}

func TestNativeWriterOriginRejectedCreateRemainsLegacyReceipt(t *testing.T){
	f:=newNativeOriginFixture(t,true)
	env:=f.env(t,"session.create","native-rejected",Object{"workspace_ref":f.workspace,"model_config_ref":"missing-model","title":"reject this finite request"})
	r,e:=f.execute(t,env,fixtureNativeRef());if e!=nil||deref(r.Status)!="REJECTED"{t.Fatalf("ordinary rejection changed: %v %s",e,Bytes(r))}
	if nativeFixtureCount(t,f.db,`SELECT count(*) FROM client_native_writer_origins`)!=0||nativeFixtureCount(t,f.db,`SELECT count(*) FROM idempotency WHERE key='native-rejected' AND json_extract(headers,'$.schema')=?`,clientCommandHeaderSchema)!=1{t.Fatal("rejection gained an origin/marker or lost its original receipt")}
}
