//go:build windows

package host

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"testing"
	"time"

	"golang.org/x/sys/windows"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

func firstUseHost(t *testing.T) *Host {
	t.Helper()
	root := t.TempDir()
	db, err := store.Open(filepath.Join(root, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	if err := store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	h, err := New(Config{DB: db, Dir: filepath.Join(root, "private-host"),
		ContractsDir: "../../spec/v2.0/contracts", MigrationFile: "../../migrations/sqlite/0002_domain.sql",
		SchemaDir: "../../internal/api/contracts"})
	if err != nil {
		t.Fatal(err)
	}
	return h
}

func nativeFirstUseFrame(t *testing.T, kind string, payload any) []byte {
	t.Helper()
	raw, err := json.Marshal(map[string]any{"kind": kind, "client_id": "local-cli", "payload": payload})
	if err != nil {
		t.Fatal(err)
	}
	return raw
}

func TestNativePublishedBootstrapRebindsAndRenews(t *testing.T) {
	h := firstUseHost(t)
	frame := nativeFirstUseFrame(t, KindUserBootstrapRequest, map[string]any{})
	first, err := h.HandleNative(frame, true, nil)
	if err != nil {
		t.Fatal(err)
	}
	before, err := h.ReadSessionFile()
	if err != nil || before.Token == "" || bytes.Contains(first, []byte(before.Token)) {
		t.Fatalf("bootstrap credential boundary: %v", err)
	}
	second, err := h.HandleNative(frame, true, nil)
	if err != nil {
		t.Fatal(err)
	}
	after, err := h.ReadSessionFile()
	if err != nil || after.Token == "" || after.Token == before.Token || bytes.Contains(second, []byte(after.Token)) {
		t.Fatalf("rebind credential boundary: %v", err)
	}
	var revoked int
	if err := h.db.QueryRow("SELECT revoked FROM auth_credentials WHERE token_hash=?", domain.Digest([]byte(before.Token))).Scan(&revoked); err != nil || revoked != 1 {
		t.Fatalf("prior token remains active: %d %v", revoked, err)
	}
	owners, total, _ := h.scanPrincipals(context.Background())
	if owners != 1 || total != 1 {
		t.Fatalf("bootstrap created extra principals: owners=%d total=%d", owners, total)
	}
	if _, err := h.HandleNative(frame, false, nil); !errors.Is(err, ErrFrameUntrusted) {
		t.Fatalf("untrusted native bootstrap accepted: %v", err)
	}
}

func TestNativeWorkspaceChooseNeedsConfirmedHostSelection(t *testing.T) {
	h := firstUseHost(t)
	selected := filepath.Join(t.TempDir(), "chosen")
	if err := os.Mkdir(selected, 0700); err != nil {
		t.Fatal(err)
	}
	suggestion := filepath.Join(t.TempDir(), "untrusted-suggestion")
	frame := nativeFirstUseFrame(t, KindWorkspaceChooseRequest, map[string]any{"requested_path": suggestion, "requested_access": AccessReadWrite})
	if _, err := h.HandleNative(frame, true, nil); !errors.Is(err, ErrUntrustedPathChoice) {
		t.Fatalf("unconfirmed caller path accepted: %v", err)
	}
	called := 0
	reply, err := h.HandleNative(frame, true, func(initial string) (string, error) {
		called++
		if initial != suggestion {
			t.Fatalf("dialog suggestion changed: %q", initial)
		}
		return selected, nil
	})
	if err != nil {
		t.Fatal(err)
	}
	if called != 1 {
		t.Fatalf("user chooser invoked %d times", called)
	}
	var parsed struct {
		Payload struct {
			Ref string `json:"selection_ref"`
		} `json:"payload"`
	}
	if err := json.Unmarshal(reply, &parsed); err != nil || parsed.Payload.Ref == "" {
		t.Fatalf("selection reply: %s %v", reply, err)
	}
	rec, err := h.ConsumeSelection(parsed.Payload.Ref, "local-cli")
	if err != nil || rec.RealPath != selected || rec.Access != AccessReadWrite {
		t.Fatalf("selected root not bound: %+v %v", rec, err)
	}
	if _, err := h.ConsumeSelection(parsed.Payload.Ref, "local-cli"); !errors.Is(err, ErrSelectionUsed) {
		t.Fatalf("single-use selection reused: %v", err)
	}
	if len(h.Roots()) != 1 || h.Roots()[0].RealPath != selected {
		t.Fatal("selected root registry mismatch")
	}
}

func TestNativeWorkspaceChooseRequiresExplicitNullablePath(t *testing.T) {
	h := firstUseHost(t)
	selected := filepath.Join(t.TempDir(), "actual-choice")
	if err := os.Mkdir(selected, 0700); err != nil {
		t.Fatal(err)
	}
	called := 0
	chooser := func(initial string) (string, error) {
		called++
		if initial != "" {
			t.Fatalf("null requested_path should produce empty chooser hint, got %q", initial)
		}
		return selected, nil
	}
	for _, tc := range []struct {
		name    string
		payload map[string]any
	}{
		{"missing-required-path", map[string]any{"requested_access": AccessReadWrite}},
		{"invalid-access", map[string]any{"requested_path": nil, "requested_access": "INVALID"}},
		{"unknown-field", map[string]any{"requested_path": nil, "requested_access": AccessReadWrite, "extra": true}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			frame := nativeFirstUseFrame(t, KindWorkspaceChooseRequest, tc.payload)
			if _, err := h.HandleNative(frame, true, chooser); !errors.Is(err, ErrFrameShape) {
				t.Fatalf("invalid request reached chooser: %v", err)
			}
			if called != 0 {
				t.Fatalf("chooser invoked for invalid request: %d", called)
			}
		})
	}
	frame := nativeFirstUseFrame(t, KindWorkspaceChooseRequest,
		map[string]any{"requested_path": nil, "requested_access": AccessReadWrite})
	reply, err := h.HandleNative(frame, true, chooser)
	if err != nil || called != 1 {
		t.Fatalf("explicit null failed to invoke actual chooser once: called=%d err=%v", called, err)
	}
	var parsed struct {
		Payload struct {
			Ref string `json:"selection_ref"`
		} `json:"payload"`
	}
	if err := json.Unmarshal(reply, &parsed); err != nil || parsed.Payload.Ref == "" {
		t.Fatalf("chooser selection reply invalid: %v", err)
	}
	rec, err := h.ConsumeSelection(parsed.Payload.Ref, "local-cli")
	if err != nil || rec.RealPath != selected || rec.Access != AccessReadWrite {
		t.Fatalf("actual chosen path not bound: %+v %v", rec, err)
	}
}

func TestNativeWindowsFolderChooserAPIsPresent(t *testing.T) {
	for _, proc := range []*windows.LazyProc{shell32Browse, shell32Path, ole32Free, user32Send} {
		if err := proc.Find(); err != nil {
			t.Fatalf("native folder dialog API unavailable: %v", err)
		}
	}
}

func TestNativePipePublishedBootstrap(t *testing.T) {
	h := firstUseHost(t)
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	pipe := PipeName(h.InstanceID())
	go func() { done <- h.ServeNative(ctx, pipe) }()
	t.Cleanup(func() {
		cancel()
		// ConnectNamedPipe may already be waiting for another same-user client.
		// A final invalid frame wakes that instance without changing host state.
		_, _ = DialNative(pipe, nativeFirstUseFrame(t, "NATIVE_UNKNOWN", map[string]any{}))
		select {
		case <-done:
		case <-time.After(5 * time.Second):
			t.Error("native pipe did not stop")
		}
	})
	reply, err := DialNative(pipe, nativeFirstUseFrame(t, KindUserBootstrapRequest, map[string]any{}))
	if err != nil {
		t.Fatal(err)
	}
	var frame struct {
		Kind string `json:"kind"`
	}
	if err := json.Unmarshal(reply, &frame); err != nil || frame.Kind != KindUserBootstrapResult {
		t.Fatalf("pipe bootstrap refused: %s %v", reply, err)
	}
	sess, err := h.ReadSessionFile()
	if err != nil || sess.Token == "" || bytes.Contains(reply, []byte(sess.Token)) {
		t.Fatalf("pipe credential boundary: %v", err)
	}
}
