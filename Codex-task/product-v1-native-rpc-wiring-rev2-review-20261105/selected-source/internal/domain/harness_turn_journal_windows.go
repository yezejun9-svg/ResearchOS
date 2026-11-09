//go:build windows

package domain

import (
	"errors"
	"os"
	"path/filepath"
	"strings"

	rt "researchos.local/research-os/adapters/runtime"
)

// writeHarnessTurnAuthorization consumes one Host-side turn authorization at a
// fixed private per-run path. A partial file is deliberately retained: recovery
// may inspect it, but can never use it as a permit or retry the prompt.
func writeHarnessTurnAuthorization(dataRoot, locator string, evidence rt.CodexTurnEvidence, dispatch Object, worker string) error {
	if locator == "" || locator == "." || locator == ".." || filepath.Base(locator) != locator ||
		strings.ContainsAny(locator, `/\`) || worker == "" || evidence.Process.PID == 0 || evidence.Process.Created <= 0 ||
		evidence.Process.Job == "" || evidence.ThreadID == "" || evidence.ProfileNonce == "" ||
		evidence.SourceBindingHash == "" || evidence.RenderedConfigSHA256 == "" || evidence.CaptureBytes < 0 {
		return errors.New("native turn authorization identity incomplete")
	}
	parent := filepath.Join(dataRoot, "runtime-dispatches", locator)
	actual, err := filepath.EvalSymlinks(parent)
	if err != nil || !strings.EqualFold(filepath.Clean(actual), filepath.Clean(parent)) {
		return errors.New("native turn journal directory unavailable or reparse changed")
	}
	info, err := os.Stat(parent)
	if err != nil || !info.IsDir() {
		return errors.New("native turn journal parent is not a directory")
	}
	fact := Object{"schema": "researchos.native-turn-authorization.v1", "state": "HOST_TURN_AUTHORIZATION_CONSUMED",
		"run_id": evidence.RunID, "task_id": evidence.TaskID, "epoch": evidence.Epoch,
		"dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "worker": worker,
		"process": harnessNativeIdentity(evidence.Process), "source_binding_hash": evidence.SourceBindingHash,
		"policy_revision": evidence.PolicyIdentity.Revision, "native_transport": evidence.PolicyIdentity.Transport,
		"helper_contract": evidence.PolicyIdentity.HelperContract, "binary_sha256": evidence.PolicyIdentity.BinarySHA256,
		"template_sha256":        evidence.PolicyIdentity.RequestedConfigSHA256,
		"rendered_config_sha256": evidence.RenderedConfigSHA256, "profile_nonce": evidence.ProfileNonce,
		"thread_id": evidence.ThreadID, "capture_bytes": evidence.CaptureBytes, "evidence_hash": Hash(evidence)}
	raw := append(Bytes(fact), '\n')
	if len(raw) > 8192 || len(raw) < 100 {
		return errors.New("native turn authorization evidence exceeds bound")
	}
	file, err := os.OpenFile(filepath.Join(parent, "native-turn-authorization.json"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	n, writeErr := file.Write(raw)
	if writeErr == nil && n != len(raw) {
		writeErr = errors.New("native turn authorization short write")
	}
	syncErr := file.Sync()
	closeErr := file.Close()
	return errors.Join(writeErr, syncErr, closeErr)
}
