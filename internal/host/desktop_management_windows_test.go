//go:build windows

package host

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/internal/auth"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/verifier"
)

func TestDesktopManagementStrictFrames(t *testing.T) {
	valid := `{"protocol":"researchos-desktop-management/1","message_id":"m1","operation":"PREPARE","host_id":"host-abc","project_id":"p","session_id":"s","model_config_ref":"mc"}`
	if _, e := decodeDesktopManagement([]byte(valid)); e != nil {
		t.Fatal(e)
	}
	for name, raw := range map[string]string{
		"duplicate":          strings.Replace(valid, `"operation":"PREPARE"`, `"operation":"PREPARE","operation":"CONFIRM"`, 1),
		"escaped_duplicate":  strings.Replace(valid, `"operation":"PREPARE"`, `"operation":"PREPARE","\u006fperation":"CONFIRM"`, 1),
		"unknown_field":      strings.TrimSuffix(valid, "}") + `,"token":"forbidden"}`,
		"trailing":           valid + ` {}`,
		"wrong_protocol":     strings.Replace(valid, DesktopManagementProtocol, "researchos-client/2", 1),
		"mixed_confirmation": strings.TrimSuffix(valid, "}") + `,"request_id":"r","request_hash":"h"}`,
		"invalid_utf8":       valid[:len(valid)-1] + string([]byte{0xff}) + "}",
		"oversized":          strings.Repeat(" ", DesktopManagementMaxFrame) + valid,
	} {
		t.Run(name, func(t *testing.T) {
			if _, e := decodeDesktopManagement([]byte(raw)); e == nil {
				t.Fatal("invalid private frame accepted")
			}
		})
	}
	var install RuntimeVerifierInstallation
	if e := decodeRuntimeManaged([]byte(`{"schema":"x","schema":"y"}`), &install); e == nil {
		t.Fatal("shared managed decoder accepted duplicate install field")
	}
	t.Log("private framing: unique keys including escapes, UTF-8, size, exact operations and no credentials")
}

func TestDesktopManagementActualParentIdentityAndPipeOnly(t *testing.T) {
	h := firstUseHost(t)
	input, parentWrite, e := os.Pipe()
	if e != nil {
		t.Fatal(e)
	}
	defer input.Close()
	defer parentWrite.Close()
	parentRead, output, e := os.Pipe()
	if e != nil {
		t.Fatal(e)
	}
	defer parentRead.Close()
	defer output.Close()
	exe, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile(exe)
	if e != nil {
		t.Fatal(e)
	}
	install := RuntimeVerifierInstallation{Schema: "researchos.runtime-verifier-installation.v1", ServiceID: verifier.ServiceID, Protocol: verifier.Protocol, Executable: exe, ExecutableHash: domain.Digest(raw), SourceCommit: strings.Repeat("0", 40), Arguments: []string{}}
	d, e := NewDesktopManagement(h, h.domain, &domain.RuntimeCoordinator{}, "http://127.0.0.1:1", install, input, output, nil)
	if e != nil {
		t.Fatal(e)
	}
	if e = d.verifyParent(); e != nil {
		t.Fatal(e)
	}
	d.parent.CreatedNS++
	if d.verifyParent() == nil {
		t.Fatal("changed parent creation identity accepted")
	}
	d.parent.CreatedNS--
	old := h.peerLookup
	h.peerLookup = func(uint32) (auth.Identity, error) { return auth.Identity{}, nil }
	if d.verifyParent() == nil {
		t.Fatal("foreign OS parent accepted")
	}
	h.peerLookup = old
	file, e := os.Create(filepath.Join(t.TempDir(), "not-a-pipe"))
	if e != nil {
		t.Fatal(e)
	}
	defer file.Close()
	if _, e = NewDesktopManagement(h, h.domain, &domain.RuntimeCoordinator{}, "http://127.0.0.1:1", install, file, output, nil); e == nil {
		t.Fatal("file accepted as private inherited transport")
	}
	if _, e = NewDesktopManagement(h, h.domain, &domain.RuntimeCoordinator{}, "http://127.0.0.1:1", install, input, file, nil); e == nil {
		t.Fatal("output file accepted as private inherited transport")
	}
	// All checks above are offline. The declared PE is only hashed, never run.
	t.Logf("actual parent PID=%d creation=%d image=%s pipe-only transport; model calls=0", d.parent.PID, d.parent.CreatedNS, d.parent.ImageSHA256)
}

func TestManagedRequestFilePrivateACLAndStrictJSON(t *testing.T) {
	path := filepath.Join(t.TempDir(), "request.json")
	if e := os.WriteFile(path, []byte(`{"request_id":"one","request_id":"two"}`), 0600); e != nil {
		t.Fatal(e)
	}
	if e := privateFile(path); e != nil {
		t.Fatal(e)
	}
	if _, e := LoadLocalRuntimeQualificationRequest(path); e == nil {
		t.Fatal("private duplicate request accepted")
	}
	if e := os.WriteFile(path, []byte(`{"request_id":"one"}`), 0600); e != nil {
		t.Fatal(e)
	}
	if _, e := LoadLocalRuntimeQualificationRequest(path); e != nil {
		t.Fatal(e)
	}
	other := filepath.Join(t.TempDir(), "inherited-acl.json")
	if e := os.WriteFile(other, []byte(`{"request_id":"one"}`), 0600); e != nil {
		t.Fatal(e)
	}
	if _, e := LoadLocalRuntimeQualificationRequest(other); e == nil {
		t.Fatal("unprotected request ACL accepted")
	}
}
