//go:build windows

package domain

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/sys/windows"
)

// Resolve by an opened native handle: EvalSymlinks can preserve NTFS junction
// aliases. CreateFile follows reparse points, including every parent junction.
// Only metadata access is requested; no source or protected body is read.
func upgradeExistingPath(path string) (string, error) {
	name, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return "", e
	}
	handle, e := windows.CreateFile(name, windows.FILE_READ_ATTRIBUTES, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
	if e != nil {
		return "", &os.PathError{Op: "upgrade-resolve", Path: path, Err: e}
	}
	defer windows.CloseHandle(handle)
	buffer := make([]uint16, 32768)
	n, e := windows.GetFinalPathNameByHandle(handle, &buffer[0], uint32(len(buffer)), 0)
	if e != nil || n == 0 || n >= uint32(len(buffer)) {
		return "", fmt.Errorf("UPGRADE_PATH_NATIVE_RESOLUTION: %v", e)
	}
	resolved := windows.UTF16ToString(buffer[:n])
	if strings.HasPrefix(resolved, `\\?\UNC\`) {
		resolved = `\\` + strings.TrimPrefix(resolved, `\\?\UNC\`)
	} else {
		resolved = strings.TrimPrefix(resolved, `\\?\`)
	}
	return filepath.Clean(resolved), nil
}
