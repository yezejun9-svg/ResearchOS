//go:build windows

package host

import (
	"context"
	"path/filepath"
	"testing"
)

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
