package host

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"errors"
	"io"
	"os"
	"path/filepath"
	"testing"

	"researchos.local/research-os/internal/auth"
)

func peerSeamHost() *Host {
	identity := auth.Identity{Kind: "WINDOWS_SID", VID: "S-1-5-21-synthetic-owner", Ref: "synthetic-os-subject"}
	h := &Host{identity: identity}
	h.bootGeneration[0] = 1
	h.peerLookup = func(uint32) (auth.Identity, error) { return identity, nil }
	return h
}

func TestNativePeerCapabilityPreservesFactsAndGeneration(t *testing.T) {
	h := peerSeamHost()
	lookups := 0
	h.peerLookup = func(pid uint32) (auth.Identity, error) {
		lookups++
		if pid != 41 {
			t.Fatalf("lookup used a claimed PID: %d", pid)
		}
		return h.identity, nil
	}
	peer, err := h.verifyNativePeer(41)
	if err != nil || !peer.validFor(h) || peer.pid != 41 || lookups != 1 {
		t.Fatalf("verified transport facts were not retained: %v", err)
	}
	// An unsupported kind exercises only parsing/dispatch; no native handler runs.
	raw := []byte(`{"kind":"UNSUPPORTED_FIXTURE_KIND","client_id":"caller-label-is-not-a-subject","payload":{}}`)
	invocation, err := h.prepareNativeInvocation(raw, &peer)
	if err != nil || invocation.peer == nil || invocation.peer.identity != h.identity || invocation.frame.ClientID != "caller-label-is-not-a-subject" {
		t.Fatalf("dispatch lost peer facts or confused the label with authority: %v", err)
	}
	legacy, err := h.prepareNativeInvocation(raw, nil)
	if err != nil || legacy.peer != nil {
		t.Fatalf("legacy invocation acquired peer evidence: %v", err)
	}
	if _, err = h.HandleNative(raw, true, nil); !errors.Is(err, ErrFrameShape) {
		t.Fatalf("legacy adapter changed: %v", err)
	}
	if _, err = h.HandleNative(raw, false, nil); !errors.Is(err, ErrFrameUntrusted) {
		t.Fatalf("legacy false accepted: %v", err)
	}
	if _, err = h.HandleNative(nil, false, nil); !errors.Is(err, ErrFrameTooLarge) {
		t.Fatalf("legacy error precedence changed: %v", err)
	}
	if _, err = h.handleVerifiedNative(raw, peer, nil); !errors.Is(err, ErrFrameShape) {
		t.Fatalf("typed dispatch changed existing kind rules: %v", err)
	}
	copyHost := *h
	if peer.validFor(&copyHost) {
		t.Fatal("peer capability crossed Host objects with matching metadata")
	}
	h.bootGeneration[1] = 2
	if peer.validFor(h) {
		t.Fatal("old generation remained current")
	}
	if _, err = h.handleVerifiedNative(raw, peer, nil); !errors.Is(err, ErrFrameUntrusted) {
		t.Fatalf("stale generation dispatched: %v", err)
	}
	if _, err = h.dispatchNative(invocation, nil); !errors.Is(err, ErrFrameUntrusted) {
		t.Fatalf("prepared invocation escaped revalidation: %v", err)
	}
	encoded, err := json.Marshal(peer)
	if err != nil || string(encoded) != "{}" {
		t.Fatal("private peer facts became a wire value")
	}
}

func TestNativePeerCapabilityRejectsUntrustedInputs(t *testing.T) {
	cases := []struct {
		name   string
		pid    uint32
		change func(*Host)
	}{
		{"zero-pid", 0, func(*Host) {}},
		{"missing-resolver", 41, func(h *Host) { h.peerLookup = nil }},
		{"failed-lookup", 41, func(h *Host) {
			h.peerLookup = func(uint32) (auth.Identity, error) { return auth.Identity{}, io.ErrUnexpectedEOF }
		}},
		{"foreign-sid-with-same-ref", 41, func(h *Host) {
			h.peerLookup = func(uint32) (auth.Identity, error) { p := h.identity; p.VID = "S-1-5-21-foreign"; return p, nil }
		}},
		{"empty-authority", 41, func(h *Host) {
			h.peerLookup = func(uint32) (auth.Identity, error) { p := h.identity; p.VID = ""; return p, nil }
		}},
		{"wrong-kind", 41, func(h *Host) {
			h.peerLookup = func(uint32) (auth.Identity, error) { p := h.identity; p.Kind = "UNIX_UID"; return p, nil }
		}},
		{"empty-reference", 41, func(h *Host) {
			h.peerLookup = func(uint32) (auth.Identity, error) { p := h.identity; p.Ref = ""; return p, nil }
		}},
		{"uninitialized-generation", 41, func(h *Host) { h.bootGeneration = [32]byte{} }},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			h := peerSeamHost()
			tc.change(h)
			peer, err := h.verifyNativePeer(tc.pid)
			if err == nil || peer.validFor(h) || peer != (verifiedNativePeer{}) {
				t.Fatal("untrusted input produced a capability")
			}
		})
	}
	var absent *Host
	if _, err := absent.verifyNativePeer(41); !errors.Is(err, ErrFrameUntrusted) {
		t.Fatalf("nil Host accepted: %v", err)
	}
	if (verifiedNativePeer{}).validFor(peerSeamHost()) {
		t.Fatal("zero capability accepted")
	}
}

type peerEntropyFailure struct{}

func (peerEntropyFailure) Read([]byte) (int, error) { return 0, io.ErrUnexpectedEOF }

func TestHostBootEntropyFailurePrecedesMutableInitialization(t *testing.T) {
	cases := []struct {
		name    string
		entropy io.Reader
	}{
		{"unavailable", nil}, {"reader-error", peerEntropyFailure{}},
		{"short", bytes.NewReader(bytes.Repeat([]byte{1}, 31))},
		{"zero-generation", bytes.NewReader(make([]byte, 32))},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			path := filepath.Join(t.TempDir(), "host-must-not-be-created")
			// A zero DB would panic if used; these nonexistent inputs must not be read.
			cfg := Config{DB: &sql.DB{}, Dir: path, ContractsDir: "not-read", MigrationFile: "not-read", SchemaDir: "not-read"}
			h, err := newHost(cfg, tc.entropy)
			if h != nil || !errors.Is(err, ErrBadState) {
				t.Fatalf("entropy failure did not stop construction: %v", err)
			}
			if _, err = os.Stat(path); !errors.Is(err, os.ErrNotExist) {
				t.Fatalf("failed entropy caused filesystem setup: %v", err)
			}
		})
	}
}
