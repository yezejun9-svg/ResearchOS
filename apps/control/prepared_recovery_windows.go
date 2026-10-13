//go:build windows

package main

import (
    "bytes"
    "context"
    "database/sql"
    "encoding/json"
    "errors"
    "net/url"
    "os"
    "path/filepath"
    "strings"
    "time"

    "researchos.local/research-os/internal/domain"
    "researchos.local/research-os/internal/recoveryauthority"
)

// Runs before all normal flags, migrations, protected stores, recovery scans,
// provider configuration and listeners. A public invocation alone lacks the
// inherited OS/crypto authority and therefore cannot open the database.
func runPreparedRecoveryMaintenance(args []string) (bool,error) {
    if len(args)==0 || (args[0]!=recoveryauthority.MaintenanceArgument && args[0]!=recoveryauthority.MigrationArgument && args[0]!=recoveryauthority.PauseMigrationArgument) { return false,nil }
    if len(args)!=1 { return true,errors.New("private recovery accepts no caller paths or authority options") }
    ctx,cancel:=context.WithTimeout(context.Background(),5*time.Minute); defer cancel()
    if args[0]==recoveryauthority.PauseMigrationArgument { return true,runPauseSchemaMaintenance(ctx) }
    if args[0]==recoveryauthority.MigrationArgument { return true,runPreparedSchemaMaintenance(ctx) }
    token,ownerToken,err:=recoveryauthority.ReceiveInherited(ctx); if err!=nil { return true,err }
    defer token.Close()
    adoption,err:=token.Adoption(); if err!=nil { return true,err }
    db,err:=openExclusiveRecoveryDB(ctx,adoption.Database); if err!=nil { return true,err }; defer db.Close()
    result,err:=domain.ExecutePreparedAbandonmentMaintenance(ctx,db,filepath.Join("spec","v2.0","contracts"),token,ownerToken)
    ownerToken=""
    if err!=nil { return true,err }; return true,json.NewEncoder(os.Stdout).Encode(result)
}
func openExclusiveRecoveryDB(ctx context.Context,path string) (*sql.DB,error) {
    u:=url.URL{Scheme:"file",Opaque:filepath.ToSlash(path)}; q:=u.Query(); q.Set("mode","rw"); u.RawQuery=q.Encode()
    db,err:=sql.Open("sqlite",u.String()); if err!=nil { return nil,err }
    db.SetMaxOpenConns(1); db.SetMaxIdleConns(1)
    ok:=false; defer func(){ if !ok { _=db.Close() } }()
    for _,statement:=range []string{"PRAGMA busy_timeout=5000","PRAGMA foreign_keys=ON","PRAGMA synchronous=FULL","PRAGMA locking_mode=EXCLUSIVE"} { if _,err=db.ExecContext(ctx,statement); err!=nil { return nil,err } }
    var mode string; if err=db.QueryRowContext(ctx,"PRAGMA locking_mode").Scan(&mode); err!=nil || strings.ToLower(mode)!="exclusive" { return nil,errors.New("native recovery requires exclusive SQLite connection") }
    // EXCLUSIVE locking mode retains the OS SQLite lock across later domain
    // transactions until this single-connection pool is closed.
    if _,err=db.ExecContext(ctx,"BEGIN EXCLUSIVE"); err!=nil { return nil,err }
    if _,err=db.ExecContext(ctx,"COMMIT"); err!=nil { return nil,err }
    ok=true; return db,nil
}
func runPreparedSchemaMaintenance(ctx context.Context) error {
    token,ownerToken,err:=recoveryauthority.ReceiveMigrationInherited(ctx); if err!=nil { return err }; defer token.Close()
    binding,err:=token.Binding(); if err!=nil { return err }
    raw,err:=token.Options(); if err!=nil { return err }
    var opt domain.LocalUpgradeOptions
    decoder:=json.NewDecoder(bytes.NewReader(raw)); decoder.DisallowUnknownFields()
    if err=decoder.Decode(&opt); err!=nil { return err }
    canonical,err:=json.Marshal(opt); if err!=nil || domain.Digest(canonical)!=binding.OptionsSHA256 || !bytes.Equal(canonical,raw) { return errors.New("native schema maintenance options differ from grant") }
    db,err:=openExclusiveRecoveryDB(ctx,binding.Database); if err!=nil { return err }; defer db.Close()
    result,err:=domain.ExecutePreparedAbandonmentSchemaUpgrade(ctx,db,token,ownerToken,opt)
    ownerToken=""
    if err!=nil { return err }; return json.NewEncoder(os.Stdout).Encode(result)
}

func runPauseSchemaMaintenance(ctx context.Context) error {
	token, ownerToken, err := recoveryauthority.ReceivePauseMigrationInherited(ctx)
	if err != nil {
		return err
	}
	defer token.Close()
	binding, err := token.Binding()
	if err != nil {
		return err
	}
	raw, err := token.Options()
	if err != nil {
		return err
	}
	var opt domain.PauseSchemaUpgradeOptions
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err = decoder.Decode(&opt); err != nil {
		return err
	}
	canonical, err := json.Marshal(opt)
	if err != nil || domain.Digest(canonical) != binding.OptionsSHA256 || !bytes.Equal(canonical, raw) {
		return errors.New("native schema maintenance options differ from grant")
	}
	db, err := openExclusiveRecoveryDB(ctx, binding.Database)
	if err != nil {
		return err
	}
	defer db.Close()
	result, err := domain.ExecutePauseSchemaUpgrade(ctx, db, token, ownerToken, opt)
	ownerToken = ""
	if err != nil {
		return err
	}
	return json.NewEncoder(os.Stdout).Encode(result)
}
