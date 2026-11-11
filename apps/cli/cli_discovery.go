package main

// The per-user locator is a non-secret hint, never a credential or writer lease.
// An explicit path and an existing legacy cwd discovery always take precedence.
import (
	"encoding/json"
	"encoding/json/jsontext"
	"errors"
	"io"
	"net"
	"net/url"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

const sharedHostLocatorSchema = "researchos.shared-host-locator/1"

type sharedHostLocator struct {
	Schema         string `json:"schema"`
	DiscoveryFile  string `json:"discovery_file"`
	DataRoot       string `json:"data_root"`
	HostInstanceID string `json:"host_instance_id"`
}

type resolvedCLIHost struct {
	discovery    discovery
	path, hostID string
}

type discoveryError struct {
	code  string
	cause error
}

func (e *discoveryError) Error() string               { return e.code }
func (e *discoveryError) Unwrap() error               { return e.cause }
func discoveryFailure(code string, cause error) error { return &discoveryError{code, cause} }

func sameHostPath(a, b string) bool {
	if runtime.GOOS == "windows" {
		return strings.EqualFold(filepath.Clean(a), filepath.Clean(b))
	}
	return filepath.Clean(a) == filepath.Clean(b)
}

func localHostURL(value string) bool {
	u, err := url.Parse(value)
	if err != nil || u == nil || (u.Scheme != "http" && u.Scheme != "https") || u.User != nil ||
		u.RawQuery != "" || u.ForceQuery || u.Fragment != "" || u.RawFragment != "" ||
		(u.Path != "" && u.Path != "/") || u.RawPath != "" || u.Hostname() == "" {
		return false
	}
	ip := net.ParseIP(u.Hostname())
	return u.Hostname() == "localhost" || ip != nil && ip.IsLoopback()
}

// A locator may not lead into a network path, a path alias, or a non-regular file.
func canonicalHostPath(value string, directory bool) error {
	if !filepath.IsAbs(value) ||
		strings.ContainsRune(value, '\x00') || runtime.GOOS == "windows" &&
		(len(filepath.VolumeName(value)) != 2 || strings.HasPrefix(value, `\\`)) {
		return discoveryFailure("HOST_LOCATOR_PATH_INVALID", nil)
	}
	info, err := os.Lstat(value)
	if err != nil {
		return discoveryFailure("HOST_LOCATOR_PATH_UNAVAILABLE", err)
	}
	if info.Mode()&os.ModeSymlink != 0 || directory && !info.IsDir() || !directory && !info.Mode().IsRegular() {
		return discoveryFailure("HOST_LOCATOR_PATH_INVALID", nil)
	}
	real, err := filepath.EvalSymlinks(value)
	if err != nil || !sameHostPath(real, value) {
		return discoveryFailure("HOST_LOCATOR_PATH_ALIAS", err)
	}
	return nil
}

func readDiscoveryBytes(file string) ([]byte, error) {
	info, err := os.Lstat(file)
	if err != nil {
		return nil, discoveryFailure("NOT_FOUND", err)
	}
	if !info.Mode().IsRegular() || info.Size() <= 0 || info.Size() > 8192 {
		return nil, discoveryFailure("INVALID_JSON", nil)
	}
	f, err := os.Open(file)
	if err != nil {
		return nil, discoveryFailure("NOT_FOUND", err)
	}
	defer f.Close()
	raw, err := io.ReadAll(io.LimitReader(f, 8193))
	if err != nil || len(raw) > 8192 || !jsontext.Value(raw).IsValid() {
		return nil, discoveryFailure("INVALID_JSON", err)
	}
	return raw, nil
}

func readCLIHost(file string, locator *sharedHostLocator) (resolvedCLIHost, error) {
	result := resolvedCLIHost{path: file}
	raw, err := readDiscoveryBytes(file)
	if err != nil {
		return result, err
	}
	var wire struct {
		URL            string `json:"url"`
		PID            int    `json:"pid"`
		DataDir        string `json:"data_dir"`
		StartedAt      string `json:"started_at"`
		HostInstanceID string `json:"host_instance_id"`
	}
	if locator != nil {
		// The shared discovery protocol has four exact keys. In particular v1's
		// case-insensitive struct matching may not interpret an alias as authority.
		var fields map[string]json.RawMessage
		if err := json.Unmarshal(raw, &fields); err != nil || len(fields) != 4 {
			return result, discoveryFailure("INVALID_JSON", err)
		}
		for _, key := range []string{"url", "pid", "data_dir", "host_instance_id"} {
			if _, exists := fields[key]; !exists {
				return result, discoveryFailure("INVALID_JSON", nil)
			}
		}
	}
	if err := json.Unmarshal(raw, &wire); err != nil {
		return result, discoveryFailure("INVALID_JSON", err)
	}
	result.discovery = discovery{URL: wire.URL, PID: wire.PID, DataDir: wire.DataDir, StartedAt: wire.StartedAt}
	result.hostID = wire.HostInstanceID
	if !localHostURL(wire.URL) {
		return result, discoveryFailure("INVALID_LOCAL_URL", nil)
	}
	if locator != nil {
		if err := canonicalHostPath(file, false); err != nil {
			return result, err
		}
		if err := canonicalHostPath(wire.DataDir, true); err != nil {
			return result, err
		}
		if !sameHostPath(wire.DataDir, locator.DataRoot) || wire.HostInstanceID != locator.HostInstanceID || wire.PID <= 0 {
			return result, discoveryFailure("HOST_LOCATOR_IDENTITY_MISMATCH", nil)
		}
		// Shared discovery follows the same HTTP loopback contract as Desktop.
		u, _ := url.Parse(wire.URL)
		if u.Scheme != "http" || u.Port() == "" || (u.Hostname() != "127.0.0.1" && u.Hostname() != "localhost" && u.Hostname() != "::1") {
			return result, discoveryFailure("INVALID_LOCAL_URL", nil)
		}
	}
	return result, nil
}

func resolveCLIHostDiscovery() (resolvedCLIHost, error) {
	if explicit := os.Getenv("RESEARCHOS_CLI_DISCOVERY"); explicit != "" {
		return readCLIHost(explicit, nil)
	}
	if _, err := os.Lstat(discoveryPath); err == nil {
		return readCLIHost(discoveryPath, nil)
	} else if !os.IsNotExist(err) {
		return resolvedCLIHost{path: discoveryPath}, discoveryFailure("NOT_FOUND", err)
	}
	if os.Getenv("RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED") == "1" {
		return resolvedCLIHost{path: discoveryPath}, discoveryFailure("NOT_FOUND", os.ErrNotExist)
	}
	base := os.Getenv("LOCALAPPDATA")
	if !filepath.IsAbs(base) {
		return resolvedCLIHost{}, discoveryFailure("HOST_LOCATOR_BASE_UNAVAILABLE", nil)
	}
	file := filepath.Join(base, "ResearchOS", "host-locator-v1.json")
	result := resolvedCLIHost{path: file}
	if err := canonicalHostPath(file, false); err != nil {
		return result, err
	}
	raw, err := readDiscoveryBytes(file)
	if err != nil {
		return result, err
	}
	var locator sharedHostLocator
	var fields map[string]json.RawMessage
	if err := json.Unmarshal(raw, &locator); err != nil {
		return result, discoveryFailure("HOST_LOCATOR_INVALID", err)
	}
	if err := json.Unmarshal(raw, &fields); err != nil || len(fields) != 4 || locator.Schema != sharedHostLocatorSchema ||
		!cliHostIDPattern.MatchString(locator.HostInstanceID) {
		return result, discoveryFailure("HOST_LOCATOR_INVALID", err)
	}
	for _, key := range []string{"schema", "discovery_file", "data_root", "host_instance_id"} {
		if _, exists := fields[key]; !exists {
			return result, discoveryFailure("HOST_LOCATOR_INVALID", nil)
		}
	}
	if err := canonicalHostPath(locator.DiscoveryFile, false); err != nil {
		return result, err
	}
	if err := canonicalHostPath(locator.DataRoot, true); err != nil {
		return result, err
	}
	return readCLIHost(locator.DiscoveryFile, &locator)
}

func discoveryErrorCode(err error) string {
	var e *discoveryError
	if errors.As(err, &e) {
		return e.code
	}
	return "HOST_DISCOVERY_UNAVAILABLE"
}
