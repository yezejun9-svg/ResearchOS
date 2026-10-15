//go:build windows

package ownedcorestop

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"os"
	"path/filepath"
	"strings"

	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

const (
	InputSchema      = "researchos.owned-core-stop-input.v1"
	PlanSchema       = "researchos.owned-core-stop-plan.v1"
	ResultSchema     = "researchos.owned-core-stop-result.v1"
	SourceBaseCommit = "4f4023c956f84d65743f39ce77d6c8899a21ada1"
	OldRun           = "f3dcb996b2e43cf52cba874be7abfc70"
	OldDispatch      = "705b11ec99044fef19e85f57e2d2b712"
	OldRequest       = "bc269e772ada7e1bce54439fd080550c"
)

type EvidenceRef struct {
	Kind   string `json:"kind"`
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
}

// Input names the historical subject and evidence locations, not permission
// flags. It cannot assert that a proof is accepted or a native child is closed.
type Input struct {
	Schema           string                 `json:"schema"`
	OperationID      string                 `json:"operation_id"`
	SourceRepository string                 `json:"source_repository"`
	DataRoot         string                 `json:"data_root"`
	CorePID          uint32                 `json:"core_pid"`
	Subject          store.OwnedStopSubject `json:"subject"`
	Evidence         []EvidenceRef          `json:"evidence"`
	PlanReviewPath   string                 `json:"plan_review_path"`
}

type Plan struct {
	Schema           string                             `json:"schema"`
	OperationID      string                             `json:"operation_id"`
	SourceBaseCommit string                             `json:"source_base_commit"`
	OutputDir        string                             `json:"output_dir"`
	InputSHA256      string                             `json:"input_sha256"`
	Input            Input                              `json:"input"`
	Native           supervisor.OwnedCoreNativeIdentity `json:"native"`
	Host             host.OwnedCoreStopPublicIdentity   `json:"host"`
	BackupPath       string                             `json:"backup_path"`
	BackupSHA256     string                             `json:"backup_sha256"`
	Baseline         store.OwnedStopCensus              `json:"baseline"`
	PreflightSafety  store.OwnedStopSafetySnapshot      `json:"preflight_safety"`
	EvidenceSHA256   string                             `json:"evidence_sha256,omitempty"`
	Eligibility      string                             `json:"eligibility"`
	Missing          []string                           `json:"missing,omitempty"`
}

type Result struct {
	Schema      string                          `json:"schema"`
	OperationID string                          `json:"operation_id"`
	PlanSHA256  string                          `json:"plan_sha256"`
	State       string                          `json:"state"`
	Reason      string                          `json:"reason,omitempty"`
	Native      *supervisor.OwnedCoreNativeExit `json:"native,omitempty"`
	Postflight  *store.OwnedStopCensus          `json:"postflight,omitempty"`
}

func digest(raw []byte) string { sum := sha256.Sum256(raw); return hex.EncodeToString(sum[:]) }
func validSHA(s string) bool {
	b, e := hex.DecodeString(s)
	return e == nil && len(b) == 32 && strings.ToLower(s) == s
}
func validID(s string) bool {
	b, e := hex.DecodeString(s)
	return e == nil && len(b) == 16 && strings.ToLower(s) == s
}

func strictJSON(raw []byte, v any) error {
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(v); err != nil {
		return err
	}
	var rest any
	if err := d.Decode(&rest); err != io.EOF {
		return errors.New("trailing JSON data")
	}
	return nil
}
func canonicalJSON(v any) ([]byte, error) {
	raw, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return nil, e
	}
	return append(raw, '\n'), nil
}

func readInput(path string) (Input, string, error) {
	var in Input
	raw, e := os.ReadFile(path)
	if e != nil {
		return in, "", e
	}
	if len(raw) > 64<<10 {
		return in, "", errors.New("bounded input required")
	}
	if e = strictJSON(raw, &in); e != nil {
		return in, "", e
	}
	if e = validateInput(in); e != nil {
		return in, "", e
	}
	return in, digest(raw), nil
}

func validateInput(in Input) error {
	if in.Schema != InputSchema || !validID(in.OperationID) || in.CorePID == 0 {
		return errors.New("invalid input identity")
	}
	if in.Subject.Run != OldRun || in.Subject.Epoch != 1 || in.Subject.DispatchKey != OldDispatch || in.Subject.RequestKey != OldRequest || in.Subject.Project == "" {
		return errors.New("subject differs from frozen historical window")
	}
	for _, path := range []string{in.SourceRepository, in.DataRoot} {
		if !filepath.IsAbs(path) || filepath.Clean(path) != path || len(filepath.VolumeName(path)) != 2 {
			return errors.New("canonical absolute local roots required")
		}
	}
	return nil
}

func validatePlan(p Plan) error {
	if p.Schema != PlanSchema || p.SourceBaseCommit != SourceBaseCommit || p.OperationID != p.Input.OperationID || p.OutputDir == "" || p.BackupPath != filepath.Join(p.OutputDir, "backup.sqlite") || !validSHA(p.InputSHA256) || !validSHA(p.BackupSHA256) || p.Native.PID != p.Input.CorePID || p.Host.DataRoot != p.Input.DataRoot || p.Host.SID != p.Native.SID || p.Host.SID != p.Native.ParentSID {
		return errors.New("plan field binding invalid")
	}
	if e := validateInput(p.Input); e != nil {
		return e
	}
	if p.Baseline.SHA256 == "" || p.Baseline.QuickCheck != "ok" || p.Host.SchemaVersion != 24 {
		return errors.New("plan baseline invalid")
	}
	return nil
}
