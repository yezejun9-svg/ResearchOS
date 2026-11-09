//go:build windows

// trustedqual is a local, OS-bound helper for one already-created CLI project.
// It deliberately has no HTTP endpoint for plan creation or qualification start.
package main

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
)

const schema = "researchos.trusted-qualification-host.v1"

// Seed contains no bearer material. The credential_ref resolves solely through
// Host's sealed, read-only vault at dispatch time.
type seed struct {
	Schema              string `json:"schema"`
	RepoRoot            string `json:"repo_root"`
	DataRoot            string `json:"data_root"`
	DiscoveryFile       string `json:"discovery_file"`
	CLIConfigFile       string `json:"cli_config_file"`
	ProjectID           string `json:"project_id"`
	DraftGoalID         string `json:"draft_goal_id"`
	WorkspaceRef        string `json:"workspace_ref"`
	WorkspaceDir        string `json:"workspace_dir"`
	WitnessSHA256       string `json:"witness_sha256"`
	WitnessBytes        int64  `json:"witness_bytes"`
	ProfileFile         string `json:"profile_file"`
	ProfileSHA256       string `json:"profile_sha256"`
	NodeExecutable      string `json:"node_executable"`
	NodeSHA256          string `json:"node_sha256"`
	BundleFile          string `json:"bundle_file"`
	BundleSHA256        string `json:"bundle_sha256"`
	ReadOnlyVaultDir    string `json:"read_only_vault_dir"`
	CredentialRef       string `json:"credential_ref"`
	Provider            string `json:"provider"`
	QualificationPrompt string `json:"qualification_prompt"`
	ProfileRaw          []byte `json:"-"`
	NodeRaw             []byte `json:"-"`
	BundleRaw           []byte `json:"-"`
}

// State is the only holder of the Run lease token. It is stored under Host's
// private directory and never copied into stdout, discovery or a public receipt.
type state struct {
	Schema              string     `json:"schema"`
	SeedSHA256          string     `json:"seed_sha256"`
	HostInstanceID      string     `json:"host_instance_id"`
	OwnerID             string     `json:"owner_id"`
	ProjectID           string     `json:"project_id"`
	DraftGoalID         string     `json:"draft_goal_id"`
	QualificationGoalID string     `json:"qualification_goal_id"`
	RequirementID       string     `json:"requirement_id"`
	RuntimeID           string     `json:"runtime_id"`
	ProfileID           string     `json:"profile_id"`
	ProfileHash         string     `json:"profile_hash"`
	ModelRef            string     `json:"model_ref,omitempty"`
	PreCoordinator      pinnedFile `json:"pre_coordinator,omitempty"`
	TaskID              string     `json:"task_id"`
	ExecutorID          string     `json:"executor_id"`
	SchedulerID         string     `json:"scheduler_id"`
	VerifierID          string     `json:"verifier_id"`
	StartedUTC          string     `json:"started_utc,omitempty"`
	RunID               string     `json:"run_id,omitempty"`
	RunEpoch            int64      `json:"run_epoch,omitempty"`
	RunCreatedAt        string     `json:"run_created_at,omitempty"`
	LeaseToken          string     `json:"lease_token,omitempty"`
	ExecuteClaimedAt    string     `json:"execute_claimed_at,omitempty"`
	AcceptanceID        string     `json:"acceptance_id,omitempty"`
	Qualified           bool       `json:"qualified"`
	Phase               string     `json:"phase"`
}

func main() {
	phase := flag.String("phase", "", "prepare-runtime | finalize-prepare | prepare | admit-only | execute-admitted")
	seedFile := flag.String("seed", "", "absolute pinned public seed JSON")
	started := flag.String("started-utc", "", "Root whole-trial start, required for admit-only")
	readyReceipt := flag.String("ready-receipt", "", "new public READY_ADMISSION_PENDING receipt")
	receiptFile := flag.String("receipt", "", "public per-phase receipt output path")
	draftGoalID := flag.String("draft-goal-id", "", "actual CLI draft goal ID, required for finalize-prepare")
	flag.Parse()
	if *phase != "prepare-runtime" && *phase != "finalize-prepare" && *phase != "prepare" && *phase != "admit-only" && *phase != "execute-admitted" {
		fatal(errors.New("choose one phase"))
	}
	if *seedFile == "" || *receiptFile == "" {
		fatal(errors.New("seed and receipt paths required"))
	}
	cfg, digest, err := readSeed(*seedFile)
	if err != nil {
		fatal(err)
	}
	ctx := context.Background()
	var result domain.Object
	switch *phase {
	case "prepare-runtime":
		result, err = prepareRuntime(ctx, cfg, digest)
	case "finalize-prepare":
		result, err = finalizePrepare(ctx, cfg, digest, *draftGoalID)
	case "prepare":
		result, err = prepare(ctx, cfg, digest)
	case "admit-only":
		result, err = admitOnly(ctx, cfg, digest, *started)
	case "execute-admitted":
		result, err = executeAdmitted(ctx, cfg, digest, *readyReceipt)
	}
	if err != nil {
		fatal(err)
	}
	result["schema"], result["phase"], result["source_seed_sha256"] = schema, *phase, digest
	if err = writeNewReceipt(*receiptFile, result); err != nil {
		fatal(err)
	}
	// execute-admitted blocks in executeAdmitted until stdin closes, a signal, or
	// the Root 300-second deadline; this receipt is then a terminal lifecycle fact.
}

func fatal(err error) {
	// Do not print values from seed, private state, HTTP body or vault to stderr.
	fmt.Fprintln(os.Stderr, "TRUSTED_QUALIFICATION_ERROR:", err)
	os.Exit(1)
}

func hashBytes(raw []byte) string { h := sha256.Sum256(raw); return hex.EncodeToString(h[:]) }
func fileHash(path string) (string, int64, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", 0, err
	}
	defer f.Close()
	h := sha256.New()
	n, err := io.Copy(h, f)
	if err != nil {
		return "", 0, err
	}
	return hex.EncodeToString(h.Sum(nil)), n, nil
}
func readPinnedSeedFile(path, expected string) ([]byte, error) {
	if expected == "" {
		return nil, errors.New("missing pinned digest")
	}
	info, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Mode()&os.ModeSymlink != 0 {
		return nil, errors.New("pinned executable/profile/bundle must be regular files")
	}
	canonical, err := filepath.EvalSymlinks(path)
	if err != nil {
		return nil, err
	}
	if !strings.EqualFold(filepath.Clean(canonical), filepath.Clean(path)) {
		return nil, errors.New("pinned file path must be canonical and non-reparse")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	if !strings.EqualFold(strings.TrimPrefix(expected, "sha256:"), hashBytes(raw)) {
		return nil, errors.New("pinned file digest mismatch")
	}
	return raw, nil
}
func readSeed(path string) (seed, string, error) {
	var s seed
	raw, err := os.ReadFile(path)
	if err != nil {
		return s, "", err
	}
	if err = json.Unmarshal(raw, &s); err != nil {
		return s, "", err
	}
	if s.Schema != schema || s.ProjectID == "" || s.WorkspaceRef == "" || s.CredentialRef == "" || s.Provider == "" || s.QualificationPrompt == "" || s.WitnessBytes < 1 {
		return s, "", errors.New("incomplete public seed")
	}
	for _, p := range []string{s.RepoRoot, s.DataRoot, s.DiscoveryFile, s.CLIConfigFile, s.WorkspaceDir, s.ProfileFile, s.NodeExecutable, s.BundleFile, s.ReadOnlyVaultDir} {
		if !filepath.IsAbs(p) {
			return s, "", errors.New("all seed paths must be absolute")
		}
	}
	if !pathInside(filepath.Join(s.RepoRoot, ".local"), s.DataRoot) || !strings.EqualFold(filepath.Clean(s.WorkspaceDir), filepath.Clean(filepath.Join(s.DataRoot, "workspace"))) || pathInside(s.ReadOnlyVaultDir, s.DataRoot) || pathInside(s.DataRoot, s.ReadOnlyVaultDir) {
		return s, "", errors.New("trial data root/workspace/vault layout differs from frozen isolation")
	}
	if s.ProfileRaw, err = readPinnedSeedFile(s.ProfileFile, s.ProfileSHA256); err != nil {
		return s, "", err
	}
	if s.NodeRaw, err = readPinnedSeedFile(s.NodeExecutable, s.NodeSHA256); err != nil {
		return s, "", err
	}
	if s.BundleRaw, err = readPinnedSeedFile(s.BundleFile, s.BundleSHA256); err != nil {
		return s, "", err
	}
	return s, hashBytes(raw), nil
}
func pathInside(parent, child string) bool {
	rel, err := filepath.Rel(filepath.Clean(parent), filepath.Clean(child))
	if err != nil {
		return false
	}
	return rel == "." || rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator))
}
func statePath(s seed) string {
	return filepath.Join(s.DataRoot, "host", "trusted-qualification-state.json")
}
func loadState(s seed, digest string) (state, error) {
	var v state
	raw, err := os.ReadFile(statePath(s))
	if err != nil {
		return v, err
	}
	if err = json.Unmarshal(raw, &v); err != nil {
		return v, err
	}
	if v.Schema != schema || v.SeedSHA256 != digest || v.ProjectID != s.ProjectID || (s.DraftGoalID != "" && v.DraftGoalID != s.DraftGoalID) {
		return v, errors.New("private state differs from pinned seed")
	}
	return v, nil
}
func saveState(s seed, v state) error {
	raw, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	path := statePath(s)
	if err = os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	temp, err := os.CreateTemp(filepath.Dir(path), "trusted-qualification-*.tmp")
	if err != nil {
		return err
	}
	defer os.Remove(temp.Name())
	if err = temp.Chmod(0600); err != nil {
		temp.Close()
		return err
	}
	if _, err = temp.Write(append(raw, '\n')); err != nil {
		temp.Close()
		return err
	}
	if err = temp.Sync(); err != nil {
		temp.Close()
		return err
	}
	if err = temp.Close(); err != nil {
		return err
	}
	return os.Rename(temp.Name(), path)
}
func writeNewReceipt(path string, body domain.Object) error {
	raw, err := json.MarshalIndent(body, "", "  ")
	if err != nil {
		return err
	}
	if err = os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return err
	}
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	if err != nil {
		return err
	}
	defer f.Close()
	if _, err = f.Write(append(raw, '\n')); err != nil {
		return err
	}
	return f.Sync()
}
func deadline(start string) (context.Context, context.CancelFunc, error) {
	t, err := time.Parse(time.RFC3339Nano, start)
	if err != nil {
		return nil, nil, errors.New("invalid Root started UTC")
	}
	if t.Location() != time.UTC || t.After(time.Now().UTC()) || time.Now().UTC().After(t.Add(300*time.Second)) {
		return nil, nil, errors.New("Root 300-second trial window invalid or expired")
	}
	c, cancel := context.WithDeadline(context.Background(), t.Add(300*time.Second))
	return c, cancel, nil
}
