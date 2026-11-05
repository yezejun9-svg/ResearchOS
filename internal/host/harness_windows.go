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
	"os/user"
	"path/filepath"
	"regexp"
	rt "researchos.local/research-os/adapters/runtime"
	"strings"
	"time"
)

// These values are supplied only by a reviewed Core build. Empty build pins
// deliberately leave the production factory closed. Neither is read from a
// request, environment variable, persisted receipt, or Native configuration.
var codexQualificationApprovedRoot string
var codexQualificationHelperSHA256 string

var codexBuildDigest = regexp.MustCompile(`^sha256:[0-9a-f]{64}$`)

type closedCodexHarness struct{ descriptor rt.CodexDescriptor }

func (d closedCodexHarness) Descriptor() rt.CodexDescriptor { return d.descriptor }
func (d closedCodexHarness) ReadinessSnapshot() rt.CodexReadiness {
	return rt.CodexReadiness{State: "UNAVAILABLE", Reason: "QUALIFICATION_REQUIRED", PolicyIdentity: rt.CodexExpectedPolicyIdentity(d.descriptor)}
}
func (d closedCodexHarness) Start(context.Context, rt.CodexLaunch, rt.CodexCallbacks) (rt.CodexHandle, error) {
	return nil, errors.New("QUALIFICATION_REQUIRED")
}

func closedQualificationHarness(descriptor rt.CodexDescriptor) rt.CodexDriver {
	descriptor.NativeTransport = rt.CodexRPCTransport
	descriptor.UnavailableReason = "QUALIFICATION_REQUIRED"
	return closedCodexHarness{descriptor: descriptor}
}

// codexQualificationScope checks a build-pinned exact synthetic source and
// shipped helper. It never derives a trusted expected digest from the source.
func codexQualificationScope(root, expectedHelper string) (rt.CodexNativeQualificationOptions, error) {
	var zero rt.CodexNativeQualificationOptions
	if root == "" || expectedHelper == "" || !filepath.IsAbs(root) || strings.Contains(root, ";") || !codexBuildDigest.MatchString(expectedHelper) {
		return zero, errors.New("QUALIFICATION_REQUIRED")
	}
	clean := filepath.Clean(root)
	actual, err := filepath.EvalSymlinks(clean)
	if err != nil || !strings.EqualFold(clean, actual) {
		return zero, errors.New("QUALIFICATION_REQUIRED")
	}
	source := filepath.Join(actual, "S")
	resolvedSource, err := filepath.EvalSymlinks(source)
	if err != nil || !strings.EqualFold(source, resolvedSource) {
		return zero, errors.New("QUALIFICATION_REQUIRED")
	}
	stat, err := os.Stat(source)
	if err != nil || !stat.IsDir() {
		return zero, errors.New("QUALIFICATION_REQUIRED")
	}
	helper := filepath.Join(source, "qualification-helper.exe")
	resolvedHelper, err := filepath.EvalSymlinks(helper)
	if err != nil || !strings.EqualFold(helper, resolvedHelper) {
		return zero, errors.New("QUALIFICATION_REQUIRED")
	}
	helperHash, err := codexFileSHA256(helper)
	if err != nil || helperHash != expectedHelper {
		return zero, errors.New("QUALIFICATION_REQUIRED")
	}
	return rt.CodexNativeQualificationOptions{ApprovedRoot: actual, SyntheticSource: source, ShippedHelper: helper, ShippedHelperSHA256: expectedHelper}, nil
}

func codexFileSHA256(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	digest := sha256.New()
	_, readErr := io.Copy(digest, f)
	closeErr := f.Close()
	if readErr != nil || closeErr != nil {
		return "", errors.New("CODEX_FILE_HASH_UNAVAILABLE")
	}
	return "sha256:" + hex.EncodeToString(digest.Sum(nil)), nil
}

func codexHostBuildSHA256() (string, error) {
	path, err := os.Executable()
	if err != nil {
		return "", err
	}
	path, err = filepath.EvalSymlinks(path)
	if err != nil || !filepath.IsAbs(path) {
		return "", errors.New("CODEX_HOST_BUILD_UNAVAILABLE")
	}
	return codexFileSHA256(path)
}

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
	// The RPC constructor seals the transport; the old exec constructor is never
	// a fallback. NormalHome comes from the actual OS user, not caller input.
	account, err := user.Current()
	if err != nil {
		return nil, errors.New("CODEX_NORMAL_HOME_UNAVAILABLE")
	}
	home, err := codexNormalHome(account.HomeDir)
	if err != nil {
		return nil, err
	}
	scope, err := codexQualificationScope(codexQualificationApprovedRoot, codexQualificationHelperSHA256)
	if err != nil {
		return closedQualificationHarness(descriptor), nil
	}
	scope.HostBuildSHA256, err = codexHostBuildSHA256()
	if err != nil {
		return closedQualificationHarness(descriptor), nil
	}
	driver, err := rt.NewCodexRPCWithNativeQualification(rt.CodexRPCOptions{Executable: executable, Descriptor: descriptor, NormalHome: home}, scope)
	if err != nil {
		return closedQualificationHarness(descriptor), nil
	}
	return driver, nil
}

func codexNormalHome(home string) (string, error) {
	if home == "" || !filepath.IsAbs(home) || strings.Contains(home, ";") {
		return "", errors.New("CODEX_NORMAL_HOME_UNAVAILABLE")
	}
	return filepath.Clean(home), nil
}
