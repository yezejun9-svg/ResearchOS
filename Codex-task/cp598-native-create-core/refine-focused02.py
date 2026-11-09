from pathlib import Path
import hashlib,json,re
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-native-create-core-20261104')
AUTHOR=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/core/author')
previous=json.loads((AUTHOR/'focused02/results.json').read_text(encoding='utf-8'))['sources']
for n,h in previous.items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
changes={}
def read(n):return changes.get(n,(ROOT/n).read_text(encoding='utf-8'))
def replace(n,a,b):
    text=read(n);assert text.count(a)==1,(n,a[:90],text.count(a));changes[n]=text.replace(a,b,1)

n='internal/domain/client_writer_origin_test.go'
replace(n,'return f.decode(t, Bytes(Object{"protocol_version": ProtocolV2, "command_id": key, "client_id": "native-client", "project_id": f.project,','var project any=f.project\n\tif method=="host.configure"||method=="host.status"{project=nil}\n\treturn f.decode(t, Bytes(Object{"protocol_version": ProtocolV2, "command_id": key, "client_id": "native-client", "project_id": project,')
n='internal/host/native_client_attestation.go'
replace(n,'\t"time"\n','\t"time"\n\n\t"github.com/santhosh-tekuri/jsonschema/v6"\n')
old='''var nativeCreateDocument = sync.OnceValues(func() (*domain.SchemaDoc, error) {
	if domain.Digest(nativeCreateProfile) != nativeCreateProfileDigest {
		return nil, fmt.Errorf("NATIVE_CREATE_PROFILE_DIGEST")
	}
	return domain.LoadSchema(nativeCreateProfile)
})'''
new='''type nativeProfileLocalLoader struct{}
func (nativeProfileLocalLoader) Load(string)(any,error){return nil,fmt.Errorf("NATIVE_CREATE_EXTERNAL_SCHEMA_FORBIDDEN")}
type nativeCreateProfileDocument struct{schemas map[string]*jsonschema.Schema}
func(d *nativeCreateProfileDocument) ValidateDefInput(name string,value any)error{
	if name!="NativeClientAttestRequestFrame"{return fmt.Errorf("NATIVE_CREATE_PROFILE_DIRECTION")}
	return d.schemas[name].Validate(value)
}
func(d *nativeCreateProfileDocument) ValidateDef(name string,value any)error{
	if name!="NativeClientAttestResultFrame"{return fmt.Errorf("NATIVE_CREATE_PROFILE_DIRECTION")}
	return d.schemas[name].Validate(value)
}
var nativeCreateDocument = sync.OnceValues(func() (schemaDocument, error) {
	if domain.Digest(nativeCreateProfile) != nativeCreateProfileDigest {return nil,fmt.Errorf("NATIVE_CREATE_PROFILE_DIGEST")}
	var value map[string]any
	if json.Unmarshal(nativeCreateProfile,&value)!=nil{return nil,fmt.Errorf("NATIVE_CREATE_PROFILE_JSON")}
	location,ok:=value["$id"].(string);if !ok{return nil,fmt.Errorf("NATIVE_CREATE_PROFILE_ID")}
	compiler:=jsonschema.NewCompiler();compiler.UseLoader(nativeProfileLocalLoader{});compiler.AssertFormat();compiler.DefaultDraft(jsonschema.Draft2020)
	if err:=compiler.AddResource(location,value);err!=nil{return nil,err}
	doc:=&nativeCreateProfileDocument{schemas:map[string]*jsonschema.Schema{}}
	for _,name:=range []string{"NativeClientAttestRequestFrame","NativeClientAttestResultFrame"}{s,err:=compiler.Compile(location+"#/$defs/"+name);if err!=nil{return nil,err};doc.schemas[name]=s}
	return doc,nil
})'''
replace(n,old,new)

n='internal/domain/contracts/0025_client_native_writer_origins.sql'
ddl=read(n)
condition=re.search(r'SELECT CASE WHEN NOT COALESCE\(\((.*?)\)\s*,0\) THEN RAISE',ddl,re.S).group(1)
old_condition=condition
for field in ['principal','project','operation','key','request_hash','status','body','created_at']:
    condition=condition.replace('NEW.'+field+'=OLD.'+field,'NEW.'+field+' IS OLD.'+field)
condition += " AND json_object('schema','researchos.private-command-envelope.v1','encoding','base64','raw_envelope_base64',json_extract(OLD.headers,'$.raw_envelope_base64')) IS OLD.headers"
condition += " AND json_object('schema','researchos.private-command-envelope.native-create.v2','encoding','base64','raw_envelope_base64',json_extract(OLD.headers,'$.raw_envelope_base64'),'native_create_origin',json_object('schema_version',1,'attestation_ref',json_extract(NEW.headers,'$.native_create_origin.attestation_ref'),'witness_hash',json_extract(NEW.headers,'$.native_create_origin.witness_hash'),'origin_hash',json_extract(NEW.headers,'$.native_create_origin.origin_hash'))) IS NEW.headers"
ddl=ddl.replace(old_condition,condition,1)
guard="CREATE TRIGGER idempotency_immutable BEFORE UPDATE ON idempotency WHEN NOT COALESCE(("+condition+"),0) BEGIN SELECT RAISE(ABORT,'immutable replay'); END;"
prefix='-- Prepared fresh-fixture addon only. Not a live migration; no schema_migrations bump.\n'
assert ddl.startswith(prefix)
changes[n]=prefix+'DROP TRIGGER idempotency_immutable;\n'+ddl[len(prefix):]+'\n-- object: idempotency_immutable\n'+guard+'\n'

n='internal/domain/client_native_writer_origin_schema.go'
legacy="CREATE TRIGGER idempotency_immutable BEFORE UPDATE ON idempotency BEGIN SELECT RAISE(ABORT,'immutable replay'); END"
replace(n,'const nativeWriterOriginSchema = ', 'const nativeOriginLegacyReplayGuard = '+json.dumps(legacy)+'\n\nconst nativeWriterOriginSchema = ')
replace(n,'\tvar markers int\n','''	var replayGuard string
	if err=ex.QueryRowContext(ctx,`SELECT sql FROM sqlite_master WHERE type='trigger' AND name='idempotency_immutable'`).Scan(&replayGuard);err!=nil && err!=sql.ErrNoRows{return false,err}
	if strings.Contains(replayGuard,nativeCommandHeaderSchema)||strings.Contains(replayGuard,"client_native_writer_origins"){found["idempotency_immutable"]=replayGuard}
	var markers int
''')
replace(n,'\tif _, err = tx.ExecContext(ctx, nativeWriterOriginDDL); err != nil {','''	var replayGuard string
	if err=tx.QueryRowContext(ctx,`SELECT sql FROM sqlite_master WHERE type='trigger' AND name='idempotency_immutable'`).Scan(&replayGuard);err!=nil{return err}
	if strings.TrimSpace(replayGuard)!=nativeOriginLegacyReplayGuard{return fmt.Errorf("NATIVE_ORIGIN_BASE_GUARD_PREIMAGE:%s",Digest([]byte(replayGuard)))}
	if _, err = tx.ExecContext(ctx, nativeWriterOriginDDL); err != nil {''')

n='internal/domain/client_native_writer_origin_store_test.go'
text=read(n);assert text.count('[]string{"native_origin_receipt_no_update", "native_origin_receipt_seal"}')==2
changes[n]=text.replace('[]string{"native_origin_receipt_no_update", "native_origin_receipt_seal"}','[]string{"native_origin_receipt_no_update", "native_origin_receipt_seal", "idempotency_immutable"}')
replace(n,'\tfor _, recursive := range []int{0, 1} {','''	if _,e:=f.db.Exec(`UPDATE idempotency SET headers=headers WHERE key='configure-native'`);e==nil{t.Fatal("prepared addon weakened ordinary replay immutability")}
	for _, recursive := range []int{0, 1} {''')
for n,text in changes.items():(ROOT/n).write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({'status':'DIRECTED_THREE_DISTINCT_FOCUSED02_CAUSES','files':list(changes),'base_guard_preimage_sha256':hashlib.sha256(legacy.encode()).hexdigest()}))
