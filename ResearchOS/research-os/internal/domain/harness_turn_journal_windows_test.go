//go:build windows

package domain

import (
	"os"
	"path/filepath"
	"testing"

	rt "researchos.local/research-os/adapters/runtime"
)

func TestHarnessTurnJournalExclusiveAndSanitized(t *testing.T) {
	root := t.TempDir()
	parent := filepath.Join(root, "runtime-dispatches", "owned-run")
	if err := os.MkdirAll(parent, 0700); err != nil {
		t.Fatal(err)
	}
	e := rt.CodexTurnEvidence{PolicyIdentity: rt.CodexPolicyIdentity{Revision: rt.CodexRPCPolicyRevision,
		Transport: rt.CodexRPCTransport, HelperContract: rt.CodexRPCHelperContract,
		BinarySHA256: "sha256:binary", RequestedConfigSHA256: "sha256:template"},
		RenderedConfigSHA256: "sha256:rendered", SourceBindingHash: "sha256:source", ProfileNonce: "nonce",
		ThreadID: "thread", TaskID: "task", RunID: "run", Epoch: "1",
		Process: rt.CodexIdentity{PID: 42, Created: 123, Job: "owned-job"}, CaptureBytes: 12}
	d := Object{"dispatch_key": "owned-run", "manifest_hash": "sha256:manifest"}
	if err := writeHarnessTurnAuthorization(root, "owned-run", e, d, "worker"); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(parent, "native-turn-authorization.json")
	first, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := Decode(first); err != nil {
		t.Fatal(err)
	}
	if err := writeHarnessTurnAuthorization(root, "owned-run", e, d, "worker"); err == nil {
		t.Fatal("second authorization replaced exclusive marker")
	}
	second, err := os.ReadFile(path)
	if err != nil || string(first) != string(second) {
		t.Fatal("exclusive marker changed")
	}
	if err := writeHarnessTurnAuthorization(root, "..", e, d, "worker"); err == nil {
		t.Fatal("parent traversal accepted")
	}
	if err := writeHarnessTurnAuthorization(root, "missing", e, d, "worker"); err == nil {
		t.Fatal("missing owned parent accepted")
	}
}
