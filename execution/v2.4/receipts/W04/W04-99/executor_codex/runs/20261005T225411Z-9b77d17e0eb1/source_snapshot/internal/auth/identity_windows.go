//go:build windows

package auth

import (
	"fmt"

	"golang.org/x/sys/windows"
)

const kind = "WINDOWS_SID"

// currentAuthority reads the access token of this process. A process without a readable
// user token has no local identity, so the host must refuse to bootstrap rather than fall
// back to "the person who ran the installer".
func currentAuthority() (string, string, error) {
	tu, err := windows.GetCurrentProcessToken().GetTokenUser()
	if err != nil {
		return "", "", err
	}
	sid := tu.User.Sid
	if sid == nil || !sid.IsValid() {
		return "", "", fmt.Errorf("invalid process token SID")
	}
	return sid.String(), kind, nil
}

// processIdentity resolves the SID of another local process, which is how a named-pipe peer
// is authenticated: the pipe ACL alone only proves "same user can connect", so the host
// additionally asks the OS who owns the client process.
func processIdentity(pid uint32) (Identity, error) {
	h, err := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION, false, pid)
	if err != nil {
		return Identity{}, fmt.Errorf("%w: open pid %d: %v", ErrMismatch, pid, err)
	}
	defer windows.CloseHandle(h)
	var tok windows.Token
	if err := windows.OpenProcessToken(windows.Handle(h), windows.TOKEN_QUERY, &tok); err != nil {
		return Identity{}, fmt.Errorf("%w: token pid %d: %v", ErrMismatch, pid, err)
	}
	defer tok.Close()
	tu, err := tok.GetTokenUser()
	if err != nil {
		return Identity{}, err
	}
	if tu.User.Sid == nil || !tu.User.Sid.IsValid() {
		return Identity{}, fmt.Errorf("invalid client token SID")
	}
	raw := tu.User.Sid.String()
	return Identity{Kind: kind, VID: raw, Ref: referenceFor(kind, raw)}, nil
}
