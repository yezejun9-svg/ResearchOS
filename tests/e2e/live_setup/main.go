//go:build windows

// live_setup prepares one isolated, real ResearchOS host for a bounded LIVE
// qualification. Prepare never contacts a model; the chooser and qualification
// are separate explicit phases so their effects are reviewable.
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"time"

	localworkspace "researchos.local/research-os/adapters/local_workspace"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	hostboundary "researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

const candidateRelative = ".local/w1401-live-candidate-20261005224707/source"
const policyRelative = ".local/w1401-live-candidate-20261005224707/preflight_policy.json"
const dataRelative = ".local/w1401-live-qualification-20261005"

type setupState struct {
	Version       int    `json:"version"`
	DataRoot      string `json:"data_root"`
	Candidate     string `json:"candidate"`
	OwnerID       string `json:"owner_id"`
	HostID        string `json:"host_id"`
	WorkspaceRef  string `json:"workspace_ref,omitempty"`
	ProjectID     string `json:"project_id,omitempty"`
	RequirementID string `json:"requirement_id,omitempty"`
	GoalID        string `json:"goal_id,omitempty"`
	CredentialRef string `json:"credential_ref,omitempty"`
	RuntimeID     string `json:"runtime_id,omitempty"`
	ProfileID     string `json:"profile_id,omitempty"`
	ProfileHash   string `json:"profile_hash,omitempty"`
	TaskID        string `json:"task_id,omitempty"`
	RunID         string `json:"run_id,omitempty"`
	AcceptanceID  string `json:"acceptance_id,omitempty"`
	ExecutorID    string `json:"executor_id,omitempty"`
	SchedulerID   string `json:"scheduler_id,omitempty"`
	VerifierID    string `json:"verifier_id,omitempty"`
	PlanReady     bool   `json:"plan_ready"`
	Qualified     bool   `json:"qualified"`
}

type setup struct {
	repo, candidate, policyPath, dataRoot string
	state                                 setupState
	db                                    *sql.DB
	svc                                   *domain.Service
	host                                  *hostboundary.Host
	owner                                 *hostboundary.BootstrapResult
	lease                                 *rt.DataRootLease
	ownerToken                            string
	nativeStarted                         bool
	nativeCancel                          context.CancelFunc
	nativeDone                            chan error
}

func main() {
	prepare := flag.Bool("prepare-only", false, "prepare isolated LIVE qualification without model dispatch")
	qualify := flag.Bool("qualify", false, "run the bounded LIVE qualification and independent acceptance")
	choose := flag.Bool("choose-workspace", false, "open the real Native directory chooser (prepare-only only)")
	data := flag.String("data-root", "", "isolated private data root; default is the fixed W14 LIVE path")
	flag.Parse()
	if *prepare == *qualify || *qualify && *choose {
		fatal(errors.New("choose exactly one of --prepare-only or --qualify; --choose-workspace belongs to prepare"))
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
	defer cancel()
	s, err := openSetup(ctx, *data)
	if err != nil {
		fatal(err)
	}
	defer s.close()
	if *prepare {
		err = s.prepare(ctx, *choose)
	} else {
		err = s.qualify(ctx)
	}
	if err != nil {
		_ = s.receipt("BLOCKED", err.Error())
		fatal(err)
	}
	if err = s.receipt(s.status(), ""); err != nil {
		fatal(err)
	}
	fmt.Printf("LIVE_SETUP status=%s data_root=%s project_id=%s task_id=%s qualification_executed=%v\n", s.status(), s.dataRoot, s.state.ProjectID, s.state.TaskID, s.state.RunID != "")
}

func fatal(err error) { fmt.Fprintln(os.Stderr, "LIVE_SETUP_ERROR:", err); os.Exit(1) }

func openSetup(ctx context.Context, requested string) (*setup, error) {
	repo, err := os.Getwd()
	if err != nil {
		return nil, err
	}
	if _, err = os.Stat(filepath.Join(repo, "AGENTS.md")); err != nil {
		return nil, fmt.Errorf("run from repository root: %w", err)
	}
	dataRoot := requested
	if dataRoot == "" {
		dataRoot = filepath.Join(repo, dataRelative)
	}
	dataRoot, err = filepath.Abs(dataRoot)
	if err != nil {
		return nil, err
	}
	candidate := filepath.Join(repo, candidateRelative)
	if info, e := os.Stat(candidate); e != nil || !info.IsDir() {
		return nil, errors.New("fixed candidate source unavailable")
	}
	lease, err := rt.AcquireDataRootLease(dataRoot)
	if err != nil {
		return nil, err
	}
	s := &setup{repo: repo, candidate: candidate, policyPath: filepath.Join(repo, policyRelative), dataRoot: lease.Root(), lease: lease}
	if err = s.loadState(); err != nil {
		s.close()
		return nil, err
	}
	db, err := store.Open(filepath.Join(s.dataRoot, "researchos.sqlite"))
	if err != nil {
		s.close()
		return nil, err
	}
	s.db = db
	if err = store.Bootstrap(ctx, db, filepath.Join(repo, "migrations/sqlite/0001_bootstrap.sql")); err != nil {
		s.close()
		return nil, err
	}
	s.svc, err = domain.New(db, filepath.Join(repo, "spec/v2.0/contracts"), filepath.Join(repo, "migrations/sqlite/0002_domain.sql"))
	if err != nil {
		s.close()
		return nil, err
	}
	s.host, err = hostboundary.New(hostboundary.Config{DB: db, Dir: filepath.Join(s.dataRoot, "host"), ContractsDir: filepath.Join(repo, "spec/v2.0/contracts"), MigrationFile: filepath.Join(repo, "migrations/sqlite/0002_domain.sql"), SchemaDir: filepath.Join(repo, "internal/api/contracts")})
	if err != nil {
		s.close()
		return nil, err
	}
	s.owner, err = s.host.BootstrapOwner(ctx)
	if err != nil {
		s.close()
		return nil, err
	}
	s.ownerToken = s.owner.Session.Token
	if s.state.OwnerID != "" && s.state.OwnerID != s.owner.PrincipalID {
		s.close()
		return nil, errors.New("private LIVE state owner differs from OS-bound owner")
	}
	s.state.Version, s.state.DataRoot, s.state.Candidate = 1, s.dataRoot, candidate
	s.state.OwnerID, s.state.HostID = s.owner.PrincipalID, s.host.InstanceID()
	if err = s.saveState(); err != nil {
		s.close()
		return nil, err
	}
	return s, nil
}

func (s *setup) close() {
	if s.nativeCancel != nil {
		s.nativeCancel()
	}
	if s.db != nil {
		_ = s.db.Close()
	}
	if s.lease != nil {
		_ = s.lease.Close()
	}
}

func (s *setup) loadState() error {
	raw, err := os.ReadFile(filepath.Join(s.dataRoot, "live_setup_state.json"))
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	if err = json.Unmarshal(raw, &s.state); err != nil {
		return err
	}
	if s.state.Version != 1 || s.state.DataRoot != s.dataRoot || s.state.Candidate != s.candidate {
		return errors.New("private LIVE state is bound to a different root or candidate")
	}
	return nil
}

func (s *setup) saveState() error {
	raw, err := json.MarshalIndent(s.state, "", "  ")
	if err != nil {
		return err
	}
	name := filepath.Join(s.dataRoot, "live_setup_state.json")
	tmp := name + ".tmp"
	if err = os.WriteFile(tmp, raw, 0600); err != nil {
		return err
	}
	return os.Rename(tmp, name)
}

func (s *setup) status() string {
	if s.state.Qualified {
		return "QUALIFIED"
	}
	if s.state.RunID != "" {
		return "QUALIFICATION_STARTED"
	}
	if s.state.PlanReady {
		return "READY_TO_QUALIFY"
	}
	if s.state.ProjectID != "" {
		return "PROJECT_BOOTSTRAPPED"
	}
	return "OWNER_BOOTSTRAPPED"
}

func (s *setup) receipt(status, reason string) error {
	name := filepath.Join(s.repo, "execution/v2.4/receipts/W14/W14-01", fmt.Sprintf("live_setup_codex_%s_%s.json", time.Now().UTC().Format("20060102T150405.000000000Z"), domain.ID()))
	if err := os.MkdirAll(filepath.Dir(name), 0755); err != nil {
		return err
	}
	content := map[string]any{"version": 1, "status": status, "stage": s.status(), "reason": reason, "created_at": time.Now().UTC().Format(time.RFC3339Nano), "data_root": s.dataRoot, "candidate": s.candidate, "owner_principal_id": s.state.OwnerID, "host_instance_id": s.state.HostID, "authorized_workspace_ref": nullable(s.state.WorkspaceRef), "project_id": nullable(s.state.ProjectID), "runtime_id": nullable(s.state.RuntimeID), "profile_artifact_id": nullable(s.state.ProfileID), "profile_hash": nullable(s.state.ProfileHash), "qualification_task_id": nullable(s.state.TaskID), "qualification_run_id": nullable(s.state.RunID), "acceptance_receipt_id": nullable(s.state.AcceptanceID), "credential_ref": nullable(s.state.CredentialRef), "qualification_executed": s.state.RunID != "", "qualified": s.state.Qualified, "actual_cost": nil, "independent_construction_acceptance": "NOT_RUN"}
	raw, err := json.MarshalIndent(content, "", "  ")
	if err != nil {
		return err
	}
	f, err := os.OpenFile(name, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.Write(append(raw, '\n'))
	return err
}

func nullable(s string) any {
	if s == "" {
		return nil
	}
	return s
}

// Production wiring shared by the preparation and qualification phases.
func (s *setup) authority() (*localworkspace.Authority, *domain.SchemaDoc, *localworkspace.Scanner, error) {
	doc, err := api.ClientProtocolDocument()
	if err != nil {
		return nil, nil, nil, err
	}
	return localworkspace.NewAuthority(s.host), doc, localworkspace.NewScanner(), nil
}
