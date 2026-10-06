//go:build !windows

package auth

import (
	"os/user"
)

const kind = "UNIX_UID"

// currentAuthority uses the process uid. The Windows host path is the one this product ships
// on; this stub exists so the package compiles and fails closed elsewhere rather than
// pretending a POSIX uid is an OS-verified local principal.
func currentAuthority() (string, string, error) {
	u, err := user.Current()
	if err != nil {
		return "", "", err
	}
	if u.Uid == "" {
		return "", "", ErrUnavailable
	}
	return u.Uid, kind, nil
}

func processIdentity(pid uint32) (Identity, error) {
	return Identity{}, ErrUnavailable
}
