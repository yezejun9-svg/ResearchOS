//go:build windows

package protectedstore

import (
	"bytes"
	"context"
	"errors"
	"golang.org/x/sys/windows"
	"os"
	"path/filepath"
	"strings"
	"time"
	"unsafe"
)

const configPipe = `\\.\pipe\ResearchOSVerifierCanary-config-v1`
const configPrefix = "configure-v1:"

func newConfigPipe(serviceSID string) (windows.Handle, error) {
	return newConfigPipeNamed(configPipe, serviceSID)
}
func newConfigPipeNamed(pipeName, serviceSID string) (windows.Handle, error) {
	sd, e := windows.SecurityDescriptorFromString("D:P(A;;FA;;;" + serviceSID + ")(A;;0x100003;;;BA)(A;;0x100003;;;SY)")
	if e != nil {
		return 0, ErrBoundary
	}
	sa := windows.SecurityAttributes{Length: uint32(unsafe.Sizeof(windows.SecurityAttributes{})), SecurityDescriptor: sd}
	h, e := windows.CreateNamedPipe(windows.StringToUTF16Ptr(pipeName), windows.PIPE_ACCESS_DUPLEX|windows.FILE_FLAG_FIRST_PIPE_INSTANCE, windows.PIPE_TYPE_MESSAGE|windows.PIPE_READMODE_MESSAGE|windows.PIPE_NOWAIT|windows.PIPE_REJECT_REMOTE_CLIENTS, 1, 128, 8192, 0, &sa)
	if e != nil {
		return 0, ErrUnavailable
	}
	return h, nil
}
func readConfigFrame(ctx context.Context, h windows.Handle) ([]byte, error) {
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) && ctx.Err() == nil {
		buffer := make([]byte, 8192)
		var n uint32
		err := windows.ReadFile(h, buffer, &n, nil)
		if err == nil && n > 0 {
			return buffer[:n], nil
		}
		wipe(buffer)
		if err != nil && !errors.Is(err, windows.ERROR_NO_DATA) {
			return nil, ErrUnavailable
		}
		if !waitBroker(ctx) {
			break
		}
	}
	return nil, ErrUnavailable
}
func (e *frozenEngine) installCredential(raw []byte) error {
	e.mu.Lock()
	defer e.mu.Unlock()
	if e.ctx.Err() != nil || privateExists(e.store, runMarkerFile) || privateExists(e.store, serviceCredentialFile) {
		return ErrBoundary
	}
	if err := e.store.saveServiceCredential(raw); err != nil {
		return err
	}
	if _, err := e.newCall(); err != nil {
		return err
	}
	e.summary = newFrozenSummary("READY")
	return nil
}
func serveConfigPipe(ctx context.Context, h windows.Handle, engine *frozenEngine) {
	for ctx.Err() == nil {
		err := windows.ConnectNamedPipe(h, nil)
		if err != nil && !errors.Is(err, windows.ERROR_PIPE_CONNECTED) {
			if !errors.Is(err, windows.ERROR_PIPE_LISTENING) {
				windows.DisconnectNamedPipe(h)
			}
			if !waitBroker(ctx) {
				return
			}
			continue
		}
		packet, err := readConfigFrame(ctx, h)
		reply := []byte("configuration-refused-v1")
		if err == nil && bytes.HasPrefix(packet, []byte(configPrefix)) && validCredential(packet[len(configPrefix):]) && engine.installCredential(packet[len(configPrefix):]) == nil {
			reply = []byte("configured-v1")
		}
		wipe(packet)
		var written uint32
		if windows.WriteFile(h, reply, &written, nil) == nil {
			pipeReadFrame(ctx, h, 2*time.Second)
		}
		windows.DisconnectNamedPipe(h)
	}
}

// ConfigureServiceCredential is callable only from the fixed installed binary
// in an elevated installer process. The credential is never an argv/env value.
func ConfigureServiceCredential(raw []byte) error {
	if !windows.GetCurrentProcessToken().IsElevated() || !validCredential(raw) {
		return ErrIsolation
	}
	root, e := CanaryInstallRoot()
	exe, err := os.Executable()
	if e != nil || err != nil || !strings.EqualFold(exe, filepath.Join(root, "broker.exe")) {
		return ErrBoundary
	}
	deadline := time.Now().Add(3 * time.Second)
	done := make(chan error, 1)
	// Own a bounded copy until the worker exits, even if the public deadline wins.
	copy := append([]byte(nil), raw...)
	go func() { defer wipe(copy); done <- configureServiceCredential(copy, deadline) }()
	timer := time.NewTimer(time.Until(deadline))
	defer timer.Stop()
	select {
	case err := <-done:
		return err
	case <-timer.C:
		return ErrUnavailable
	}
}
func configureServiceCredential(raw []byte, deadline time.Time) error {
	file, service, pid, e := connectServicePipe(configPipe)
	if e != nil {
		return e
	}
	defer file.Close()
	defer service.Close()
	if file.SetDeadline(deadline) != nil {
		return ErrUnavailable
	}
	packet := append([]byte(configPrefix), raw...)
	defer wipe(packet)
	if _, e = file.Write(packet); e != nil {
		return ErrUnavailable
	}
	buffer := make([]byte, 128)
	n, e := file.Read(buffer)
	if e != nil || string(buffer[:n]) != "configured-v1" {
		return ErrUnavailable
	}
	if _, e = file.Write([]byte("ack")); e != nil {
		return ErrUnavailable
	}
	status, e := service.Query()
	if e != nil || status.ProcessId != pid {
		return ErrIsolation
	}
	return nil
}
