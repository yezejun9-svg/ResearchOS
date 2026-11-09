from pathlib import Path
import hashlib,json,re,runpy
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-native-create-core-20261104')
RECEIPT=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/core')
scope=json.loads((RECEIPT/'scope.json').read_text(encoding='utf-8-sig'))
for n,h in scope['baseline_sha256'].items():
    p=ROOT/n
    assert (not p.exists()) if h=='ABSENT_BEFORE' else hashlib.sha256(p.read_bytes()).hexdigest()==h,n
runpy.run_path(str(HERE/'generate-ddl.py'))
src=HERE/'src'
store=src/'internal/domain/client_native_writer_origin_store.go'
store.write_text(store.read_text(encoding='utf-8').replace('// GENERATED_ACCESSORS',(HERE/'store-generated.txt').read_text(encoding='utf-8')),encoding='utf-8',newline='\n')
dto=json.loads((HERE/'INTERFACE.v1.json').read_text(encoding='utf-8'))
req={'schema_version':{'const':1},'credential_value':{'type':'string','minLength':1,'maxLength':1024,'writeOnly':True},'command_id':{'type':'string','pattern':'^[A-Za-z0-9._:-]{1,64}$'},'method':{'const':'session.create'},'project_id':{'type':'string','minLength':1,'maxLength':512},'request_raw_sha256':{'type':'string','pattern':'^sha256:[0-9a-f]{64}$'},'session_id':{'const':None},'expected_revision':{'const':None},'writer_epoch':{'const':None}}
result={'schema_version':{'const':1},'attestation_ref':{'type':'string','pattern':dto['reference_pattern']},'client_instance_ref':{'type':'string','pattern':dto['connection_instance_pattern']},'host_instance_id':{'type':'string','pattern':dto['host_pattern']},'expires_at':{'type':'string','format':'date-time'}}
def obj(props):return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}
profile={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'https://researchos.local/contracts/native.client-attestation.v1.schema.json','$defs':{'NativeClientAttestRequestFrame':obj({'kind':{'const':dto['request_kind']},'client_id':{'type':'string','minLength':1,'maxLength':512},'payload':obj(req)}),'NativeClientAttestResultFrame':obj({'kind':{'const':dto['result_kind']},'payload':obj(result)})}}
p=src/'internal/host/contracts/native.client-attestation.v1.schema.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
hsrc=src/'internal/host/native_client_attestation.go'
htext=hsrc.read_text(encoding='utf-8').replace('__PROFILE_DIGEST__','sha256:'+hashlib.sha256(p.read_bytes()).hexdigest())
htext=htext.replace('\n\t"strings"','').replace('\nvar _ = strings.TrimSpace\n','\n')
htext=htext.replace('''	var req nativeCreateRequest
''','''	encoded,err:=json.Marshal(call.frame)
	if err!=nil||h.validateNativeCreateFrame(encoded)!=nil{return nil,nil,ErrFrameShape}
	var req nativeCreateRequest
''')
hsrc.write_text(htext,encoding='utf-8',newline='\n')

texts={n:(ROOT/n).read_text(encoding='utf-8') for n in scope['production_paths'] if scope['baseline_sha256'][n]!='ABSENT_BEFORE'}
def change(n,old,new,count=1):
    assert texts[n].count(old)==count,(n,old[:100],texts[n].count(old))
    texts[n]=texts[n].replace(old,new)

n='internal/host/host.go'
change(n,'\tstate      *hostState\n','\tstate      *hostState\n\tnativeCreate *nativeCreateState\n')
change(n,'\tsvc, err := domain.NewCurrentMu(', '\tif _, err = nativeCreateDocument(); err != nil { return nil, err }\n\tsvc, err := domain.NewCurrentMu(')
change(n,'bootGeneration: generation, now: now, doc: doc}', 'bootGeneration: generation, now: now, doc: doc, nativeCreate: &nativeCreateState{witnesses: map[string]nativeCreateWitness{}}}')
n='internal/host/native.go'
change(n,'\tif def, ok := nativeRequestDefs[frame.Kind]; ok {','\tif frame.Kind == KindNativeClientAttestRequest { if err := h.validateNativeCreateFrame(raw); err != nil { return nativeInvocation{}, err } }\n\tif def, ok := nativeRequestDefs[frame.Kind]; ok {')
change(n,'\tswitch frame.Kind {\n\tcase KindUserBootstrapRequest:', '\tswitch frame.Kind {\n\tcase KindNativeClientAttestRequest:\n\t\treply, undo, err = h.nativeClientAttest(context.Background(), invocation)\n\tcase KindUserBootstrapRequest:')
n='internal/host/contract.go'
change(n,'\tdef, ok := nativeResultDefs[frame.Kind]\n','\tif frame.Kind == KindNativeClientAttestResult { return validateNativeCreateResult(reply) }\n\tdef, ok := nativeResultDefs[frame.Kind]\n')
n='internal/domain/client_protocol.go'
change(n,'\tConfigurationAuthority ClientConfigurationAuthority\n','\tConfigurationAuthority ClientConfigurationAuthority\n\tNativeCreateAuthority NativeCreateAuthority\n')
change(n,'\thash, err := env.ContentHash()\n','\tif _, err := nativeOriginHistoryTx(ctx, tx, s.Doc); err != nil { return nil, false, err }\n\thash, err := env.ContentHash()\n')
change(n,'\tvar existingHash, body string\n','\tnativeOrigin, err := s.authorizeNativeCreate(ctx, tx, env, principal)\n\tif err != nil { return clientFaultForExecute(env, err) }\n\tvar existingHash, body string\n')
change(n,'\treturn res, false, nil\n','\tif err := s.recordNativeCreateOrigin(ctx, tx, env, principal, res, nativeOrigin); err != nil { return nil, false, err }\n\treturn res, false, nil\n')
change(n,'\t\tvar oldLease sql.NullString\n','\t\tif sess.writerClientID != deref(env.ClientID) { marked, err := hasNativeWriterOrigin(ctx,tx,sess.project,sess.sessionID); if err != nil { return nil,err }; if marked { return reject(sess.revision,sess.epoch,"WRITER_BUSY","Native-origin writer handoff is not supported by this pilot"),nil } }\n\t\tvar oldLease sql.NullString\n')
# Keep the existing typed rejection helper semantics without altering its signature.
texts[n]+='\nfunc clientFaultForExecute(env *Envelope, err error) (*Response,bool,error) { r,e:=clientFault(env,err); return r,false,e }\n'
n='internal/domain/client_protocol_auth.go'
texts[n]+='\nfunc NativeCreatePreparedSchemaAvailable(ctx context.Context,tx *sql.Tx)(bool,error){ if tx==nil{return false,ErrNoCredential};return nativeOriginSchemaState(ctx,tx) }\n'
n='internal/domain/client_command_identity.go'
change(n,'\thash string\n','\thash string\n\tnativeOrigin *nativeCreateOriginMarker\n')
change(n,'return clientIdentityRequest{parsed, actual}, nil','return clientIdentityRequest{env: parsed, hash: actual}, nil')
change(n,'func readClientCommandEnvelope(doc *SchemaDoc, headers string) (clientIdentityRequest, bool, error) {\n','func readClientCommandEnvelope(doc *SchemaDoc, headers string) (clientIdentityRequest, bool, error) {\n\tif strings.Contains(headers,nativeCommandHeaderSchema) || strings.Contains(headers,`"native_create_origin"`) { return readNativeMarkedCommandEnvelope(doc,headers) }\n')
change(n,'\treturn response, nil\n','\tif err = validateClientNativeReceipt(ctx,tx,doc,principal,req); err != nil { return nil,err }\n\treturn response, nil\n')
n='internal/api/v2.go'
change(n,'\tresp, replayed, err := v.svc.Execute(authContext, tx, env, principal.ID)\n','''	if refs, present := r.Header[http.CanonicalHeaderKey(domain.NativeCreateAttestationHeader)]; present {
		if len(refs)!=1 { writeTypedError(w,http.StatusBadRequest,env,"INVALID_REQUEST","one Native attestation reference required");return }
		authContext,err=domain.WithNativeCreateAttestationReference(authContext,refs[0])
		if err!=nil { writeTypedError(w,http.StatusBadRequest,env,"INVALID_REQUEST","invalid Native attestation reference");return }
	}
	resp, replayed, err := v.svc.Execute(authContext, tx, env, principal.ID)
''')
n='internal/api/server.go'
old='func HandlerWithConfigurationHost(db *sql.DB, webDir string, service *domain.Service, runtime domain.ClientSessionRuntime, instanceID string, workspace domain.WorkspaceAuthority, inventory domain.LocalInventoryScanner, configuration domain.ClientConfigurationAuthority, workspaceFiles ...domain.ClientWorkspaceFiles) http.Handler {\n'
new=old+'\treturn HandlerWithNativeCreateHost(db,webDir,service,runtime,instanceID,workspace,inventory,configuration,nil,workspaceFiles...)\n}\n\nfunc HandlerWithNativeCreateHost(db *sql.DB, webDir string, service *domain.Service, runtime domain.ClientSessionRuntime, instanceID string, workspace domain.WorkspaceAuthority, inventory domain.LocalInventoryScanner, configuration domain.ClientConfigurationAuthority, native domain.NativeCreateAuthorityBinder, workspaceFiles ...domain.ClientWorkspaceFiles) http.Handler {\n'
change(n,old,new)
change(n,'\t\tv2.svc.ConfigurationAuthority = configuration\n','\t\tv2.svc.ConfigurationAuthority = configuration\n\t\tif native != nil { authority,err:=native.BindNativeCreateAuthority(v2.svc); if err != nil { v2.loadErr=err } else { v2.svc.NativeCreateAuthority=authority } }\n')
n='apps/control/main.go'
change(n,'api.HandlerWithConfigurationHost(', 'api.HandlerWithNativeCreateHost(',2)
change(n,'workspaceAuthority, inventory, localHost, localHost))','workspaceAuthority, inventory, localHost, localHost, localHost))',2)
n='internal/domain/backup.go'
change(n,'func backupIntegrityPolicy(db *sql.DB, policy *backupPolicy) error {\n','func backupIntegrityPolicy(db *sql.DB, policy *backupPolicy) error {\n\tif err := rejectPreparedNativeOriginBackup(db); err != nil { return err }\n')

for n,text in texts.items():
    p=src/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8',newline='\n')
# Install exactly the registered production closure, never Main/other author files.
for n in scope['production_paths']:
    p=src/n;assert p.is_file(),n
for n in scope['production_paths']:
    p=ROOT/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((src/n).read_bytes())
print(json.dumps({'status':'INSTALLED_EXACT17_CORE_PRODUCTION','files':scope['production_paths']},ensure_ascii=False))
