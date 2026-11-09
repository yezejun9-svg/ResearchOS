//go:build !windows

package domain

import "path/filepath"

func upgradeExistingPath(path string) (string, error) {
	return filepath.EvalSymlinks(path)
}
