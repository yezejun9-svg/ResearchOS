//go:build windows

package ownedcorestop

import (
	"encoding/base64"
	"encoding/json"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

func TestCompiledGrantStrictCanonicalAndActionBoundary(t *testing.T) {
	sha := strings.Repeat("a", 64)
	sid := "S-1-5-21-fixture"
	data := `C:\fixture\data`
	db := filepath.Join(data, "researchos.sqlite")
	out := `C:\fixture\operation`
	now := time.Now().UTC().Truncate(time.Second)
	g := operationGrant{Schema: grantSchema, GrantKind: "PREFLIGHT_ONLY", OperationID: strings.Repeat("b", 32), IssuedAt: now.Format(time.RFC3339Nano), NotBefore: now.Format(time.RFC3339Nano), ExpiresAt: now.Add(20 * time.Minute).Format(time.RFC3339Nano), Purpose: "EXACT_RETAINED_CORE_CRASH_STOP", TrustedOperatorSID: sid, DataRoot: grantFileIdentity{data, 1, 2}, Database: grantFileIdentity{db, 1, 3}, OperationDir: grantFileIdentity{out, 1, 4}, Native: grantNativeIdentity{PID: 10, Created100NS: "123", SID: sid, ImagePath: `C:\fixture\core.exe`, ImageSHA256: sha, ImageVolume: 1, ImageIndex: 5, ParentPID: 9, ParentCreated100NS: "100", ParentSID: sid, ParentImagePath: `C:\fixture\desktop.exe`, ParentImageSHA256: sha, ParentImageVolume: 1, ParentImageIndex: 6}, Host: host.OwnedCoreStopPublicIdentity{DataRoot: data, Database: db, DatabaseVolume: 1, DatabaseIndex: 3, SID: sid, PrincipalRef: "fixture", HostID: "fixture", OwnerID: "fixture", OwnerRoot: "fixture", HostStateSHA256: sha, SchemaVersion: 24}, Subject: store.OwnedStopSubject{Project: "fixture", Run: OldRun, Epoch: 1, DispatchKey: OldDispatch, RequestKey: OldRequest}, RequiredProofKinds: append([]string{}, proofKinds...), RulesetVersion: "strict-closure-v1", SchemaSHA256: sha, AllowedActions: []string{"preflight", "inspect"}, TerminateCount: 0, Proposal: grantDocument{`C:\fixture\proposal.json`, sha}, PreflightScope: grantDocument{`C:\fixture\scope.json`, sha}, PreflightReview: grantDocument{`C:\fixture\review.json`, sha}, HistoricalManifest: grantDocument{`C:\fixture\historical.json`, sha}}
	raw, err := json.Marshal(g)
	if err != nil {
		t.Fatal(err)
	}
	raw, err = canonicalMapJSON(raw)
	if err != nil {
		t.Fatal(err)
	}
	parsed, err := parseCompiledOperationGrant(base64.StdEncoding.EncodeToString(raw))
	if err != nil {
		t.Fatal(err)
	}
	if parsed.digest != digest(raw) {
		t.Fatal("compiled grant digest differs")
	}
	if _, err = parsed.checkAction("commit", true); err == nil {
		t.Fatal("preflight grant allowed commit")
	}
	parsed.expires = time.Now().Add(-time.Second)
	if _, err = parsed.checkAction("preflight", true); err == nil {
		t.Fatal("expired preflight allowed action")
	}
	if _, err = parsed.checkAction("inspect", false); err != nil {
		t.Fatalf("expired read-only inspect denied: %v", err)
	}
	for _, bad := range []string{"", base64.StdEncoding.EncodeToString([]byte(`{"schema":"a","schema":"b"}`)), base64.StdEncoding.EncodeToString(raw) + "\n"} {
		if _, err = parseCompiledOperationGrant(bad); err == nil {
			t.Fatalf("malformed grant accepted: %q", bad)
		}
	}
	var unknown map[string]any
	if err = json.Unmarshal(raw, &unknown); err != nil {
		t.Fatal(err)
	}
	unknown["wildcard"] = true
	unknownRaw, err := json.Marshal(unknown)
	if err != nil {
		t.Fatal(err)
	}
	unknownRaw, err = canonicalMapJSON(unknownRaw)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = parseCompiledOperationGrant(base64.StdEncoding.EncodeToString(unknownRaw)); err == nil {
		t.Fatal("unknown grant field accepted")
	}
	g.Proposal.SHA256 = strings.Repeat("0", 64)
	zeroRaw, err := json.Marshal(g)
	if err != nil {
		t.Fatal(err)
	}
	zeroRaw, err = canonicalMapJSON(zeroRaw)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = parseCompiledOperationGrant(base64.StdEncoding.EncodeToString(zeroRaw)); err == nil {
		t.Fatal("zero digest accepted")
	}
}

func TestOwnedCoreStopMissingHistoricalProofNeverEligible(t *testing.T) {
	plan := Plan{OperationID: strings.Repeat("a", 32), Input: Input{SourceRepository: t.TempDir()}}
	_, missing := validateHistoricalEvidence(plan)
	if len(missing) < len(proofKinds) {
		t.Fatalf("missing F01/native/effect proofs were accepted: %v", missing)
	}
	for _, ref := range []EvidenceRef{{Kind: "f01_ready", Path: filepath.Join(t.TempDir(), "forged.json"), SHA256: strings.Repeat("a", 64)}} {
		plan.Input.Evidence = append(plan.Input.Evidence, ref)
	}
	_, missing = validateHistoricalEvidence(plan)
	if len(missing) == 0 {
		t.Fatal("caller-selected evidence outside independent namespace accepted")
	}
}

func TestOwnedCoreStopCallerReviewCannotOmitExactScope(t *testing.T) {
	plan := Plan{Input: Input{SourceRepository: t.TempDir(), PlanReviewPath: filepath.Join(t.TempDir(), "review.json")}}
	if err := validatePlanReview(plan, strings.Repeat("a", 64)); err == nil {
		t.Fatal("non-independent review path accepted")
	}
}

func TestNativeExitProofRequiresExplicitNumericCapturePerClass(t *testing.T) {
	sha := strings.Repeat("a", 64)
	for _, kind := range []string{"worker_native_exit", "verifier_native_exit"} {
		for _, tc := range []struct {
			name  string
			field string
			value any
			omit  bool
			want  bool
		}{
			{"explicit exit zero", "native_exit_code", 0, false, true},
			{"explicit exit nonzero", "native_exit_code", 137, false, true},
			{"missing exit", "native_exit_code", nil, true, false},
			{"null exit", "native_exit_code", nil, false, false},
			{"negative exit", "native_exit_code", -1, false, false},
			{"overflow exit", "native_exit_code", int64(1) << 32, false, false},
			{"fractional exit", "native_exit_code", 0.5, false, false},
			{"explicit wait zero", "native_wait_result", 0, false, true},
			{"missing wait", "native_wait_result", nil, true, false},
			{"null wait", "native_wait_result", nil, false, false},
			{"nonzero wait", "native_wait_result", 258, false, false},
			{"negative wait", "native_wait_result", -1, false, false},
			{"overflow wait", "native_wait_result", int64(1) << 32, false, false},
			{"fractional wait", "native_wait_result", 0.5, false, false},
		} {
			t.Run(kind+"/"+tc.name, func(t *testing.T) {
				fields := map[string]any{
					"kind": kind, "native_pid": 8, "native_created_ns": 123,
					"native_wait_api": "WaitForSingleObject", "native_wait_result": 0,
					"native_exit_api": "GetExitCodeProcess", "native_exit_code": 0,
					"native_handle_record_sha256": sha,
				}
				if tc.omit {
					delete(fields, tc.field)
				} else {
					fields[tc.field] = tc.value
				}
				raw, err := json.Marshal(fields)
				if err != nil {
					t.Fatal(err)
				}
				var proof historicalEvidence
				err = decodeCanonicalAuthority(raw, &proof)
				got := err == nil && nativeExitEvidenceComplete(proof, 9)
				if got != tc.want {
					t.Fatalf("native proof %s accepted=%v want=%v decode=%v: %s", tc.name, got, tc.want, err, raw)
				}
			})
		}
	}
}
