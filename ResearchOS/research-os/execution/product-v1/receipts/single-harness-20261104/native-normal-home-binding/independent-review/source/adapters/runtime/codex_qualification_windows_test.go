//go:build windows

package runtime

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"sync"
	"testing"
	"time"

	"researchos.local/research-os/internal/qualificationprobe"
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
	rpc.qualifier = q
	dir := filepath.Join(root, "run")
	q.observation = nativeQualificationObservation{TaskID: "task", RunID: "run", Epoch: "1", SourceBindingHash: "sha256:source", Source: source, Directory: dir, NativeHash: hash, HelperHash: q.options.ShippedHelperSHA256, HostBuildHash: q.options.HostBuildSHA256, TemplateHash: CodexRPCPolicyIdentity(hash).RequestedConfigSHA256, EnvironmentHash: Hash(mustJSON(Environment(""))), NormalHome: home, HostBoot: q.boot, Until: time.Now().Add(time.Minute)}
	e := CodexTurnEvidence{PolicyIdentity: CodexRPCPolicyIdentity(hash), RenderedConfigSHA256: codexRPCConfigHash("researchos-readonly-0123456789abcdef0123456789abcdef", filepath.Join(dir, "cwd"), source), SourceBindingHash: "sha256:source", ProfileNonce: "researchos-readonly-0123456789abcdef0123456789abcdef", ThreadID: "thread", TaskID: "task", RunID: "run", Epoch: "1", Process: CodexIdentity{PID: 42, Created: 123, Job: "model-owned-job"}}
	return q, e
}
func TestQualificationNormalHomeSpelling(t *testing.T) {
	trusted := `C:\Users\yqyyds`
	for _, tc := range []struct {
		name, normalHome, userProfile string
		want                          bool
	}{
		{"same", trusted, trusted, true},
		{"forward slashes", trusted, "C:/Users/yqyyds", true},
		{"mixed case and separators", trusted, "c:/uSeRs/YQYYDS", true},
		{"changed user", trusted, `C:\Users\other`, false},
		{"prefix sibling", trusted, `C:\Users\yqyyds2`, false},
		{"changed drive", trusted, `D:\Users\yqyyds`, false},
		{"changed root", trusted, `C:\Other\yqyyds`, false},
		{"empty profile", trusted, "", false},
		{"empty trusted home", "", trusted, false},
		{"relative", trusted, `Users\yqyyds`, false},
		{"drive relative", trusted, `C:Users\yqyyds`, false},
		{"dot segment", trusted, `C:\Users\.\yqyyds`, false},
		{"parent segment", trusted, `C:\Users\other\..\yqyyds`, false},
		{"NUL", trusted, trusted + "\x00", false},
		{"CRLF", trusted, trusted + "\r\n", false},
		{"semicolon", trusted, trusted + ";", false},
		{"invalid character", trusted, trusted + "?", false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			if got := sameQualificationNormalHome(tc.normalHome, tc.userProfile); got != tc.want {
				t.Fatalf("sameQualificationNormalHome(%q, %q) = %t, want %t", tc.normalHome, tc.userProfile, got, tc.want)
			}
		})
	}
}

func TestQualificationNormalHomeEarlyGateAcceptsSlashEquivalentProfile(t *testing.T) {
	q, _ := qualifiedFixture(t)
	q.rpc.options.NormalHome = filepath.Clean(q.rpc.options.NormalHome)
	t.Setenv("USERPROFILE", filepath.ToSlash(q.rpc.options.NormalHome))
	// A deliberately mismatched synthetic helper digest stops before collector
	// launch, after the home gate and its existing private-root checks.
	q.options.ShippedHelperSHA256 = Hash([]byte("different synthetic helper"))
	in := CodexLaunch{TaskID: "task", RunID: "run", Epoch: "1", Workspace: q.options.SyntheticSource, Directory: filepath.Join(q.options.ApprovedRoot, "run"), SourceBindingHash: "sha256:source"}
	obs, err := q.ensureLaunch(context.Background(), in)
	if err == nil || err.Error() != "QUALIFICATION_BOOTSTRAP_BLOCKED" || obs.ReceiptPath == "" || !obs.PreflightNoChild || obs.Capture.PID != 0 || q.state != "FAILED" {
		t.Fatal("separator-equivalent home failed the early gate or reached a child", obs.ReceiptPath, obs.Capture.PID, q.state, err)
	}
}

func TestQualificationNormalHomeEarlyGateRejectsChangedOrEmptyProfile(t *testing.T) {
	for _, tc := range []struct{ name, profile string }{
		{"changed", `C:\Users\a-different-user`},
		{"empty", ""},
	} {
		t.Run(tc.name, func(t *testing.T) {
			q, _ := qualifiedFixture(t)
			t.Setenv("USERPROFILE", tc.profile)
			in := CodexLaunch{TaskID: "task", RunID: "run", Epoch: "1", Workspace: q.options.SyntheticSource, Directory: filepath.Join(q.options.ApprovedRoot, "run"), SourceBindingHash: "sha256:source"}
			obs, err := q.ensureLaunch(context.Background(), in)
			if err == nil || err.Error() != "QUALIFICATION_SCOPE_MISMATCH" || obs.ReceiptPath != "" || q.state != "FAILED" {
				t.Fatal("changed or empty profile passed the prelaunch gate", obs.ReceiptPath, q.state, err)
			}
			if _, err := os.Stat(filepath.Join(q.options.ApprovedRoot, "receipts")); !errors.Is(err, os.ErrNotExist) {
				t.Fatal("prelaunch gate created qualification artifacts", err)
			}
		})
	}
}

func TestCodexNativeQualificationEnsureIsSingleUseAndBound(t *testing.T) {
	q, e := qualifiedFixture(t)
	if err := q.Ensure(context.Background(), e); err != nil {
		t.Fatal(err)
	}
	if err := q.Ensure(context.Background(), e); err == nil {
		t.Fatal("reused qualification observation")
	}
	q, e = qualifiedFixture(t)
	wrong := e
	wrong.SourceBindingHash = "stale"
	if err := q.Ensure(context.Background(), wrong); err == nil {
		t.Fatal("stale first use qualified")
	}
	if err := q.Ensure(context.Background(), e); err == nil {
		t.Fatal("failed first use was retried")
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

func TestMalformedLaunchDoesNotConsumeQualification(t *testing.T) {
	q, _ := qualifiedFixture(t)
	q.state = "NOT_STARTED"
	d := &qualifiedRPC{rpc: q.rpc, q: q}
	if gate := d.rpc.readiness(); gate.State != "PREPARATION_READY" {
		t.Fatal("fixture is not preparation ready", gate)
	}
	valid := CodexLaunch{TaskID: "task", RunID: "run", Epoch: "1", Workspace: q.options.SyntheticSource, Prompt: "synthetic request", Directory: filepath.Join(q.options.ApprovedRoot, "run"), SourceBindingHash: "sha256:source", Timeout: time.Minute}
	validCallbacks := CodexCallbacks{BeforeResume: func(CodexIdentity) error { return nil }, BeforeModelTurn: func(CodexTurnEvidence) error { return nil }, Event: func(CodexEvent) error { return nil }}
	cases := map[string]func(*CodexLaunch, *CodexCallbacks){
		"epoch_noncanonical": func(v *CodexLaunch, _ *CodexCallbacks) { v.Epoch = "01" },
		"epoch_zero":         func(v *CodexLaunch, _ *CodexCallbacks) { v.Epoch = "0" },
		"prompt_empty":       func(v *CodexLaunch, _ *CodexCallbacks) { v.Prompt = "  " },
		"prompt_oversize":    func(v *CodexLaunch, _ *CodexCallbacks) { v.Prompt = strings.Repeat("x", 65537) },
		"callback_resume":    func(_ *CodexLaunch, v *CodexCallbacks) { v.BeforeResume = nil },
		"callback_turn":      func(_ *CodexLaunch, v *CodexCallbacks) { v.BeforeModelTurn = nil },
		"callback_event":     func(_ *CodexLaunch, v *CodexCallbacks) { v.Event = nil },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			in, cb := valid, validCallbacks
			change(&in, &cb)
			if h, err := d.Start(context.Background(), in, cb); err == nil || h != nil {
				t.Fatal("malformed request reached qualification", h, err)
			}
			if q.state != "NOT_STARTED" {
				t.Fatal("malformed request consumed one-shot qualification", q.state)
			}
		})
	}
}

func TestQualificationEvaluatorKeepsViolationAndHostControls(t *testing.T) {
	if got := qualificationPreferredReason("QUALIFICATION_POLICY_VIOLATION", "QUALIFICATION_INCOMPLETE"); got != "QUALIFICATION_POLICY_VIOLATION" {
		t.Fatal("violation overwritten", got)
	}
	if got := qualificationPreferredReason("QUALIFICATION_INCOMPLETE", "QUALIFICATION_POLICY_VIOLATION"); got != "QUALIFICATION_POLICY_VIOLATION" {
		t.Fatal("violation lost to ordering", got)
	}
	for _, tc := range []struct {
		name  string
		event qualificationprobe.Event
		want  string
	}{
		{"denied_wrong_errno", qualificationprobe.Event{Errno: 2}, "QUALIFICATION_INCOMPLETE"},
		{"denied_opened", qualificationprobe.Event{Opened: true}, "QUALIFICATION_POLICY_VIOLATION"},
		{"loopback_opened", qualificationprobe.Event{Opened: true}, "QUALIFICATION_POLICY_VIOLATION"},
		{"source_wrong_digest", qualificationprobe.Event{Opened: true, Digest: "wrong", Bytes: 4}, "QUALIFICATION_CONTROL_INVALID"},
	} {
		name := "denied_read"
		switch tc.name {
		case "loopback_opened":
			name = "loopback_connect"
		case "source_wrong_digest":
			name = "source_read"
		}
		if got := evaluateQualificationCase(name, tc.event, "sha256:expected", 4); got != tc.want {
			t.Fatal(tc.name, got, tc.want)
		}
	}
	root := t.TempDir()
	create := filepath.Join(root, "create-denied.txt")
	if err := hostCreateControl(create); err != nil {
		t.Fatal("Host positive create control failed", err)
	}
	if _, err := os.Lstat(create); !errors.Is(err, os.ErrNotExist) {
		t.Fatal("Host control left target", err)
	}
	if err := os.WriteFile(create, []byte("already exists"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := hostCreateControl(create); err == nil {
		t.Fatal("existing target accepted as fresh create")
	}
}

func TestCodexNativeQualificationSourcePrivateAccessor(t *testing.T) {
	q, _ := qualifiedFixture(t)
	d := &qualifiedRPC{rpc: q.rpc, q: q, prepareLaunch: q.ensureLaunch, delegateStart: q.rpc.Start}
	if source, ok := CodexNativeQualificationSource(d); !ok || source != q.options.SyntheticSource {
		t.Fatal("private synthetic source missing", source, ok)
	}
	if source, ok := CodexNativeQualificationSource(q.rpc); ok || source != "" {
		t.Fatal("ordinary driver asserted B3 source", source, ok)
	}
	var nilQualified *qualifiedRPC
	if source, ok := CodexNativeQualificationSource(nilQualified); ok || source != "" {
		t.Fatal("nil wrapper asserted B3 source", source, ok)
	}
	d.q.boot = ""
	if source, ok := CodexNativeQualificationSource(d); ok || source != "" {
		t.Fatal("missing private boot asserted B3 source", source, ok)
	}
}

type unrelatedQualificationHandle struct{}

func (unrelatedQualificationHandle) Cancel() {}
func (unrelatedQualificationHandle) Wait(context.Context) (CodexResult, error) {
	return CodexResult{}, nil
}

type serializedQualificationHandle struct{ facts CodexPreparationFailure }

func (serializedQualificationHandle) Cancel() {}
func (serializedQualificationHandle) Wait(context.Context) (CodexResult, error) {
	return CodexResult{}, errors.New("serialized facts are not authority")
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
	raw, err := json.Marshal(preparationFailure("QUALIFICATION_CONTROL_INVALID", obs))
	if err != nil {
		t.Fatal(err)
	}
	var copied CodexPreparationFailure
	if err := json.Unmarshal(raw, &copied); err != nil {
		t.Fatal(err)
	}
	if _, ok := CodexPreparationFailureForHandle(serializedQualificationHandle{facts: copied}); ok {
		t.Fatal("serialized facts minted private proof")
	}
	h := makeHandle()
	if _, ok := CodexPreparationFailureForHandle(h); ok {
		t.Fatal("running handle minted terminal proof")
	}
	close(h.done)
	if facts, ok := CodexPreparationFailureForHandle(h); !ok || !facts.NoModelDelegation || !facts.NoQualificationChild || facts.QualificationPID != 0 || facts.NativeHash != obs.NativeHash || facts.HelperHash != obs.HelperHash || facts.SyntheticSource != obs.Source {
		t.Fatal("known preflight no-child proof rejected", facts, ok)
	}
	for name, mutate := range map[string]func(*CodexPreparationFailure){
		"native": func(f *CodexPreparationFailure) { f.NativeHash = "other" },
		"helper": func(f *CodexPreparationFailure) { f.HelperHash = "other" },
		"source": func(f *CodexPreparationFailure) { f.SyntheticSource = "other" },
	} {
		t.Run(name, func(t *testing.T) {
			h := makeHandle()
			mutate(h.preparationFailure)
			close(h.done)
			if _, ok := CodexPreparationFailureForHandle(h); ok {
				t.Fatal("altered preparation provenance accepted")
			}
		})
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

type qualificationLifecycleFakeHandle struct {
	done chan struct{}
	once sync.Once
}

func (h *qualificationLifecycleFakeHandle) Cancel() { h.once.Do(func() { close(h.done) }) }
func (h *qualificationLifecycleFakeHandle) Wait(ctx context.Context) (CodexResult, error) {
	select {
	case <-h.done:
		return CodexResult{State: "CANCELLED"}, nil
	case <-ctx.Done():
		return CodexResult{}, ctx.Err()
	}
}
func qualificationWrapperFixture(t *testing.T) (*qualifiedRPC, CodexLaunch, CodexCallbacks, nativeQualificationObservation) {
	t.Helper()
	q, _ := qualifiedFixture(t)
	q.state = "NOT_STARTED"
	d := &qualifiedRPC{rpc: q.rpc, q: q}
	in := CodexLaunch{TaskID: "task", RunID: "run", Epoch: "1", Workspace: q.options.SyntheticSource, Prompt: "synthetic request", Directory: q.observation.Directory, SourceBindingHash: "sha256:source", Timeout: time.Second}
	cb := CodexCallbacks{BeforeResume: func(CodexIdentity) error { return nil }, BeforeModelTurn: func(CodexTurnEvidence) error { return nil }, Event: func(CodexEvent) error { return nil }}
	obs := q.observation
	obs.PreflightNoChild = true
	return d, in, cb, obs
}

func TestQualificationWrapperDelegatesOnlyRemainingBudget(t *testing.T) {
	d, in, cb, obs := qualificationWrapperFixture(t)
	delegated := make(chan time.Duration, 1)
	d.prepareLaunch = func(context.Context, CodexLaunch) (nativeQualificationObservation, error) {
		time.Sleep(15 * time.Millisecond)
		return obs, nil
	}
	d.delegateStart = func(_ context.Context, got CodexLaunch, _ CodexCallbacks) (CodexHandle, error) {
		delegated <- got.Timeout
		h := &qualificationLifecycleFakeHandle{done: make(chan struct{})}
		h.Cancel()
		return h, nil
	}
	h, err := d.Start(context.Background(), in, cb)
	if err != nil {
		t.Fatal(err)
	}
	result, err := h.Wait(context.Background())
	if err != nil || result.State != "CANCELLED" {
		t.Fatal("fake delegated handle not observed", result, err)
	}
	remaining := <-delegated
	if remaining <= 0 || remaining >= in.Timeout {
		t.Fatal("fresh or expired delegate timeout", remaining, in.Timeout)
	}
	if _, ok := CodexPreparationFailureForHandle(h); ok {
		t.Fatal("delegated handle projected pre-RPC failure")
	}
}

func TestQualificationWrapperCancelAndDeadlineNeverDelegate(t *testing.T) {
	for _, mode := range []string{"cancel", "deadline"} {
		t.Run(mode, func(t *testing.T) {
			d, in, cb, obs := qualificationWrapperFixture(t)
			entered := make(chan struct{})
			delegated := make(chan struct{}, 1)
			if mode == "deadline" {
				in.Timeout = 30 * time.Millisecond
			}
			d.prepareLaunch = func(ctx context.Context, _ CodexLaunch) (nativeQualificationObservation, error) {
				close(entered)
				<-ctx.Done()
				if mode == "deadline" {
					return obs, nil
				}
				return obs, errors.New("QUALIFICATION_CANCELLED_BEFORE_RPC")
			}
			d.delegateStart = func(context.Context, CodexLaunch, CodexCallbacks) (CodexHandle, error) {
				delegated <- struct{}{}
				return nil, errors.New("fake must never delegate")
			}
			h, err := d.Start(context.Background(), in, cb)
			if err != nil {
				t.Fatal(err)
			}
			<-entered
			if mode == "cancel" {
				h.Cancel()
			}
			_, err = h.Wait(context.Background())
			if err == nil {
				t.Fatal("cancelled or expired preparation returned success")
			}
			select {
			case <-delegated:
				t.Fatal("RPC delegate attempted after preparation ended")
			default:
			}
			facts, ok := CodexPreparationFailureForHandle(h)
			if !ok || !facts.NoQualificationChild || !facts.NoModelDelegation || facts.NativeHash != obs.NativeHash || facts.HelperHash != obs.HelperHash || facts.SyntheticSource != obs.Source {
				t.Fatal("terminal private failure lost provenance", facts, ok)
			}
		})
	}
}

func TestQualificationWrapperDelegateErrorCannotMintPreRPCFailure(t *testing.T) {
	d, in, cb, obs := qualificationWrapperFixture(t)
	d.prepareLaunch = func(context.Context, CodexLaunch) (nativeQualificationObservation, error) { return obs, nil }
	d.delegateStart = func(context.Context, CodexLaunch, CodexCallbacks) (CodexHandle, error) {
		return nil, errors.New("synthetic delegate failure")
	}
	h, err := d.Start(context.Background(), in, cb)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := h.Wait(context.Background()); err == nil {
		t.Fatal("delegate error hidden")
	}
	if _, ok := CodexPreparationFailureForHandle(h); ok {
		t.Fatal("attempted RPC Start minted pre-RPC proof")
	}
}

func TestQualificationWrapperCancelForwardsToDelegate(t *testing.T) {
	d, in, cb, obs := qualificationWrapperFixture(t)
	started := make(chan *qualificationLifecycleFakeHandle, 1)
	d.prepareLaunch = func(context.Context, CodexLaunch) (nativeQualificationObservation, error) { return obs, nil }
	d.delegateStart = func(context.Context, CodexLaunch, CodexCallbacks) (CodexHandle, error) {
		fake := &qualificationLifecycleFakeHandle{done: make(chan struct{})}
		started <- fake
		return fake, nil
	}
	h, err := d.Start(context.Background(), in, cb)
	if err != nil {
		t.Fatal(err)
	}
	fake := <-started
	h.Cancel()
	select {
	case <-fake.done:
	case <-time.After(time.Second):
		t.Fatal("cancel was not forwarded to owned delegate")
	}
	if _, err := h.Wait(context.Background()); err != nil {
		t.Fatal(err)
	}
	if _, ok := CodexPreparationFailureForHandle(h); ok {
		t.Fatal("cancelled delegate projected pre-RPC failure")
	}
}
