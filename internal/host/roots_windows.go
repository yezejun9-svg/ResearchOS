//go:build windows

package host

import (
	"fmt"
	"path/filepath"
	"strings"

	"golang.org/x/sys/windows"
)

const fileAttributeReparsePoint = 0x400

// fileIdentity pins a directory by volume serial plus file index and reports the resolved
// final path, which is how a junction or symlink substitution is detected later.
func fileIdentity(path string) (volume string, fileID uint64, final string, err error) {
	wide, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return "", 0, "", err
	}
	h, err := windows.CreateFile(wide, 0, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE,
		nil, windows.OPEN_EXISTING, windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
	if err != nil {
		return "", 0, "", fmt.Errorf("open %s: %w", path, err)
	}
	defer windows.CloseHandle(h)
	var info windows.ByHandleFileInformation
	if err := windows.GetFileInformationByHandle(h, &info); err != nil {
		return "", 0, "", err
	}
	vol := fmt.Sprintf("%08x", info.VolumeSerialNumber)
	id := uint64(info.FileIndexHigh)<<32 | uint64(info.FileIndexLow)
	buf := make([]uint16, 4096)
	n, err := windows.GetFinalPathNameByHandle(h, &buf[0], uint32(len(buf)), 0)
	if err != nil {
		return vol, id, "", fmt.Errorf("final path unavailable for %s: %w", path, err)
	}
	final, err = boundedFinalPathUTF16(buf, n)
	if err != nil {
		return vol, id, "", fmt.Errorf("final path unavailable for %s: %w", path, err)
	}
	final = strings.TrimPrefix(final, `\\?\`)
	return vol, id, final, nil
}

// GetFinalPathNameByHandleW reports UTF-16 code units, not UTF-8 bytes. On
// insufficient capacity its return is the required capacity, including NUL.
func boundedFinalPathUTF16(buf []uint16, n uint32) (string, error) {
	if n == 0 {
		return "", fmt.Errorf("empty final path")
	}
	if n >= uint32(len(buf)) {
		return "", fmt.Errorf("final path needs %d UTF-16 units; capacity is %d", n, len(buf))
	}
	return windows.UTF16ToString(buf[:n]), nil
}

// chainHasReparsePoint walks every prefix of the path, so a junction anywhere above the target
// is caught even when the final component is an ordinary file.
func chainHasReparsePoint(path string) (bool, error) {
	abs, err := filepath.Abs(path)
	if err != nil {
		return false, err
	}
	parts := strings.Split(abs, string(filepath.Separator))
	var cur string
	for _, p := range parts {
		if p == "" {
			cur = abs[:1] + string(filepath.Separator)
			continue
		}
		if cur == "" {
			cur = p + string(filepath.Separator)
			continue
		}
		cur = filepath.Join(cur, p)
		reparse, err := isReparsePoint(cur)
		if err != nil {
			// Not existing yet is normal for a write target; only existing components can be
			// reparse points.
			continue
		}
		if reparse {
			return true, nil
		}
	}
	return false, nil
}

func isReparsePoint(path string) (bool, error) {
	wide, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return false, err
	}
	h, err := windows.CreateFile(wide, 0, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE,
		nil, windows.OPEN_EXISTING, windows.FILE_FLAG_BACKUP_SEMANTICS|windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return false, err
	}
	defer windows.CloseHandle(h)
	var info windows.ByHandleFileInformation
	if err := windows.GetFileInformationByHandle(h, &info); err != nil {
		return false, err
	}
	return info.FileAttributes&fileAttributeReparsePoint != 0, nil
}
