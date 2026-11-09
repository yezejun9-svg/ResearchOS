//go:build windows

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
	var info syscall.ByHandleFileInformation
	if err = syscall.GetFileInformationByHandle(syscall.Handle(dir.Fd()), &info); err != nil {
		return "", err
	}
	return fmt.Sprintf("%08x:%08x:%08x", info.VolumeSerialNumber, info.FileIndexHigh, info.FileIndexLow), nil
}
