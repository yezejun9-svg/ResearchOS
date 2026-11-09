package domain

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"strings"
	"testing"
)

func nativeOriginTamperReceipt(t *testing.T,f *nativeOriginFixture,edit func(string)string){
	t.Helper();objects:=nativeOriginDDLObjects()
	for _,name:=range []string{"native_origin_receipt_no_update","native_origin_receipt_seal"}{if _,e:=f.db.Exec(`DROP TRIGGER `+name);e!=nil{t.Fatal(e)}}
	var headers string;if e:=f.db.QueryRow(`SELECT headers FROM idempotency WHERE key='store-native'`).Scan(&headers);e!=nil{t.Fatal(e)}
	if _,e:=f.db.Exec(`UPDATE idempotency SET headers=? WHERE key='store-native'`,edit(headers));e!=nil{t.Fatal(e)}
	for _,name:=range []string{"native_origin_receipt_no_update","native_origin_receipt_seal"}{if _,e:=f.db.Exec(objects[name]);e!=nil{t.Fatal(e)}}
}

func TestNativeOriginStoreSchemaAndImmutability(t *testing.T){
	f:=newNativeOriginFixture(t,true);if _,e:=f.execute(t,f.create(t,"store-native"),fixtureNativeRef());e!=nil{t.Fatal(e)}
	for _,recursive:=range []int{0,1}{t.Run(string(rune('0'+recursive)),func(t *testing.T){
		if _,e:=f.db.Exec(`PRAGMA recursive_triggers=`+string(rune('0'+recursive)));e!=nil{t.Fatal(e)}
		for _,query:=range []string{
			`UPDATE client_native_writer_origins SET writer_epoch=writer_epoch`,
			`DELETE FROM client_native_writer_origins`,
			`INSERT OR REPLACE INTO client_native_writer_origins SELECT * FROM client_native_writer_origins`,
			`INSERT OR IGNORE INTO client_native_writer_origins SELECT * FROM client_native_writer_origins`,
			`UPDATE idempotency SET headers=headers WHERE key='store-native'`,
			`UPDATE idempotency SET body=body WHERE key='store-native'`,
			`DELETE FROM idempotency WHERE key='store-native'`,
			`INSERT OR REPLACE INTO idempotency SELECT * FROM idempotency WHERE key='store-native'`,
		}{if _,e:=f.db.Exec(query);e==nil{t.Fatal("immutable relation was mutable",query)}}
	})}
	if _,e:=ValidateClientNativeWriterOriginHistory(context.Background(),f.db,f.client.Doc);e!=nil{t.Fatal(e)}
	if _,e:=f.db.Exec(`CREATE INDEX extra_native_origin_index ON client_native_writer_origins(project)`);e!=nil{t.Fatal(e)}
	if _,e:=ValidateClientNativeWriterOriginHistory(context.Background(),f.db,f.client.Doc);e==nil{t.Fatal("extra index drift ignored")}
}

func TestNativeOriginStoreMissingRelationsAndExactWire(t *testing.T){
	for _,mode:=range []string{"missing-row","missing-marker","wire-whitespace","bad-body-hash","missing-schema"}{t.Run(mode,func(t *testing.T){
		f:=newNativeOriginFixture(t,true);env:=f.create(t,"store-native");if _,e:=f.execute(t,env,fixtureNativeRef());e!=nil{t.Fatal(e)}
		switch mode{
		case "missing-row":
			if _,e:=f.db.Exec(`DROP TRIGGER native_origin_no_delete; DELETE FROM client_native_writer_origins;`);e!=nil{t.Fatal(e)}
			if _,e:=f.db.Exec(nativeOriginDDLObjects()["native_origin_no_delete"]);e!=nil{t.Fatal(e)}
		case "missing-marker":nativeOriginTamperReceipt(t,f,func(old string)string{var h nativeMarkedCommandHeader;if json.Unmarshal([]byte(old),&h)!=nil{t.Fatal("header fixture")};return string(Bytes(clientCommandHeader{clientCommandHeaderSchema,h.Encoding,h.Raw}))})
		case "wire-whitespace":nativeOriginTamperReceipt(t,f,func(old string)string{var h nativeMarkedCommandHeader;if json.Unmarshal([]byte(old),&h)!=nil{t.Fatal("header fixture")};raw,e:=base64.StdEncoding.DecodeString(h.Raw);if e!=nil{t.Fatal(e)};h.Raw=base64.StdEncoding.EncodeToString(append([]byte(" \n"),raw...));return string(Bytes(h))})
		case "bad-body-hash":
			if _,e:=f.db.Exec(`DROP TRIGGER native_origin_no_update; UPDATE client_native_writer_origins SET origin_hash=?`,Digest([]byte("shape-valid-corruption")));e!=nil{t.Fatal(e)}
			if _,e:=f.db.Exec(nativeOriginDDLObjects()["native_origin_no_update"]);e!=nil{t.Fatal(e)}
		case "missing-schema":if _,e:=f.db.Exec(`DROP TABLE client_native_writer_origins`);e!=nil{t.Fatal(e)}
		}
		if _,e:=ValidateClientNativeWriterOriginHistory(context.Background(),f.db,f.client.Doc);e==nil{t.Fatal("missing/corrupt provenance became legacy")}
		if _,e:=f.execute(t,env,"");e==nil{t.Fatal("sealed replay ignored storage corruption")}
	})}
}

func TestNativeOriginStorePreparedInstallDoesNotAdopt25(t *testing.T){
	f:=newNativeOriginFixture(t,false)
	var before,after int;if e:=f.db.QueryRow(`SELECT max(version) FROM schema_migrations`).Scan(&before);e!=nil{t.Fatal(e)}
	if e:=InstallClientNativeWriterOriginPreparedSchema(context.Background(),f.db);e!=nil{t.Fatal(e)}
	if e:=f.db.QueryRow(`SELECT max(version) FROM schema_migrations`).Scan(&after);e!=nil{t.Fatal(e)}
	if before!=after||after>24{t.Fatal("prepared addon changed ordinary migration adoption")}
	if e:=InstallClientNativeWriterOriginPreparedSchema(context.Background(),f.db);e!=nil{t.Fatal("same exact prepared schema was not idempotent",e)}
	if _,e:=f.db.Exec(`DROP TRIGGER native_origin_no_update`);e!=nil{t.Fatal(e)}
	if e:=InstallClientNativeWriterOriginPreparedSchema(context.Background(),f.db);e==nil||strings.Contains(e.Error(),"UNSUPPORTED"){t.Fatal("drift was reinstalled or treated as never-adopted")}
}
