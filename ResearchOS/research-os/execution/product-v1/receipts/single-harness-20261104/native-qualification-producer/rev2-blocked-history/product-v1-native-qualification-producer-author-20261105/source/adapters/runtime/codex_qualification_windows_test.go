//go:build windows

package runtime

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"
)

func qualifiedFixture(t *testing.T) (*nativeQualifier, CodexTurnEvidence) {
	t.Helper()
	home := os.Getenv("USERPROFILE")
	root := t.TempDir()
	source := filepath.Join(root, "S")
	if err := os.Mkdir(source, 0700); err != nil {
		t.Fatal(err)
	}
	nativePath, helperPath := filepath.Join(root, "codex.exe"), filepath.Join(source, "qualification-helper.exe")
	if err := os.WriteFile(nativePath, []byte("synthetic native identity"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(helperPath, []byte("synthetic helper identity"), 0600); err != nil {
		t.Fatal(err)
	}
	hash := Hash([]byte("synthetic native identity"))
	helperHash := Hash([]byte("synthetic helper identity"))
	rpc := &codexRPC{options: CodexRPCOptions{Executable: nativePath, Descriptor: CodexDescriptor{Present: true, Version: "0.166.0", ExecutableHash: hash, AuthState: "LOGGED_IN", ConfigurationControlled: true, NativeTransport: CodexRPCTransport}, NormalHome: home}}
	q := &nativeQualifier{state: "OBSERVED_PASS", rpc: rpc, boot: "private-boot", options: CodexNativeQualificationOptions{ApprovedRoot: root, SyntheticSource: source, ShippedHelper: helperPath, ShippedHelperSHA256: helperHash, HostBuildSHA256: "sha256:" + strings.Repeat("c", 64)}}
	dir := filepath.Join(root, "run")
	q.observation = nativeQualificationObservation{TaskID: "task", RunID: "run", Epoch: "1", SourceBindingHash: "sha256:source", Source: source, Directory: dir, NativeHash: hash, HelperHash: q.options.ShippedHelperSHA256, HostBuildHash: q.options.HostBuildSHA256, TemplateHash: CodexRPCPolicyIdentity(hash).RequestedConfigSHA256, EnvironmentHash: Hash(mustJSON(Environment(""))), NormalHome: home, HostBoot: q.boot, Until: time.Now().Add(time.Minute)}
	e := CodexTurnEvidence{PolicyIdentity: CodexRPCPolicyIdentity(hash), RenderedConfigSHA256: codexRPCConfigHash("researchos-readonly-0123456789abcdef0123456789abcdef", filepath.Join(dir, "cwd"), source), SourceBindingHash: "sha256:source", ProfileNonce: "researchos-readonly-0123456789abcdef0123456789abcdef", ThreadID: "thread", TaskID: "task", RunID: "run", Epoch: "1", Process: CodexIdentity{PID: 42, Created: 123, Job: "model-owned-job"}}
	return q, e
}
func TestCodexNativeQualificationEnsureIsSingleUseAndBound(t *testing.T) {
	q, e := qualifiedFixture(t)
	if err := q.Ensure(context.Background(), e); err != nil {
		t.Fatal(err)
	}
	if err := q.Ensure(context.Background(), e); err == nil {
		t.Fatal("reused qualification observation")
	}
	for name, mutate := range map[string]func(*nativeQualifier, *CodexTurnEvidence){
		"task": func(_ *nativeQualifier, e *CodexTurnEvidence) { e.TaskID = "other" }, "run": func(_ *nativeQualifier, e *CodexTurnEvidence) { e.RunID = "other" },
		"epoch": func(_ *nativeQualifier, e *CodexTurnEvidence) { e.Epoch = "2" }, "source": func(_ *nativeQualifier, e *CodexTurnEvidence) { e.SourceBindingHash = "other" },
		"template": func(_ *nativeQualifier, e *CodexTurnEvidence) { e.RenderedConfigSHA256 = "other" }, "binary": func(q *nativeQualifier, _ *CodexTurnEvidence) {
			q.rpc.options.Descriptor.ExecutableHash = "sha256:" + strings.Repeat("d", 64)
		},
		"helper": func(q *nativeQualifier, _ *CodexTurnEvidence) {
			q.options.ShippedHelperSHA256 = "sha256:" + strings.Repeat("d", 64)
		}, "build": func(q *nativeQualifier, _ *CodexTurnEvidence) {
			q.options.HostBuildSHA256 = "sha256:" + strings.Repeat("d", 64)
		},
		"boot": func(q *nativeQualifier, _ *CodexTurnEvidence) { q.boot = "other" }, "expired": func(q *nativeQualifier, _ *CodexTurnEvidence) { q.observation.Until = time.Now().Add(-time.Second) },
		"helper_bytes": func(q *nativeQualifier, _ *CodexTurnEvidence) {
			_ = os.WriteFile(q.options.ShippedHelper, []byte("changed helper"), 0600)
		},
		"source_root": func(q *nativeQualifier, _ *CodexTurnEvidence) {
			q.options.SyntheticSource = filepath.Dir(q.options.SyntheticSource)
		},
	} {
		t.Run(name, func(t *testing.T) {
			q, e := qualifiedFixture(t)
			mutate(q, &e)
			if err := q.Ensure(context.Background(), e); err == nil {
				t.Fatal("changed live identity qualified")
			}
		})
	}
}
func TestQualificationArgvProjectsExactB1Policy(t *testing.T) {
	nonce := "researchos-readonly-0123456789abcdef0123456789abcdef"
	source := `C:\synthetic\S`
	working := `C:\synthetic\QW`
	helper := `C:\synthetic\S\qualification-helper.exe`
	args, err := qualificationArguments(nonce, source, working, helper, "fixed-plan")
	if err != nil {
		t.Fatal(err)
	}
	base := codexRPCArguments(nonce, source)
	if !reflect.DeepEqual(args[:len(base)-3], base[:len(base)-3]) {
		t.Fatal("qualification policy differs from B1 ordered builder")
	}
	if !reflect.DeepEqual(args[len(args)-10:], []string{"sandbox", "--include-managed-config", "--permission-profile", nonce, "-C", working, "--", helper, "--plan-v1", "fixed-plan"}) {
		t.Fatal("qualification suffix widened", args)
	}
}

type unrelatedQualificationHandle struct{}

func (unrelatedQualificationHandle) Cancel() {}
func (unrelatedQualificationHandle) Wait(context.Context) (CodexResult, error) {
	return CodexResult{}, nil
}
func TestPreparationFailureRequiresPrivateTerminalUndelegatedHandle(t *testing.T) {
	q, _ := qualifiedFixture(t)
	launch := CodexLaunch{TaskID: "task", RunID: "run", Epoch: "1", SourceBindingHash: "sha256:source"}
	obs := q.observation
	obs.PreflightNoChild = true
	makeHandle := func() *qualifiedHandle {
		h := &qualifiedHandle{q: q, launch: launch, done: make(chan struct{}), err: errors.New("QUALIFICATION_CONTROL_INVALID")}
		h.preparationFailure = preparationFailure("QUALIFICATION_CONTROL_INVALID", obs)
		return h
	}
	if _, ok := CodexPreparationFailureForHandle(unrelatedQualificationHandle{}); ok {
		t.Fatal("foreign handle minted preparation proof")
	}
	h := makeHandle()
	if _, ok := CodexPreparationFailureForHandle(h); ok {
		t.Fatal("running handle minted terminal proof")
	}
	close(h.done)
	if facts, ok := CodexPreparationFailureForHandle(h); !ok || !facts.NoModelDelegation || !facts.NoQualificationChild || facts.QualificationPID != 0 {
		t.Fatal("known preflight no-child proof rejected", facts, ok)
	}
	h = makeHandle()
	h.delegateAttempted = true
	close(h.done)
	if _, ok := CodexPreparationFailureForHandle(h); ok {
		t.Fatal("attempted RPC child minted pre-model proof")
	}
	h = makeHandle()
	h.preparationFailure.Reason = "PASS"
	close(h.done)
	if _, ok := CodexPreparationFailureForHandle(h); ok {
		t.Fatal("caller PASS string minted proof")
	}
	h = makeHandle()
	h.preparationFailure.NoQualificationChild = false
	close(h.done)
	if _, ok := CodexPreparationFailureForHandle(h); ok {
		t.Fatal("zero PID without known no-child minted stop proof")
	}
}
