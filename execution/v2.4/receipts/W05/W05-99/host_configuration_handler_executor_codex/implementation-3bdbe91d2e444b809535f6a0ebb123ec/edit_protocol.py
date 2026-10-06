from pathlib import Path
R=Path(__file__).resolve().parents[8]
# Explicit worktree, never Main or a former author's checkout.
R=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-host-configuration-handler')
p=R/'internal/domain/client_protocol.go';s=p.read_text(encoding='utf8')
def change(a,b):
 global s
 assert s.count(a)==1, a[:100]
 s=s.replace(a,b)
change('\t"time"\n)', '\t"time"\n\n\t"researchos.local/research-os/internal/canonical"\n)')
change('\t"session.create": true,','\t"session.create": true, "host.configure": true,')
change('\textra            map[string]json.RawMessage','\textra            map[string]json.RawMessage\n\toriginalRaw      []byte')
change('func DecodeEnvelope(raw []byte) (*Envelope, error) {\n', '''func DecodeEnvelope(raw []byte) (*Envelope, error) {
 if len(raw)==0 || len(raw)>clientIdentityMaxRequest { return nil, fmt.Errorf("ENVELOPE_SIZE") }
 if _, err := canonical.JSON(raw); err != nil { return nil, fmt.Errorf("ENVELOPE_JSON: %w",err) }
''')
change('\te.extra = probe','\te.extra = probe\n\te.originalRaw = append([]byte(nil), raw...)\n\tfor _, key := range []string{"project_id","session_id","expected_revision","writer_epoch"} { if _, ok := probe[key]; !ok { return nil, fmt.Errorf("MISSING_FIELD:%s",key) } }')
change('if writeMethods[*e.Method] && *e.Method != "session.attach"', 'if writeMethods[*e.Method] && *e.Method != "host.configure" && *e.Method != "session.attach"')
start=s.index('\tif *e.Method == "host.configure" {');end=s.index('\n\tif err := e.validatePayload()',start)
s=s[:start]+''' if *e.Method == "host.configure" {
  if err := validateClientConfigurationScope(&e); err != nil { return nil, err }
 }
'''+s[end:]
change('\tInventoryScanner   LocalInventoryScanner','\tInventoryScanner   LocalInventoryScanner\n\tConfigurationAuthority ClientConfigurationAuthority')
start=s.index('\tif s.Doc != nil {',s.index('func (s *ClientService) Execute('));end=s.index('\n\tvar existingHash, body string',start)
s=s[:start]+''' if env == nil || env.Method == nil { return nil,false,fmt.Errorf("COMMAND_ENVELOPE_REQUIRED") }
 if _, err := clientAuthenticatedPrincipal(ctx,tx,principal); err != nil { return nil,false,err }
 if s.Doc == nil { return nil,false,fmt.Errorf("COMMAND_SCHEMA_REQUIRED") }
 if _, err := validateClientIdentityRequest(s.Doc,env.originalRaw,env); err != nil { return NewTypedRejection(env,"INVALID_REQUEST","command violates the published request schema"),false,nil }
 hash, err := env.ContentHash()
 if err != nil { return nil,false,err }
 original, err := lookupClientCommandIdentity(ctx,tx,s.Doc,principal,env.originalRaw,env)
 if err != nil { return nil,false,err }
 if original != nil && !(deref(env.Method)=="session.control" && deref(original.Status)=="ACKNOWLEDGED") { return original,true,nil }
'''+s[end:]
needle='\t// A typed rejection is committed for idempotency, but must not preserve any'
change(needle,''' if _, err = reserveClientCommandIdentity(ctx,tx,s.Doc,principal,env.originalRaw,env); err != nil { return nil,false,err }
 headers, err := writeClientCommandEnvelope(s.Doc,env)
 if err != nil { return nil,false,err }
'''+needle)
change('hash, 0, string(rb), "", time.Now()', 'hash, 0, string(rb), headers, time.Now()')
change('\treturn res, false, nil\n}', ''' if _, err = lookupClientCommandIdentity(ctx,tx,s.Doc,principal,env.originalRaw,env); err != nil { return nil,false,err }
 if deref(env.Method)=="host.configure" && deref(res.Status)=="COMPLETED" {
  owner, e := s.configurationOwner(ctx,tx,principal)
  if e != nil { return nil,false,e }
  if _, e = readClientConfiguration(ctx,tx,s.Doc,owner,principal,Str(res.Result,"model_config_ref")); e != nil { return nil,false,e }
 }
 return res, false, nil
}''')
change('\tswitch *env.Method {\n\tcase "workspace.register", "project.bootstrap":','\tswitch *env.Method {\n\tcase "host.configure":\n\t\treturn s.configureClientHost(ctx,tx,env,principal,sess)\n\tcase "workspace.register", "project.bootstrap":')
change('\treturn s.handleWrite(ctx, tx, env, principal, sess, reject)\n}', ''' if deref(env.Method)=="session.send" || deref(env.Method)=="goal.start" || deref(env.Method)=="workspace.write" {
  if err := s.validateSessionConfiguration(ctx,tx,principal,sess,false); err != nil { return clientFault(env,err) }
 }
 return s.handleWrite(ctx, tx, env, principal, sess, reject)
}''')
change('\t\treturn complete(1, map[string]any{', '''        revision, configs, credentials, err := s.clientConfigurationStatus(ctx,tx,principal)
        if err != nil { return clientFault(env,err) }
        return complete(1, map[string]any{''')
change('"authenticated_principal_ref": "principal:" + principal','"authenticated_principal_ref": principal')
change('"config_revision": s.Host.ConfigRevision, "model_configurations": nulls(s.Host.ModelConfigs),','"config_revision": revision, "model_configurations": configs,')
change('"credentials": nulls(s.Host.CredentialSumm)', '"credentials": credentials')
p.write_text(s,encoding='utf8',newline='\r\n')
