//go:build windows

package recoveryauthority

import (
    "context"
    "crypto/ed25519"
    "crypto/rand"
    "encoding/hex"
    "errors"
    "io"
    "os"
    "os/exec"
    "path/filepath"
    "strconv"
    "syscall"
    "time"

    "golang.org/x/sys/windows"
)

// RunEnrolledRoot is composed only by ops/supervisor/recovery_root. The ordinary
// control CLI has no route to it. It cannot mint without compiled issuer trust,
// an accepted own image, a fresh issuer-signed exact grant and enrolled signer.
// ownerToken is obtained from a private inherited input, never flags or receipts.
func RunEnrolledRoot(ctx context.Context,ownerToken string) error {
    if ownerToken=="" || len(ownerToken)>4096 { return errors.New("AUTHORITY_OWNER_INPUT") }
    self,e:=process(windows.CurrentProcess()); if e!=nil { return e }
    dir:=filepath.Dir(self.Image.Path)
    release,releaseRaw,e:=loadRelease(filepath.Join(dir,"recovery-release.json")); if e!=nil { return e }
    if e=acceptedImage(self,release.RootImage,release.SID,"researchos.local/research-os/ops/supervisor/recovery_root"); e!=nil { return e }
    guards,e:=sourceGuards(release); if e!=nil { return e }; defer func(){ for _,f:=range guards { _=f.file.Close() } }()
    cf,_,e:=pinHeld(release.ControlImage); if e!=nil { return e }; defer cf.file.Close()
    grantFile,e:=hold(filepath.Join(dir,"current-adoption-grant.json"),false,false); if e!=nil { return e }; defer grantFile.file.Close()
    grantRaw,e:=io.ReadAll(io.LimitReader(grantFile.file,maxFrame+1)); if e!=nil || len(grantRaw)>maxFrame { return errors.New("AUTHORITY_GRANT_SIZE") }
    g,e:=verifyGrant(grantRaw,releaseRaw); if e!=nil { return e }
    if !releaseCoversGrant(release,g.ExpiresUTC) { return errors.New("AUTHORITY_RELEASE_EXPIRES_BEFORE_GRANT") }
    expires,_:=time.Parse(time.RFC3339Nano,g.ExpiresUTC)
    ctx,cancel:=context.WithDeadline(ctx,expires); defer cancel()
    raw:=map[string][]byte{}
    for _,p:=range g.Pins { f,data,err:=pinHeld(p); if err!=nil { return err }; guards=append(guards,f); raw[p.Role]=data }
    historical,started,expired,e:=readHistorical(raw,g.Tuple,g.Pins); if e!=nil { return e }
    root,e:=hold(g.Root,true,true); if e!=nil { return e }; defer root.file.Close()
    db,e:=hold(g.Database,false,true); if e!=nil { return e }; defer db.file.Close()
    if root.id!=g.RootIdentity || db.id!=g.DatabaseIdentity { return errors.New("AUTHORITY_GRANT_NATIVE_DATABASE_ID") }
    key,e:=readPurposeKey(filepath.Join(dir,"root-adoption-signing.dpapi"),"root-adoption"); if e!=nil { return e }; defer wipe(key)
    if hex.EncodeToString(ed25519.PrivateKey(key).Public().(ed25519.PublicKey))!=release.RootSigningPublicKey { return errors.New("AUTHORITY_SIGNER_NOT_ENROLLED") }
    // Durable CREATE_NEW consumes this fresh grant before any child starts.
    // Crash or transport failure never removes it or automatically retries.
    nonceDir:=filepath.Join(dir,"consumed-adoption-grants")
    if e=os.MkdirAll(nonceDir,0700); e!=nil { return e }
    if e=plainPath(nonceDir); e!=nil { return e }
    consumed,e:=os.OpenFile(filepath.Join(nonceDir,g.Nonce+".used"),os.O_WRONLY|os.O_CREATE|os.O_EXCL,0600); if e!=nil { return errors.New("AUTHORITY_GRANT_ALREADY_USED_OR_UNAVAILABLE") }
    if _,e=consumed.WriteString(digest(grantRaw)+"\n"); e==nil { e=consumed.Sync() }; ce:=consumed.Close(); if e!=nil { return e }; if ce!=nil { return ce }
    a:=Adoption{Schema:Schema,Kind:"HISTORICAL_EVIDENCE_ADOPTION",Purpose:Purpose,ReleaseID:release.ID,GrantSHA256:digest(grantRaw),Tuple:g.Tuple,Root:g.Root,RootIdentity:g.RootIdentity,Database:g.Database,DatabaseIdentity:g.DatabaseIdentity,Producer:self,SignedUTC:time.Now().UTC().Format(time.RFC3339Nano),ExpiresUTC:g.ExpiresUTC,Nonce:g.Nonce,Historical:historical,RootStartedUTC:started,RootClockExpiredUTC:expired,Pins:g.Pins,StateVerification:"REQUIRE_CURRENT_OWNER_AND_EXACT_CAS"}
    var random [32]byte; if _,e=rand.Read(random[:]); e!=nil { return e }; name:=pipePrefix+hex.EncodeToString(random[:])
    transportKey:=make([]byte,32); if _,e=rand.Read(transportKey); e!=nil { return e }; defer wipe(transportKey)
    server,e:=createPrivate(name); if e!=nil { return e }; serverOwned:=true; defer func(){ if serverOwned { _=windows.CloseHandle(server) } }()
    job,e:=maintenanceJob(); if e!=nil { return e }; defer windows.CloseHandle(job)
    br,bw,e:=os.Pipe(); if e!=nil { return e }; defer br.Close(); defer bw.Close()
    if e=windows.SetHandleInformation(windows.Handle(br.Fd()),windows.HANDLE_FLAG_INHERIT,windows.HANDLE_FLAG_INHERIT); e!=nil { return e }
    child:=exec.CommandContext(ctx,release.ControlImage.Path,MaintenanceArgument)
    child.Dir=release.SourceRoot
    child.Env=[]string{"SystemRoot="+os.Getenv("SystemRoot"),"WINDIR="+os.Getenv("WINDIR"),bootstrapEnv+"="+strconv.FormatUint(uint64(br.Fd()),10)}
    child.SysProcAttr=&syscall.SysProcAttr{HideWindow:true,AdditionalInheritedHandles:[]syscall.Handle{syscall.Handle(br.Fd())}}
    // No stdout/stderr credentials. Domain result is emitted only by successful
    // maintenance; inherited OWNER bytes never enter command/environment logs.
    child.Stdout=os.Stdout; child.Stderr=os.Stderr
    if e=child.Start(); e!=nil { return e }
    waited:=false; defer func(){ if !waited { _=child.Process.Kill(); _=child.Wait() } }()
    ph,e:=windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE|windows.PROCESS_SET_QUOTA|windows.PROCESS_TERMINATE,false,uint32(child.Process.Pid)); if e!=nil { return e }; defer windows.CloseHandle(ph)
    // Until assignment succeeds the child is blocked reading its empty private
    // bootstrap pipe. Parent death closes that pipe; no database has been opened.
    if e=windows.AssignProcessToJobObject(job,ph); e!=nil { return e }
    childIdentity,e:=process(ph); if e!=nil { return e }
    if e=acceptedImage(childIdentity,release.ControlImage,release.SID,"researchos.local/research-os/apps/control"); e!=nil { return e }
    a.Maintenance=childIdentity
    a.Signature=hex.EncodeToString(ed25519.Sign(ed25519.PrivateKey(key),append([]byte(Purpose+"/adoption\x00"),encoded(a)...)))
    if e=verifyAdoption(a,release,g,grantRaw); e!=nil { return e }
    if _,e=bw.Write(encoded(inheritedBootstrap{Purpose:Purpose,Pipe:name,Key:transportKey,Peer:self})); e!=nil { return e }; if e=bw.Close(); e!=nil { return e }; _=br.Close()
    connection,e:=acceptPrivate(ctx,server,childIdentity); if e!=nil { return e }; serverOwned=false; defer connection.Close()
    if e=writeFrame(connection,transportKey,Purpose,bootstrapFrame{Grant:grantRaw,Adoption:a,OwnerToken:ownerToken}); e!=nil { return e }
    // Root remains alive and keeps all source/raw guards until maintenance exits.
    // Lost result means unknown outcome and requires fresh review, never replay.
    e=child.Wait(); waited=true; return e
}
