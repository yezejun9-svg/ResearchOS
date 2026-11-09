//go:build !windows

package host

import "errors"

// Without the OS-user-scoped secret store there is no protected place to put a provider
// credential, so the host refuses rather than falling back to a file the other accounts on the
// machine may read.
func protect([]byte) ([]byte, error)   { return nil, ErrCredentialProtected }
func unprotect([]byte) ([]byte, error) { return nil, ErrCredentialProtected }

var errUnsupportedPlatform = errors.New("host protected store requires Windows")

func otherOS() bool { return true }
