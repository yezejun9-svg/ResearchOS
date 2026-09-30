package main

import (
    "context"
    "encoding/json"
    "log"
    "os"
    "path/filepath"
    "time"

    "researchos.local/research-os/internal/domain"
    "researchos.local/research-os/internal/store"
)

// This process is only used against the temporary W13 browser fixture database.
func main() {
    if len(os.Args) != 2 || os.Getenv("RESEARCHOS_TASK_ID") != "W13" { log.Fatal("W13 project id required") }
    db, err := store.Open(filepath.Join(os.Getenv("RESEARCHOS_DATA_DIR"), "researchos.sqlite"))
    if err != nil { log.Fatal(err) }
    defer db.Close()
    service, err := domain.New(db, filepath.Join("spec", "v2.0", "contracts"), filepath.Join("migrations", "sqlite", "0002_domain.sql"))
    if err != nil { log.Fatal(err) }
    principal := domain.Principal{ID: domain.ID(), Roles: []string{"SOURCE_ADAPTER"}, Grants: []domain.Grant{{ProjectID: os.Args[1]}}}
    if err = service.ProvisionPrincipal(context.Background(), principal); err != nil { log.Fatal(err) }
    token, err := service.IssueCredential(context.Background(), principal.ID, 15*time.Minute)
    if err != nil { log.Fatal(err) }
    result := map[string]string{"principal_id": principal.ID, "token": token}
    for name, roles := range map[string][]string{"editor": {"PLANNER", "EXECUTOR"}, "verifier": {"VERIFIER"}, "scheduler": {"SCHEDULER"}} {
        actor := domain.Principal{ID: domain.ID(), Roles: roles, Grants: []domain.Grant{{ProjectID: os.Args[1]}}}
        if err = service.ProvisionPrincipal(context.Background(), actor); err != nil { log.Fatal(err) }
        credential, issueErr := service.IssueCredential(context.Background(), actor.ID, 15*time.Minute)
        if issueErr != nil { log.Fatal(issueErr) }
        result[name+"_id"] = actor.ID
        result[name+"_token"] = credential
    }
    if err = json.NewEncoder(os.Stdout).Encode(result); err != nil { log.Fatal(err) }
}
