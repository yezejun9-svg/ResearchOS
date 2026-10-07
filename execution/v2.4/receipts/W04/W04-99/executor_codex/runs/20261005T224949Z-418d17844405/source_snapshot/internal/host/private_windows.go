//go:build windows

package host

import (
	"errors"

	"golang.org/x/sys/windows"
)

// privateDir applies a protected current-user-only DACL to the host directory. The owner ACE
// plus "protected" means inherited permissions from a parent directory (for example a shared
// project folder) cannot grant another account access.
func privateDir(path string) error {
	id, err := currentSIDString()
	if err != nil {
		return err
	}
	sd, err := windows.SecurityDescriptorFromString("O:" + id + "D:P(A;OICI;FA;;;" + id + ")")
	if err != nil {
		return err
	}
	dacl, _, err := sd.DACL()
	if err != nil {
		return err
	}
	// Exactly the mechanism the existing local host already uses for private files: protected DACL
	// only. Claiming owner information needs WRITE_OWNER, and ownership is already this user.
	return windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT,
		windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION,
		nil, nil, dacl, nil)
}

// privateFile does the same for one file; it is applied before the durable rename so a
// credential or root record is never briefly readable by another account.
func privateFile(path string) error {
	id, err := currentSIDString()
	if err != nil {
		return err
	}
	sd, err := windows.SecurityDescriptorFromString("O:" + id + "D:P(A;;FA;;;" + id + ")")
	if err != nil {
		return err
	}
	dacl, _, err := sd.DACL()
	if err != nil {
		return err
	}
	// Exactly the mechanism the existing local host already uses for private files: protected DACL
	// only. Claiming owner information needs WRITE_OWNER, and ownership is already this user.
	return windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT,
		windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION,
		nil, nil, dacl, nil)
}

var errNoSID = errors.New("no current-process SID")

func currentSIDString() (string, error) {
	tu, err := windows.GetCurrentProcessToken().GetTokenUser()
	if err != nil {
		return "", err
	}
	if tu.User.Sid == nil || !tu.User.Sid.IsValid() {
		return "", errNoSID
	}
	return tu.User.Sid.String(), nil
}
