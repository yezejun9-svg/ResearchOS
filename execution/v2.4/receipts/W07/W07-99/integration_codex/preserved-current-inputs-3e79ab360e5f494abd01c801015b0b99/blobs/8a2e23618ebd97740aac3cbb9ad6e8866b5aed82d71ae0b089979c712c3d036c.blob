//go:build !windows

package retrieval

import (
	"fmt"
	"os"
	"syscall"
)

func rootIdentity(root *os.Root) (string, error) {
	dir, err := root.Open(".")
	if err != nil {
		return "", err
	}
	defer dir.Close()
	info, err := dir.Stat()
	if err != nil {
		return "", err
	}
	stat, ok := info.Sys().(*syscall.Stat_t)
	if !ok {
		return "", fmt.Errorf("root file identity unavailable")
	}
	return fmt.Sprintf("%x:%x", stat.Dev, stat.Ino), nil
}
