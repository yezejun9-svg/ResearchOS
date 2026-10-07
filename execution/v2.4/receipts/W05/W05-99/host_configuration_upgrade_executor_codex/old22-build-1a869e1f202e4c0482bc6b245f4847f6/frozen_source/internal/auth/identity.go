// Package auth resolves the local OS identity that the trusted host uses to bootstrap and
// renew a session (W17-01, 22_CLIENT_INTERFACE §OS bootstrap). It is deliberately not a
// second account system: it only answers "which OS principal is standing in front of this
// host right now" so the existing domain principals can be bound to that identity. No
// secret, token or password is ever produced or read here.
package auth

import (
	"errors"
	"fmt"
	"os/user"
	"strings"
)

// Identity is an OS-principal reference, never a credential. Ref is a stable
// non-reversible handle so logs and receipts can name the user without leaking identity
// material beyond what the local machine already knows.
type Identity struct {
	Kind string `json:"kind"` // WINDOWS_SID | UNIX_UID
	VID  string `json:"-"`    // raw authority: SID string or uid
	Ref  string `json:"principal_ref"`
	Name string `json:"account_name"`
}

var (
	ErrUnavailable = errors.New("OS_IDENTITY_UNAVAILABLE")
	ErrMismatch    = errors.New("OS_IDENTITY_MISMATCH")
)

// Current returns the identity of the process that is asking. On Windows this is the access
// token user SID; elsewhere the uid. It fails closed: an unreadable token is an error, not
// an anonymous identity.
func Current() (Identity, error) {
	raw, kind, err := currentAuthority()
	if err != nil {
		return Identity{}, fmt.Errorf("%w: %v", ErrUnavailable, err)
	}
	name := ""
	if u, e := user.Current(); e == nil && u != nil {
		name = u.Username
	}
	return Identity{Kind: kind, VID: raw, Ref: referenceFor(kind, raw), Name: name}, nil
}

// referenceFor derives a stable, non-reversible local reference from the authority string.
func referenceFor(kind, raw string) string {
	return strings.ToLower(kind) + ":" + shortHash(kind+"|"+raw)
}

// SameUser compares authorities by SID/uid string equality. Two identities from different
// OS users never match, even if both are administrators.
func (i Identity) SameUser(other Identity) bool {
	if i.VID == "" || other.VID == "" {
		return false
	}
	return i.Kind == other.Kind && strings.EqualFold(i.VID, other.VID)
}

// ProcessIdentity resolves the OS principal behind a foreign process id. Exported so
// qualification can assert that a peer from another account is refused.
func ProcessIdentity(pid uint32) (Identity, error) { return processIdentity(pid) }

// VerifyProcess checks that a foreign process (for example the peer of a named pipe) belongs
// to the same OS user as this one. pid==0 is rejected: there is no anonymous local caller.
func VerifyProcess(pid uint32, against Identity) (Identity, error) {
	if pid == 0 {
		return Identity{}, ErrMismatch
	}
	peer, err := processIdentity(pid)
	if err != nil {
		return Identity{}, err
	}
	if !against.SameUser(peer) {
		return peer, ErrMismatch
	}
	return peer, nil
}
