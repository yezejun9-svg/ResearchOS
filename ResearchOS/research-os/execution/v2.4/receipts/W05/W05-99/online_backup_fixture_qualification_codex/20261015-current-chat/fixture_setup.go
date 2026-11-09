// Fixture-only driver. It creates new task-owned roots via the pinned public Host/domain APIs.
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"

    "researchos.local/research-os/adapters/local_workspace"
    "researchos.local/research-os/internal/api"
    "researchos.local/research-os/internal/domain"
    "researchos.local/research-os/internal/host"
    "researchos.local/research-os/internal/store"
)

func fatal(err error) { if err != nil { fmt.Fprintln(os.Stderr, err); os.Exit(1) } }

func main() {
    if len(os.Args) != 4 || (os.Args[1] != "Q01" && os.Args[1] != "Q02") {
        fatal(fmt.Errorf("usage: fixture_setup Q01|Q02 <new-case-root> <pinned-repo>"))
    }
    ctx := context.Background()
    kind, root, repo := os.Args[1], os.Args[2], os.Args[3]
    if _, err := os.Stat(root); !os.IsNotExist(err) { fatal(fmt.Errorf("case root must not exist: %v", err)) }
    fatal(os.MkdirAll(root, 0700))
    data := filepath.Join(root, "source-data")
    fatal(os.Mkdir(data, 0700))
    dbpath := filepath.Join(data, "researchos.sqlite")
    db, err := store.Open(dbpath); fatal(err)
    defer db.Close()
    fatal(store.Bootstrap(ctx, db, filepath.Join(repo, "migrations", "sqlite", "0001_bootstrap.sql")))
    svc, err := domain.New(db, filepath.Join(repo, "spec", "v2.0", "contracts"), filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql")); fatal(err)
    h, err := host.New(host.Config{DB: db, Dir: filepath.Join(data, "host"), ContractsDir: filepath.Join(repo, "spec", "v2.0", "contracts"), MigrationFile: filepath.Join(repo, "migrations", "sqlite", "0002_domain.sql"), SchemaDir: filepath.Join(repo, "internal", "api", "contracts")}); fatal(err)
    owner, err := h.BootstrapOwner(ctx); fatal(err)
    result := map[string]any{"case":kind,"db":dbpath,"source_data":data,"host_initialized":true,"owner_created":owner.CreatedOwner}
    if kind == "Q02" {
        workspace := filepath.Join(root, "chosen-workspace")
        fatal(os.MkdirAll(filepath.Join(workspace,"src"),0700))
        fatal(os.Mkdir(filepath.Join(workspace,"empty"),0700))
        fatal(os.WriteFile(filepath.Join(workspace,"src","main.go"),[]byte("package fixture\n"),0600))
        frame, err := json.Marshal(map[string]any{"kind":host.KindWorkspaceChooseRequest,"client_id":"online-backup-fixture","payload":map[string]any{"requested_path":workspace,"requested_access":host.AccessReadWrite}}); fatal(err)
        reply, err := h.HandleNative(frame,true,func(string)(string,error){return workspace,nil}); fatal(err)
        var choice struct{ Payload struct{ Ref string `json:"selection_ref"` } `json:"payload"` }
        fatal(json.Unmarshal(reply,&choice))
        if choice.Payload.Ref == "" { fatal(fmt.Errorf("empty selection reference")) }
        doc, err := api.ClientProtocolDocument(); fatal(err)
        principal := domain.Principal{ID:owner.PrincipalID,Roles:[]string{"OWNER"},CanCreateProject:true}
        authority := localworkspace.NewAuthority(h)
        registered, err := svc.RegisterWorkspace(ctx,principal,authority,doc,domain.RegisterWorkspaceInput{SelectionRef:choice.Payload.Ref,DisplayName:"fixture workspace",RequestedAccess:host.AccessReadWrite,ClientID:"online-backup-fixture",CommandID:"online-backup-register"}); fatal(err)
        ref := domain.Str(registered,"authorized_workspace_ref")
        project, err := svc.BootstrapProject(ctx,principal,authority,doc,localworkspace.NewScanner(),domain.BootstrapProjectInput{AuthorizedWorkspaceRef:ref,DisplayName:"fixture project",ClientID:"online-backup-fixture",CommandID:"online-backup-project",MeasurementMode:"FIXTURE"}); fatal(err)
        result["workspace_ref"] = ref
        result["project_id"] = domain.Str(project,"project_id")
        result["workspace"] = workspace
        result["workspace_file_sha256"] = domain.Digest([]byte("package fixture\n"))
    }
    var version int
    fatal(db.QueryRow("PRAGMA user_version").Scan(&version))
    result["user_version"] = version
    fatal(json.NewEncoder(os.Stdout).Encode(result))
}
