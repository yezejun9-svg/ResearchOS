//go:build windows

package host

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"os"
	"path/filepath"
	rt "researchos.local/research-os/adapters/runtime"
	"testing"
)

func TestCodexQualificationBuildPinsClosedByDefault(t *testing.T) {
	d := rt.CodexDescriptor{Present: true, Version: "0.166.0", ExecutableHash: "sha256:binary", AuthState: "LOGGED_IN", AuthKind: "chatgpt", ConfigurationControlled: true}
	closed := closedQualificationHarness(d)
	metadata := closed.Descriptor()
	if !metadata.Present || metadata.Version != d.Version || metadata.ExecutableHash != d.ExecutableHash || metadata.AuthState != d.AuthState || metadata.AuthKind != d.AuthKind || metadata.UnavailableReason != "QUALIFICATION_REQUIRED" || metadata.NativeTransport != rt.CodexRPCTransport {
		t.Fatal("closed factory lost installation or authentication metadata", metadata)
	}
	if closed.ReadinessSnapshot().State != "UNAVAILABLE" {
		t.Fatal("unconfigured production driver became preparation-ready")
	}
	if _, err := closed.Start(context.Background(), rt.CodexLaunch{}, rt.CodexCallbacks{}); err == nil {
		t.Fatal("closed factory launched a child")
	}
	for _, pins := range [][2]string{{"", ""}, {`C:\synthetic`, ""}, {"", "sha256:" + hex.EncodeToString(make([]byte, 32))}, {"relative", "sha256:" + hex.EncodeToString(make([]byte, 32))}} {
		if _, err := codexQualificationScope(pins[0], pins[1]); err == nil {
			t.Fatalf("unreviewed build pins accepted: %v", pins)
		}
	}
}

func TestCodexQualificationExactSyntheticScopeAndHelperPin(t *testing.T) {
	root := t.TempDir()
	source := filepath.Join(root, "S")
	if err := os.Mkdir(source, 0700); err != nil {
		t.Fatal(err)
	}
	helper := filepath.Join(source, "qualification-helper.exe")
	content := []byte("inert reviewed helper fixture")
	if err := os.WriteFile(helper, content, 0600); err != nil {
		t.Fatal(err)
	}
	sum := sha256.Sum256(content)
	want := "sha256:" + hex.EncodeToString(sum[:])
	scope, err := codexQualificationScope(root, want)
	if err != nil || scope.ApprovedRoot != root || scope.SyntheticSource != source || scope.ShippedHelper != helper || scope.ShippedHelperSHA256 != want {
		t.Fatal("exact synthetic build pins rejected", scope, err)
	}
	if _, err = codexQualificationScope(root, "sha256:"+hex.EncodeToString(make([]byte, 32))); err == nil {
		t.Fatal("wrong reviewed helper digest accepted")
	}
	if err = os.WriteFile(helper, []byte("changed after build"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err = codexQualificationScope(root, want); err == nil {
		t.Fatal("helper mutation accepted")
	}
	if hash, err := codexHostBuildSHA256(); err != nil || len(hash) != 71 || hash[:7] != "sha256:" {
		t.Fatal("actual Host build file metadata unavailable", hash, err)
	}
}

func TestCodexNormalHomeRejectsUncontrolledPaths(t *testing.T) {
	for _, home := range []string{"", "relative\\home", `C:\normal;injected`} {
		if _, err := codexNormalHome(home); err == nil {
			t.Fatalf("accepted uncontrolled home %q", home)
		}
	}
	got, err := codexNormalHome(`C:\Users\owner\..\owner`)
	if err != nil || got != filepath.Clean(`C:\Users\owner\..\owner`) {
		t.Fatalf("normal home rejected: %q, %v", got, err)
	}
}

func TestHarnessHostPrincipalActualBinding(t *testing.T) {
	h := firstUseHost(t)
	if _, err := h.BootstrapOwner(context.Background()); err != nil {
		t.Fatal(err)
	}
	actual, err := h.HarnessPrincipal(context.Background())
	if err != nil || actual == "" || actual != h.boundPrincipal() {
		t.Fatal("actual Host binding missing", err)
	}
	original := h.state.PrincipalRef
	h.state.PrincipalRef = "foreign"
	if _, err = h.HarnessPrincipal(context.Background()); err == nil {
		t.Fatal("spoofed identity accepted")
	}
	h.state.PrincipalRef = original
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err = h.HarnessPrincipal(ctx); err == nil {
		t.Fatal("cancelled auth accepted")
	}
}
