package host

// Path policy for workspace roots (22 §workspace binding). The published RelativePath pattern is
// re-implemented here because the host must enforce it at access time, not only when a command
// is graded against the schema: the two are cross-checked against the same inputs by the
// qualification program, so neither can silently drift.

import (
	"errors"
	"regexp"
	"strings"
)

var (
	ErrPathAbsolute     = errors.New("ABSOLUTE_PATH")
	ErrPathEscape       = errors.New("PATH_OUT_OF_SCOPE")
	ErrPathDrive        = errors.New("ABSOLUTE_PATH")
	ErrPathNull         = errors.New("INVALID_REQUEST")
	ErrPathEmpty        = errors.New("INVALID_REQUEST")
	ErrPathStream       = errors.New("INVALID_REQUEST")
	ErrPathUNC          = errors.New("ABSOLUTE_PATH")
	ErrPathReparsePoint = errors.New("PATH_OUT_OF_SCOPE")
	ErrRootRevoked      = errors.New("WORKSPACE_REVOKED")
	ErrRootUnknown      = errors.New("NOT_FOUND")
	ErrRootDenied       = errors.New("POLICY_DENIED")

	drivePrefix = regexp.MustCompile(`^[A-Za-z]:`)
)

// CheckRelativePath rejects everything the contract's RelativePath pattern rejects, plus the
// Windows-only escapes the pattern cannot express (alternate data streams and UNC prefixes),
// which the schema description explicitly assigns to the host.
func CheckRelativePath(rel string) error {
	if rel == "" {
		return ErrPathEmpty
	}
	if strings.ContainsRune(rel, 0) {
		return ErrPathNull
	}
	if strings.HasPrefix(rel, "/") || strings.HasPrefix(rel, "\\") {
		return ErrPathAbsolute
	}
	if drivePrefix.MatchString(rel) {
		return ErrPathDrive
	}
	// A drive-qualified path and an NTFS stream both use ':'; the second may appear later.
	if i := strings.Index(rel, ":"); i > 1 && i < len(rel)-1 {
		return ErrPathStream
	}
	segments := splitRel(rel)
	for _, seg := range segments {
		if seg == ".." {
			return ErrPathEscape
		}
	}
	return nil
}

func splitRel(rel string) []string {
	return strings.FieldsFunc(rel, func(r rune) bool { return r == '/' || r == '\\' })
}

// NormalizeRelative folds a published relative path to a single-separator form for comparison
// and joins it under a root without ever consulting the caller's idea of the current directory.
func NormalizeRelative(rel string) string {
	return strings.Join(splitRel(rel), "/")
}
