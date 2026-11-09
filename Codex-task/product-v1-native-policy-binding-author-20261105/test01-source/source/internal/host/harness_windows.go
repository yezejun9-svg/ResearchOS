//go:build windows

package host

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	rt "researchos.local/research-os/adapters/runtime"
	"strings"
	"time"
)

// HarnessPrincipal revalidates the OS-bound Host, then returns its existing
// authenticated domain principal. HTTP identity claims cannot construct it.
func (h *Host) HarnessPrincipal(ctx context.Context) (string, error) {
	if err := ctx.Err(); err != nil {
		return "", err
	}
	if _, err := h.reverify(); err != nil {
		return "", err
	}
	principal := h.boundPrincipal()
	if principal == "" {
		return "", ErrBadState
	}
	if _, err := h.ConfigurationMetadata(ctx, principal, "", nil); err != nil {
		return "", err
	}
	return principal, nil
}

// NewCodexHarness discovers the native CLI executable only. No provider key,
// model settings, or CLI authentication files are opened by the Host.
func (h *Host) NewCodexHarness(ctx context.Context) (rt.CodexDriver, error) {
	executable, err := exec.LookPath("codex.exe")
	if err != nil {
		// npm's public shim keeps the real Windows executable in its installed package.
		roots := []string{filepath.Join(os.Getenv("APPDATA"), "npm")}
		if shim, e := exec.LookPath("codex.cmd"); e == nil {
			roots = append(roots, filepath.Dir(shim))
		}
		unique := map[string]string{}
		for _, root := range roots {
			for _, pattern := range []string{
				filepath.Join(root, "node_modules", "@openai", "codex", "vendor", "*", "codex", "codex.exe"),
				filepath.Join(root, "node_modules", "@openai", "codex", "node_modules", "@openai", "codex-win32-*", "vendor", "*", "bin", "codex.exe"),
			} {
				matches, _ := filepath.Glob(pattern)
				for _, match := range matches {
					unique[strings.ToLower(filepath.Clean(match))] = match
				}
			}
		}
		if len(unique) != 1 {
			return nil, errors.New("CODEX_EXECUTABLE_UNAVAILABLE")
		}
		for _, match := range unique {
			executable = match
		}
	}
	executable, err = filepath.Abs(executable)
	if err != nil {
		return nil, err
	}
	f, err := os.Open(executable)
	if err != nil {
		return nil, err
	}
	digest := sha256.New()
	_, err = io.Copy(digest, f)
	closeErr := f.Close()
	if err != nil || closeErr != nil {
		return nil, errors.New("CODEX_EXECUTABLE_UNAVAILABLE")
	}
	descriptor := rt.CodexDescriptor{Present: true, ExecutableHash: "sha256:" + hex.EncodeToString(digest.Sum(nil)), AuthState: "UNPROBED", ConfigurationControlled: true}
	versionCtx, versionCancel := context.WithTimeout(ctx, 5*time.Second)
	versionCommand := exec.CommandContext(versionCtx, executable, "--version")
	versionCommand.Env = rt.Environment("")
	versionCommand.Dir = h.dir
	versionOutput, versionErr := versionCommand.Output()
	versionCancel()
	if versionErr == nil && strings.TrimSpace(string(versionOutput)) == "codex-cli 0.166.0" {
		descriptor.Version = "0.166.0"
	} else {
		descriptor.ConfigurationControlled = false
		descriptor.UnavailableReason = "UNSUPPORTED_NATIVE_CLI_VERSION"
	}
	// A bounded metadata command, performed once by the actual Host composition,
	// grants no model execution qualification. GET capabilities never probes.
	metadataCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	command := exec.CommandContext(metadataCtx, executable, "login", "status")
	command.Env = rt.Environment("")
	command.Dir = h.dir
	output, err := command.CombinedOutput()
	descriptor.AuthCheckedAt = time.Now().UTC().Format(time.RFC3339Nano)
	if err == nil && strings.Contains(strings.ToLower(string(output)), "logged in") {
		descriptor.AuthState = "LOGGED_IN"
		descriptor.AuthKind = "other"
		if strings.Contains(strings.ToLower(string(output)), "chatgpt") {
			descriptor.AuthKind = "chatgpt"
		} else if strings.Contains(strings.ToLower(string(output)), "api key") {
			descriptor.AuthKind = "api_key"
		}
	} else if err != nil {
		descriptor.AuthState = "LOGGED_OUT"
	}
	// The requested permission profile is supplied per launch from trusted Host
	// code. Managed native platform requirements remain authoritative (D03).
	return rt.NewCodexCLI(rt.CodexCLIOptions{Executable: executable, Descriptor: descriptor})
}
