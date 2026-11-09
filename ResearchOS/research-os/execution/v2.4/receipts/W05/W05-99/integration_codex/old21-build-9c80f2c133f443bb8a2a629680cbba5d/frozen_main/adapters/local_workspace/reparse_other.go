//go:build !windows

package localworkspace

// On POSIX systems the directory iterator reports a symlink with ModeSymlink, and the walk already
// refuses those, so no extra handle-level check exists or is needed.
func reparsePoint(string) bool { return false }
