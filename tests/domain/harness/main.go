// Trusted offline fixture provisioning. Never linked into the control HTTP surface.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "Fixture provisioning failed")
		os.Exit(1)
	}
}

func run() error {
	var input struct {
		Action         string
		DataDir        string
		PrincipalID    string
		Roles          []string
		ProjectID      string
		Restricted     bool
		CredentialFile string
	}
	if len(os.Args) != 2 {
		return fmt.Errorf("input path required")
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		return err
	}
	if err := json.Unmarshal(data, &input); err != nil {
		return err
	}
	db, err := store.Open(filepath.Join(input.DataDir, "researchos.sqlite"))
	if err != nil {
		return err
	}
	defer db.Close()
	service, err := domain.New(db, filepath.Join("spec", "v2.0", "contracts"), filepath.Join("migrations", "sqlite", "0002_domain.sql"))
	if err != nil {
		return err
	}
	ctx := context.Background()
	if input.Action == "revoke" {
		return service.RevokePrincipal(ctx, input.PrincipalID)
	}
	if input.Action != "provision" {
		return fmt.Errorf("unsupported fixture action")
	}
	principal := domain.Principal{ID: input.PrincipalID, Roles: input.Roles,
		Grants: []domain.Grant{{ProjectID: input.ProjectID, Restricted: input.Restricted}}}
	if err := service.ProvisionPrincipal(ctx, principal); err != nil {
		return err
	}
	token, err := service.IssueCredential(ctx, input.PrincipalID, 15*time.Minute)
	if err != nil {
		return err
	}
	credential, err := json.Marshal(map[string]string{"token": token, "principal_id": input.PrincipalID})
	if err != nil {
		return err
	}
	return os.WriteFile(input.CredentialFile, credential, 0600)
}
