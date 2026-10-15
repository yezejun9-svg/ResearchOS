//go:build windows

// Offline enrollment utility. Never installed as a public service endpoint.
// Provision emits only a public key; signed outputs require the source-pinned
// issuer's DPAPI resource. Root must review exact payload bytes before signing.
package main

import (
    "fmt"
    "log"
    "os"

    "researchos.local/research-os/internal/recoveryauthority"
)
func main() {
    if len(os.Args)==4 && os.Args[1]=="provision" {
        pub,err:=recoveryauthority.ProvisionEnrollmentKey(os.Args[3],os.Args[2]); if err!=nil { log.Fatal(err) }; fmt.Println(pub); return
    }
    if len(os.Args)==6 && os.Args[1]=="sign-reviewed" {
        raw,err:=os.ReadFile(os.Args[4]); if err!=nil { log.Fatal(err) }
        signed,err:=recoveryauthority.SignEnrollmentDocument(os.Args[3],os.Args[2],raw); if err!=nil { log.Fatal(err) }
        out,err:=os.OpenFile(os.Args[5],os.O_WRONLY|os.O_CREATE|os.O_EXCL,0600); if err!=nil { log.Fatal(err) }
        if _,err=out.Write(signed); err==nil { err=out.Sync() }; closeErr:=out.Close(); if err!=nil { log.Fatal(err) }; if closeErr!=nil { log.Fatal(closeErr) }; return
    }
    log.Fatal("usage: provision issuer|root-adoption private.dpapi; sign-reviewed release|grant|migration-grant|pause-migration-grant issuer.dpapi reviewed-payload.json new-signed.json")
}
