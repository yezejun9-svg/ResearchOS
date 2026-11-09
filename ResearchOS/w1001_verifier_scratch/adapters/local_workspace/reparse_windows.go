//go:build windows

package localworkspace

import "golang.org/x/sys/windows"

// reparsePoint asks the filesystem itself. An NTFS junction is not surfaced as a symlink by the
// directory iterator (its mode bits come back irregular and EvalSymlinks refuses to resolve it),
// so the only honest detector is the reparse attribute on a handle opened without following the
// link. internal/host makes the same decision the same way for the authorised roots.
func reparsePoint(path string) bool {
	p, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return false
	}
	h, err := windows.CreateFile(p, 0,
		windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE, nil,
		windows.OPEN_EXISTING, windows.FILE_FLAG_BACKUP_SEMANTICS|windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return false
	}
	defer windows.CloseHandle(h)
	var info windows.ByHandleFileInformation
	if err := windows.GetFileInformationByHandle(h, &info); err != nil {
		return false
	}
	return info.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0
}
