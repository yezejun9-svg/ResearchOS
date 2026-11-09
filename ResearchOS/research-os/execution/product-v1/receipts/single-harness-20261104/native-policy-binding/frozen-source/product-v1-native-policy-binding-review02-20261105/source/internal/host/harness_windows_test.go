//go:build windows

package host

import (
	"context"
	"testing"
)

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
