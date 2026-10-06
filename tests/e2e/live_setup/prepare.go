//go:build windows

package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
	hostboundary "researchos.local/research-os/internal/host"
)

const setupClientID = "w14-live-setup"

func (s *setup) prepare(ctx context.Context, choose bool) error {
	if _, err := os.Stat(s.policyPath); err != nil {
		return fmt.Errorf("frozen native Go preflight policy unavailable: %w", err)
	}
	if s.state.ProjectID == "" && !choose {
		return nil // Owner and private state are real; the chooser was not invoked.
	}
	if s.state.ProjectID == "" {
		if err := s.chooseAndBootstrap(ctx); err != nil {
			return err
		}
	}
	if s.state.CredentialRef == "" {
		key := os.Getenv("DEEPSEEK_API_KEY")
		if key == "" {
			return nil // Never fabricate a LIVE credential reference or model result.
		}
		ref, err := s.importModelCredential(ctx, key)
		key = ""
		if err != nil {
			return err
		}
		s.state.CredentialRef = ref
		if err := s.saveState(); err != nil {
			return err
		}
	}
	if !s.state.PlanReady {
		if err := s.preparePlan(ctx); err != nil {
			return err
		}
	} else if err := s.refreshCoordinatorConfig(ctx); err != nil {
		return err
	}
	return nil
}

func (s *setup) nativeCall(ctx context.Context, kind string, payload any) (domain.Object, error) {
	pipe := hostboundary.PipeName(s.host.InstanceID())
	if !s.nativeStarted {
		serverCtx, stop := context.WithCancel(ctx)
		s.nativeCancel, s.nativeDone, s.nativeStarted = stop, make(chan error, 1), true
		go func() { s.nativeDone <- s.host.ServeNative(serverCtx, pipe) }()
	}
	raw, err := json.Marshal(hostboundary.NativeFrame{Kind: kind, ClientID: setupClientID, Payload: domain.Bytes(payload)})
	if err != nil {
		return nil, err
	}
	reply, err := hostboundary.DialNative(pipe, raw)
	if err != nil {
		select {
		case serveErr := <-s.nativeDone:
			return nil, fmt.Errorf("native host %v, dial %w", serveErr, err)
		default:
			return nil, err
		}
	}
	var frame domain.Object
	if err := json.Unmarshal(reply, &frame); err != nil {
		return nil, err
	}
	if frame["kind"] == "NATIVE_ERROR" {
		return nil, fmt.Errorf("native host refused %s: %v", kind, frame["error"])
	}
	value, ok := frame["payload"].(map[string]any)
	if !ok {
		return nil, errors.New("native host returned no typed payload")
	}
	return value, nil
}

func (s *setup) chooseAndBootstrap(ctx context.Context) error {
	selected, err := s.nativeCall(ctx, hostboundary.KindWorkspaceChooseRequest, domain.Object{"requested_path": s.candidate, "requested_access": hostboundary.AccessReadWrite})
	if err != nil {
		return err
	}
	selectionRef := domain.Str(selected, "selection_ref")
	if selectionRef == "" {
		return errors.New("native chooser returned no selection reference")
	}
	if !strings.EqualFold(filepath.Clean(domain.Str(selected, "display_path")), filepath.Clean(s.candidate)) {
		return errors.New("native chooser selected a directory outside the fixed W14 candidate")
	}
	authority, schema, scanner, err := s.authority()
	if err != nil {
		return err
	}
	owner := domain.Principal{ID: s.owner.PrincipalID, Roles: []string{"OWNER"}, CanCreateProject: true}
	binding, err := s.svc.RegisterWorkspace(ctx, owner, authority, schema, domain.RegisterWorkspaceInput{SelectionRef: selectionRef, DisplayName: "W14 LIVE qualification candidate", RequestedAccess: hostboundary.AccessReadWrite, CommandID: "w14-live-workspace-register", ClientID: setupClientID})
	if err != nil {
		return err
	}
	workspaceRef := domain.Str(binding, "authorized_workspace_ref")
	if workspaceRef == "" {
		return errors.New("workspace.register returned no authorized reference")
	}
	// Recheck the persisted root pin returned by workspace.register.
	if !strings.EqualFold(filepath.Clean(domain.Str(binding, "display_path")), filepath.Clean(s.candidate)) {
		return errors.New("selected directory differs from the fixed candidate source")
	}
	boot, err := s.svc.BootstrapProject(ctx, owner, authority, schema, scanner, domain.BootstrapProjectInput{AuthorizedWorkspaceRef: workspaceRef, DisplayName: "W14 LIVE qualification", ClientID: setupClientID, CommandID: "w14-live-project-bootstrap", MeasurementMode: "LIVE"})
	if err != nil {
		return err
	}
	s.state.WorkspaceRef, s.state.ProjectID = workspaceRef, domain.Str(boot, "project_id")
	if s.state.ProjectID == "" {
		return errors.New("project.bootstrap returned no project ID")
	}
	return s.saveState()
}

func (s *setup) importModelCredential(ctx context.Context, key string) (string, error) {
	if err := ctx.Err(); err != nil {
		return "", err
	}
	if strings.TrimSpace(key) == "" {
		return "", errors.New("empty provider credential cannot be imported")
	}
	payload, err := s.nativeCall(ctx, hostboundary.KindCredentialImportRequest, domain.Object{"provider_id": "deepseek", "credential_kind": "API_KEY", "credential_value": key, "replace_credential_ref": nil})
	if err != nil {
		return "", err
	}
	ref := domain.Str(payload, "credential_ref")
	if ref == "" || s.host.CredentialStatus(ref) != "AVAILABLE" {
		return "", errors.New("native credential import did not create an available reference")
	}
	return ref, nil
}

func (s *setup) credentialFresh() bool {
	if s.state.CredentialRef == "" {
		return false
	}
	return s.host.CredentialUsable(s.state.CredentialRef)
}

func (s *setup) updatePrivateCoordinatorConfig(config domain.RuntimeCoordinatorConfig) error {
	name := filepath.Join(s.dataRoot, "host", "live_coordinator.json")
	raw, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(name+".tmp", raw, 0600); err != nil {
		return err
	}
	if err := os.Rename(name+".tmp", name); err != nil {
		return err
	}
	return nil
}

func privateTokenTTL() time.Duration { return 15 * time.Minute }
