//go:build windows

package host

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"researchos.local/research-os/internal/canonical"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/verifier"
	"researchos.local/research-os/ops/supervisor"
)

type RuntimeVerifierInstallation struct {
	Schema         string   `json:"schema"`
	ServiceID      string   `json:"service_id"`
	Protocol       string   `json:"protocol"`
	Executable     string   `json:"executable"`
	ExecutableHash string   `json:"executable_hash"`
	SourceCommit   string   `json:"source_commit"`
	Arguments      []string `json:"arguments"`
}

// LoadRuntimeVerifierInstallation reads a local administrator's bounded install
// manifest. SourceCommit is declared build provenance, not proof of OS isolation.
// The actual executable bytes, PID and creation time are verified again at start.
func LoadRuntimeVerifierInstallation(path string) (RuntimeVerifierInstallation, error) {
	var install RuntimeVerifierInstallation
	raw, e := readRuntimeManagedFile(path, 64<<10)
	if e != nil {
		return install, e
	}
	if e = decodeRuntimeManaged(raw, &install); e != nil {
		return install, e
	}
	if install.Schema != "researchos.runtime-verifier-installation.v1" || install.ServiceID != verifier.ServiceID || install.Protocol != verifier.Protocol || len(install.Arguments) != 0 || len(install.SourceCommit) != 40 {
		return install, errors.New("fixed runtime verifier installation required")
	}
	if _, e = hex.DecodeString(install.SourceCommit); e != nil {
		return install, errors.New("verifier build commit invalid")
	}
	if e = verifyRuntimeVerifierImage(install); e != nil {
		return install, e
	}
	return install, nil
}
func verifyRuntimeVerifierImage(install RuntimeVerifierInstallation) error {
	// Direct trusted Go callers have the same installation contract as the
	// managed startup manifest loader.
	if install.Schema != "researchos.runtime-verifier-installation.v1" || install.ServiceID != verifier.ServiceID || install.Protocol != verifier.Protocol || len(install.Arguments) != 0 || len(install.SourceCommit) != 40 {
		return errors.New("fixed runtime verifier installation required")
	}
	if _, e := hex.DecodeString(install.SourceCommit); e != nil {
		return errors.New("verifier build commit invalid")
	}
	raw, e := readRuntimeManagedFile(install.Executable, 128<<20)
	if e != nil || domain.Digest(raw) != install.ExecutableHash || len(raw) < 2 || string(raw[:2]) != "MZ" || !strings.EqualFold(filepath.Ext(install.Executable), ".exe") {
		return errors.New("installed verifier executable bytes unavailable or changed")
	}
	return nil
}
func readRuntimeManagedFile(path string, limit int64) ([]byte, error) {
	if !filepath.IsAbs(path) {
		return nil, errors.New("absolute managed resource path required")
	}
	resolved, e := filepath.EvalSymlinks(path)
	if e != nil || !strings.EqualFold(filepath.Clean(resolved), filepath.Clean(path)) {
		return nil, errors.New("managed resource path unavailable or redirected")
	}
	info, e := os.Lstat(path)
	if e != nil || !info.Mode().IsRegular() || info.Size() < 1 || info.Size() > limit {
		return nil, errors.New("bounded regular managed resource required")
	}
	return os.ReadFile(path)
}
func decodeRuntimeManaged(raw []byte, target any) error {
	strict, e := canonical.JSON(raw)
	if e != nil {
		return errors.New("managed runtime JSON must have unique keys and valid encoding")
	}
	d := json.NewDecoder(strings.NewReader(string(strict)))
	d.DisallowUnknownFields()
	if d.Decode(target) != nil {
		return errors.New("managed runtime request invalid")
	}
	var extra any
	if d.Decode(&extra) != io.EOF {
		return errors.New("managed runtime request has trailing data")
	}
	return nil
}

type runtimeVerifierProcess struct {
	cmd      *exec.Cmd
	in       io.WriteCloser
	out      io.ReadCloser
	cancel   context.CancelFunc
	identity supervisor.ProcessIdentity
	nonce    string
	waited   bool
}

func startRuntimeVerifier(ctx context.Context, install RuntimeVerifierInstallation) (*runtimeVerifierProcess, error) {
	if e := verifyRuntimeVerifierImage(install); e != nil {
		return nil, e
	}
	deadline, cancel := context.WithTimeout(ctx, 3*time.Minute)
	p := &runtimeVerifierProcess{cancel: cancel}
	p.cmd = exec.CommandContext(deadline, install.Executable)
	p.cmd.Dir = filepath.Dir(install.Executable)
	p.cmd.Env = []string{}
	for _, name := range []string{"SystemRoot", "WINDIR", "TEMP", "TMP"} {
		if value := os.Getenv(name); value != "" {
			p.cmd.Env = append(p.cmd.Env, name+"="+value)
		}
	}
	p.cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	// These are dedicated inherited anonymous pipes. No token is placed in argv,
	// environment, a file, logs, worker configuration or the scheduler object.
	var e error
	if p.in, e = p.cmd.StdinPipe(); e != nil {
		cancel()
		return nil, e
	}
	if p.out, e = p.cmd.StdoutPipe(); e != nil {
		p.in.Close()
		cancel()
		return nil, e
	}
	p.cmd.Stderr = io.Discard
	if e = p.cmd.Start(); e != nil {
		p.in.Close()
		p.out.Close()
		cancel()
		return nil, errors.New("installed verifier process could not start")
	}
	ok := false
	defer func() {
		if !ok {
			p.close()
		}
	}()
	p.identity, e = supervisor.ObserveProcess(uint32(p.cmd.Process.Pid))
	if e != nil || "sha256:"+p.identity.ImageSHA256 != install.ExecutableHash {
		return nil, errors.New("verifier process does not match installed image")
	}
	var nonce [32]byte
	if _, e = rand.Read(nonce[:]); e != nil {
		return nil, e
	}
	p.nonce = hex.EncodeToString(nonce[:])
	if e = verifier.WriteFrame(p.in, verifier.Challenge{Protocol: verifier.Protocol, Nonce: p.nonce}); e != nil {
		return nil, errors.New("verifier handshake write failed")
	}
	var hello verifier.Hello
	if e = p.read(deadline, &hello); e != nil {
		return nil, e
	}
	if hello.Protocol != verifier.Protocol || hello.ServiceID != verifier.ServiceID || hello.Nonce != p.nonce || hello.PID != p.cmd.Process.Pid {
		return nil, errors.New("verifier process handshake identity differs")
	}
	ok = true
	return p, nil
}
func (p *runtimeVerifierProcess) read(ctx context.Context, target any) error {
	done := make(chan error, 1)
	go func() { done <- verifier.ReadFrame(p.out, target) }()
	timer := time.NewTimer(20 * time.Second)
	defer timer.Stop()
	select {
	case e := <-done:
		return e
	case <-ctx.Done():
		p.cancel()
		return errors.New("verifier process cancelled")
	case <-timer.C:
		p.cancel()
		return errors.New("verifier reply deadline exceeded")
	}
}
func (p *runtimeVerifierProcess) verify(ctx context.Context, job verifier.Job) (verifier.Result, error) {
	var result verifier.Result
	observed, e := supervisor.ObserveProcess(uint32(p.cmd.Process.Pid))
	if e != nil || observed != p.identity {
		return result, errors.New("verifier process identity changed before credential transfer")
	}
	job.Protocol, job.Nonce = verifier.Protocol, p.nonce
	if e = verifier.WriteFrame(p.in, job); e != nil {
		return result, errors.New("private verifier job transfer failed")
	}
	job.Token = ""
	_ = p.in.Close()
	if e = p.read(ctx, &result); e != nil {
		return result, e
	}
	e = p.cmd.Wait()
	p.waited = true
	if e != nil || result.Protocol != verifier.Protocol || result.Nonce != p.nonce || result.Status != "QUALIFIED" || result.ErrorCode != "" {
		for _, code := range []string{"TASK_RUN_BINDING", "PROFILE_EVIDENCE", "NATIVE_OBSERVATION", "OUTPUT_EVIDENCE", "FROZEN_CHECKS", "DETERMINISTIC_CHECK", "SERVER_ACCEPTANCE", "SERVER_QUALIFICATION"} {
			if result.ErrorCode == code {
				return result, errors.New("independent verifier rejected stage " + code)
			}
		}
		return result, errors.New("independent verifier did not qualify the runtime")
	}
	return result, nil
}
func (p *runtimeVerifierProcess) close() {
	p.cancel()
	_ = p.in.Close()
	_ = p.out.Close()
	if !p.waited {
		_ = p.cmd.Wait()
		p.waited = true
	}
}
