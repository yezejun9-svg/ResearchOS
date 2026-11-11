//go:build windows

package recoveryauthority

import (
    "context"
    "crypto/rand"
    "encoding/hex"
    "encoding/json"
    "errors"
    "io"
    "os"
    "os/exec"
    "path/filepath"
    "strconv"
    "syscall"
    "time"

    "golang.org/x/sys/windows"
    rt "researchos.local/research-os/adapters/runtime"
)

type migrationBootstrapFrame struct { Grant json.RawMessage `json:"migration_grant"`; OwnerToken string `json:"owner_token"` }

func ReceiveMigrationInherited(ctx context.Context) (MigrationToken,string,error) {
    var zero MigrationToken
    boot,e:=readBootstrap(); if e!=nil { return zero,"",e }; if boot.Purpose!=MigrationPurpose { return zero,"",errors.New("AUTHORITY_MIGRATION_BOOTSTRAP_PURPOSE") }
    self,e:=process(windows.CurrentProcess()); if e!=nil { return zero,"",e }
    release,releaseRaw,e:=loadRelease(filepath.Join(filepath.Dir(self.Image.Path),"recovery-release.json")); if e!=nil { return zero,"",e }
    if e=acceptedImage(self,release.ControlImage,release.SID,"researchos.local/research-os/apps/control"); e!=nil { return zero,"",e }
    peer,e:=windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE,false,boot.Peer.PID); if e!=nil { return zero,"",e }
    n:=&nativeSession{peer:peer,self:self,peerIdentity:boot.Peer}; ok:=false; defer func(){ if !ok { _=n.close() } }()
    observed,e:=process(peer); if e!=nil || !sameProcess(observed,boot.Peer) { return zero,"",errors.New("AUTHORITY_MIGRATION_PEER") }
    if e=acceptedImage(observed,release.RootImage,release.SID,"researchos.local/research-os/ops/supervisor/recovery_root"); e!=nil { return zero,"",e }
    n.channel,e=dialPrivate(ctx,boot.Pipe,boot.Peer); if e!=nil { return zero,"",e }
    var frame migrationBootstrapFrame; if e=readFrame(n.channel,boot.Key,MigrationPurpose,&frame); e!=nil { return zero,"",e }
    g,e:=verifyMigrationGrant(frame.Grant,releaseRaw); if e!=nil { return zero,"",e }; b:=g.Binding
    if !releaseCoversGrant(release,g.ExpiresUTC) { return zero,"",errors.New("AUTHORITY_MIGRATION_RELEASE_EXPIRY") }
    n.expires,_=time.Parse(time.RFC3339Nano,g.ExpiresUTC)
    if n.guards,e=sourceGuards(release); e!=nil { return zero,"",e }
    for _,pin:=range []RawPin{release.RootImage,release.ControlImage} { f,_,err:=pinHeld(pin); if err!=nil { return zero,"",err }; n.guards=append(n.guards,f) }
    for _,p:=range g.Pins { f,_,err:=pinHeld(p); if err!=nil { return zero,"",err }; n.guards=append(n.guards,f) }
    if n.root,e=hold(b.Root,true,true); e!=nil { return zero,"",e }; if n.root.id!=b.RootIdentity { return zero,"",errors.New("AUTHORITY_MIGRATION_ROOT_ID") }
    if n.db,e=hold(b.Database,false,true); e!=nil { return zero,"",e }; if n.db.id!=b.DatabaseIdentity { return zero,"",errors.New("AUTHORITY_MIGRATION_DATABASE_ID") }
    if n.lease,e=rt.AcquireDataRootLease(b.Root); e!=nil { return zero,"",e }
    if e=n.lease.Borrow(b.Root); e!=nil { _=n.lease.Close(); n.lease=nil; return zero,"",e }
    if e=n.check(); e!=nil { return zero,"",e }; if frame.OwnerToken=="" { return zero,"",errors.New("AUTHORITY_MIGRATION_OWNER_REQUIRED") }
    ok=true; return MigrationToken{state:&migrationState{native:n,grant:g,phase:"READY"}},frame.OwnerToken,nil
}

// Distinct entry, grant filename, purpose, schema and nonce journal; never calls
// adoption signing, Run mutation or runtime dispatch. It carries no old token.
func RunEnrolledMigrationRoot(ctx context.Context,ownerToken string) error {
    if ownerToken=="" || len(ownerToken)>4096 { return errors.New("AUTHORITY_OWNER_INPUT") }
    self,e:=process(windows.CurrentProcess()); if e!=nil { return e }; dir:=filepath.Dir(self.Image.Path)
    release,releaseRaw,e:=loadRelease(filepath.Join(dir,"recovery-release.json")); if e!=nil { return e }
    if e=acceptedImage(self,release.RootImage,release.SID,"researchos.local/research-os/ops/supervisor/recovery_root"); e!=nil { return e }
    guards,e:=sourceGuards(release); if e!=nil { return e }; defer func(){ for _,f:=range guards { _=f.file.Close() } }()
    control,_,e:=pinHeld(release.ControlImage); if e!=nil { return e }; defer control.file.Close()
    gf,e:=hold(filepath.Join(dir,"current-schema23-to24-grant.json"),false,false); if e!=nil { return e }; defer gf.file.Close()
    raw,e:=io.ReadAll(io.LimitReader(gf.file,maxFrame+1)); if e!=nil || len(raw)>maxFrame { return errors.New("AUTHORITY_MIGRATION_GRANT_SIZE") }
    g,e:=verifyMigrationGrant(raw,releaseRaw); if e!=nil { return e }
    if !releaseCoversGrant(release,g.ExpiresUTC) { return errors.New("AUTHORITY_MIGRATION_RELEASE_EXPIRY") }
    for _,p:=range g.Pins { f,_,err:=pinHeld(p); if err!=nil { return err }; guards=append(guards,f) }
    root,e:=hold(g.Binding.Root,true,true); if e!=nil { return e }; defer root.file.Close()
    db,e:=hold(g.Binding.Database,false,true); if e!=nil { return e }; defer db.file.Close()
    if root.id!=g.Binding.RootIdentity || db.id!=g.Binding.DatabaseIdentity { return errors.New("AUTHORITY_MIGRATION_GRANT_NATIVE_ID") }
    nonceDir:=filepath.Join(dir,"consumed-schema23-to24-grants"); if e=os.MkdirAll(nonceDir,0700); e!=nil { return e }; if e=plainPath(nonceDir); e!=nil { return e }
    consumed,e:=os.OpenFile(filepath.Join(nonceDir,g.Nonce+".used"),os.O_WRONLY|os.O_CREATE|os.O_EXCL,0600); if e!=nil { return errors.New("AUTHORITY_MIGRATION_GRANT_ALREADY_USED") }
    if _,e=consumed.WriteString(digest(raw)+"\n"); e==nil { e=consumed.Sync() }; ce:=consumed.Close(); if e!=nil { return e }; if ce!=nil { return ce }
    expires,_:=time.Parse(time.RFC3339Nano,g.ExpiresUTC); ctx,cancel:=context.WithDeadline(ctx,expires); defer cancel()
    random:=make([]byte,32); if _,e=rand.Read(random); e!=nil { return e }; name:=pipePrefix+hex.EncodeToString(random)
    key:=make([]byte,32); if _,e=rand.Read(key); e!=nil { return e }; defer wipe(key)
    server,e:=createPrivate(name); if e!=nil { return e }; serverOwned:=true; defer func(){ if serverOwned { _=windows.CloseHandle(server) } }()
    job,e:=maintenanceJob(); if e!=nil { return e }; defer windows.CloseHandle(job)
    br,bw,e:=os.Pipe(); if e!=nil { return e }; defer br.Close(); defer bw.Close()
    if e=windows.SetHandleInformation(windows.Handle(br.Fd()),windows.HANDLE_FLAG_INHERIT,windows.HANDLE_FLAG_INHERIT); e!=nil { return e }
    child:=exec.CommandContext(ctx,release.ControlImage.Path,MigrationArgument); child.Dir=release.SourceRoot
    child.Env=[]string{"SystemRoot="+os.Getenv("SystemRoot"),"WINDIR="+os.Getenv("WINDIR"),bootstrapEnv+"="+strconv.FormatUint(uint64(br.Fd()),10)}
    child.SysProcAttr=&syscall.SysProcAttr{HideWindow:true,AdditionalInheritedHandles:[]syscall.Handle{syscall.Handle(br.Fd())}}; child.Stdout=os.Stdout; child.Stderr=os.Stderr
    if e=child.Start(); e!=nil { return e }; waited:=false; defer func(){ if !waited { _=child.Process.Kill(); _=child.Wait() } }()
    ph,e:=windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE|windows.PROCESS_SET_QUOTA|windows.PROCESS_TERMINATE,false,uint32(child.Process.Pid)); if e!=nil { return e }; defer windows.CloseHandle(ph)
    if e=windows.AssignProcessToJobObject(job,ph); e!=nil { return e }
    observed,e:=process(ph); if e!=nil { return e }; if e=acceptedImage(observed,release.ControlImage,release.SID,"researchos.local/research-os/apps/control"); e!=nil { return e }
    if _,e=bw.Write(encoded(inheritedBootstrap{Purpose:MigrationPurpose,Pipe:name,Key:key,Peer:self})); e!=nil { return e }; if e=bw.Close(); e!=nil { return e }; _=br.Close()
    connection,e:=acceptPrivate(ctx,server,observed); if e!=nil { return e }; serverOwned=false; defer connection.Close()
    if e=writeFrame(connection,key,MigrationPurpose,migrationBootstrapFrame{Grant:raw,OwnerToken:ownerToken}); e!=nil { return e }
    e=child.Wait(); waited=true; return e
}
