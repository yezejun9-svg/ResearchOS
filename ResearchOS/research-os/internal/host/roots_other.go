//go:build !windows

package host

import "errors"

// The workspace-root binding depends on handle-level volume/index pinning and reparse-point
// detection. Elsewhere the host must refuse to register a root rather than pretend it verified
// one, so a non-Windows build cannot claim W17 workspace security.
var errPlatformUnsupported = errors.New("workspace root binding requires Windows handle semantics")

func fileIdentity(string) (string, uint64, string, error) { return "", 0, "", errPlatformUnsupported }
func chainHasReparsePoint(string) (bool, error)           { return false, errPlatformUnsupported }
