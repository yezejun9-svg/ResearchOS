from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
src=HERE/'src/internal/domain'
fields=re.findall(r'\t(\w+) (string|int64) `json:"([^"]+)"`', (src/'client_native_writer_origin_schema.go').read_text(encoding='utf-8').split('type nativeOriginRow')[0])
assert len(fields)==22
columns=[]
for name,kind,col in fields:
    sqltype='INTEGER' if kind=='int64' else 'TEXT'
    check=f"typeof({col})='integer' AND {col}=1" if kind=='int64' else f"typeof({col})='text' AND length({col})>0"
    if col=='origin_schema':check+=f" AND {col}='researchos.client-native-writer-origin.v1'"
    for target,prefix,length in [('attestation_ref','natt-',64),('connection_instance_ref','nci-',32),('host_instance_ref','host-',12)]:
        if col==target:check+=f" AND length({col})={len(prefix)+length} AND substr({col},1,{len(prefix)})='{prefix}' AND substr({col},{len(prefix)+1}) NOT GLOB '*[^0-9a-f]*'"
    if col.endswith('_hash') or col in ('witness_hash','host_generation_ref'):
        check+=f" AND length({col})=71 AND substr({col},1,7)='sha256:' AND substr({col},8) NOT GLOB '*[^0-9a-f]*'"
    columns.append(f" {col} {sqltype} NOT NULL CHECK({check})")
columns += [" origin_body TEXT NOT NULL CHECK(json_valid(origin_body) AND json_type(origin_body)='object')", " origin_hash TEXT NOT NULL CHECK(length(origin_hash)=71 AND substr(origin_hash,1,7)='sha256:' AND substr(origin_hash,8) NOT GLOB '*[^0-9a-f]*')"]
for name,kind,col in fields:
    jtype='integer' if kind=='int64' else 'text'
    columns.append(f" CHECK(COALESCE(json_type(origin_body,'$.{col}')='{jtype}' AND json_extract(origin_body,'$.{col}')={col},0))")
columns += [" PRIMARY KEY(attestation_ref)"," UNIQUE(principal,command_id)"," UNIQUE(project,session_id,writer_epoch)"," FOREIGN KEY(principal,command_id,request_hash) REFERENCES client_command_identities(principal,command_id,request_hash) DEFERRABLE INITIALLY DEFERRED", " FOREIGN KEY(session_id) REFERENCES client_sessions(id) DEFERRABLE INITIALLY DEFERRED"]
parts=[('client_native_writer_origins','CREATE TABLE client_native_writer_origins (\n'+',\n'.join(columns)+'\n);')]
parts += [
 ('native_origin_no_update',"CREATE TRIGGER native_origin_no_update BEFORE UPDATE ON client_native_writer_origins BEGIN SELECT RAISE(ABORT,'immutable native writer origin'); END;"),
 ('native_origin_no_delete',"CREATE TRIGGER native_origin_no_delete BEFORE DELETE ON client_native_writer_origins BEGIN SELECT RAISE(ABORT,'immutable native writer origin'); END;"),
 ('native_origin_no_replace',"CREATE TRIGGER native_origin_no_replace BEFORE INSERT ON client_native_writer_origins WHEN EXISTS(SELECT 1 FROM client_native_writer_origins WHERE attestation_ref=NEW.attestation_ref OR (principal=NEW.principal AND command_id=NEW.command_id) OR (project=NEW.project AND session_id=NEW.session_id AND writer_epoch=NEW.writer_epoch)) BEGIN SELECT RAISE(ABORT,'immutable native writer origin'); END;")]
v2="researchos.private-command-envelope.native-create.v2"
old="researchos.private-command-envelope.v1"
native=lambda a:f"CASE WHEN json_valid({a}.headers) THEN json_extract({a}.headers,'$.schema')='{v2}' OR json_type({a}.headers,'$.native_create_origin') IS NOT NULL ELSE 0 END"
parts += [
 ('native_origin_receipt_no_insert',f"CREATE TRIGGER native_origin_receipt_no_insert BEFORE INSERT ON idempotency WHEN {native('NEW')} BEGIN SELECT RAISE(ABORT,'native receipt must seal existing response'); END;"),
 ('native_origin_receipt_no_update',f"CREATE TRIGGER native_origin_receipt_no_update BEFORE UPDATE ON idempotency WHEN {native('OLD')} BEGIN SELECT RAISE(ABORT,'immutable native receipt'); END;"),
 ('native_origin_receipt_no_delete',f"CREATE TRIGGER native_origin_receipt_no_delete BEFORE DELETE ON idempotency WHEN {native('OLD')} BEGIN SELECT RAISE(ABORT,'immutable native receipt'); END;"),
 ('native_origin_receipt_no_replace',f"CREATE TRIGGER native_origin_receipt_no_replace BEFORE INSERT ON idempotency WHEN EXISTS(SELECT 1 FROM idempotency old WHERE old.principal=NEW.principal AND old.project=NEW.project AND old.operation=NEW.operation AND old.key=NEW.key AND ({native('old')})) BEGIN SELECT RAISE(ABORT,'immutable native receipt'); END;"),
 ('native_origin_receipt_seal',f"""CREATE TRIGGER native_origin_receipt_seal BEFORE UPDATE ON idempotency WHEN {native('NEW')} BEGIN
 SELECT CASE WHEN NOT (COALESCE(json_extract(OLD.headers,'$.schema')='{old}',0) AND NEW.principal=OLD.principal AND NEW.project=OLD.project AND NEW.operation=OLD.operation AND NEW.key=OLD.key AND NEW.request_hash=OLD.request_hash AND NEW.status=OLD.status AND NEW.body=OLD.body AND NEW.created_at=OLD.created_at AND json_extract(NEW.headers,'$.schema')='{v2}' AND json_extract(NEW.headers,'$.encoding')='base64' AND json_extract(NEW.headers,'$.raw_envelope_base64')=json_extract(OLD.headers,'$.raw_envelope_base64') AND json_extract(NEW.headers,'$.native_create_origin.schema_version')=1 AND OLD.operation='v2:session.create' AND json_extract(OLD.body,'$.status')='COMPLETED' AND EXISTS(SELECT 1 FROM client_native_writer_origins o WHERE o.principal=OLD.principal AND o.project=OLD.project AND o.command_id=OLD.key AND o.request_hash=OLD.request_hash AND o.session_id=json_extract(OLD.body,'$.session_id') AND o.session_id=json_extract(OLD.body,'$.result.session_id') AND o.attestation_ref=json_extract(NEW.headers,'$.native_create_origin.attestation_ref') AND o.witness_hash=json_extract(NEW.headers,'$.native_create_origin.witness_hash') AND o.origin_hash=json_extract(NEW.headers,'$.native_create_origin.origin_hash'))) THEN RAISE(ABORT,'invalid native receipt seal') END;
END;""")]
out=src/'contracts/0025_client_native_writer_origins.sql';out.parent.mkdir(parents=True,exist_ok=True)
parts=[(n,s.replace('SELECT CASE WHEN NOT (COALESCE','SELECT CASE WHEN NOT COALESCE((COALESCE').replace("THEN RAISE(ABORT,'invalid native receipt seal')"," ,0) THEN RAISE(ABORT,'invalid native receipt seal')")) if n=='native_origin_receipt_seal' else (n,s) for n,s in parts]
out.write_text('-- Prepared fresh-fixture addon only. Not a live migration; no schema_migrations bump.\n'+''.join('\n-- object: '+n+'\n'+s+'\n' for n,s in parts),encoding='utf-8',newline='\n')
names=','.join(col for _,_,col in fields)+',origin_body,origin_hash'
args=', '.join('b.'+name for name,_,_ in fields)+', row.raw, row.hash'
scan=', '.join('&b.'+name for name,_,_ in fields)+', &raw, &hash'
snippet=f'''const nativeOriginColumns = "{names}"
func insertNativeOrigin(ctx context.Context,tx *sql.Tx,row nativeOriginRow)error{{
 b:=row.body
 _,err:=tx.ExecContext(ctx,`INSERT INTO client_native_writer_origins(`+nativeOriginColumns+`) VALUES({','.join('?' for _ in range(24))})`,{args})
 return err
}}
func readNativeOrigins(ctx context.Context,ex nativeOriginExecutor)([]nativeOriginRow,error){{
 rows,err:=ex.QueryContext(ctx,`SELECT `+nativeOriginColumns+` FROM client_native_writer_origins ORDER BY attestation_ref`);if err!=nil{{return nil,err}}
 defer rows.Close();out:=[]nativeOriginRow{{}}
 for rows.Next(){{
  var b clientNativeWriterOriginBody;var raw,hash string
  if err=rows.Scan({scan});err!=nil{{return nil,err}}
  row,e:=makeNativeOriginRow(b);if e!=nil{{return nil,e}};stored,e:=decodeNativeOriginRow(raw,hash);if e!=nil{{return nil,e}}
  if stored.raw!=row.raw||stored.hash!=row.hash{{return nil,fmt.Errorf("NATIVE_ORIGIN_COLUMN_BODY")}}
  out=append(out,stored);if len(out)>10000{{return nil,fmt.Errorf("NATIVE_ORIGIN_INVENTORY_LIMIT")}}
 }}
 return out,rows.Err()
}}
'''
(HERE/'store-generated.txt').write_text(snippet,encoding='utf-8',newline='\n')
print('generated prepared addon and exact24-column accessors')
