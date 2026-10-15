//go:build windows

// This dedicated Root requires separately enrolled own/control images and a
// signed current exact grant. It is never a normal control command or HTTP API.
package main

import (
    "context"
    "errors"
    "io"
    "log"
    "os"
    "strings"
    "time"

    "golang.org/x/sys/windows"
    "researchos.local/research-os/internal/recoveryauthority"
)

func main() {
    if err:=run(); err!=nil { log.Fatal(err) }
}
func run() error {
    // Trusted local Main delivers the CURRENT Owner credential through a pipe;
    // no token/path can be selected from ordinary command-line/environment.
    if kind,err:=windows.GetFileType(windows.Handle(os.Stdin.Fd())); err!=nil || kind!=windows.FILE_TYPE_PIPE { return errors.New("current Owner requires private inherited input") }
    raw,err:=io.ReadAll(io.LimitReader(os.Stdin,4097)); if err!=nil || len(raw)==0 || len(raw)>4096 { return errors.New("current Owner input unavailable") }
    defer func(){ for i:=range raw { raw[i]=0 } }()
    token:=strings.TrimSpace(string(raw)); ctx,cancel:=context.WithTimeout(context.Background(),5*time.Minute); defer cancel()
    if len(os.Args)==2 && os.Args[1]=="schema24-to25" { return recoveryauthority.RunEnrolledPauseMigrationRoot(ctx,token) }
    if len(os.Args)==2 && os.Args[1]=="schema23-to24" { return recoveryauthority.RunEnrolledMigrationRoot(ctx,token) }
    if len(os.Args)!=1 { return errors.New("Root accepts only its fixed recovery purpose") }
    return recoveryauthority.RunEnrolledRoot(ctx,token)
}
