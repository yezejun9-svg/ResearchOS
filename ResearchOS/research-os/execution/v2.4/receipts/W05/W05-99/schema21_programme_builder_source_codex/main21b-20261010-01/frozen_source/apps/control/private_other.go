//go:build !windows

package main

import "os"

func privateFile(path string) error {
	return os.Chmod(path, 0600)
}
