package host

import (
	"errors"
	"fmt"
	"time"
)

const stateFile = "host_state.json"

// hostState records which domain principal this host directory belongs to. It is local, not
// business truth: the database stays authoritative about principals and grants, while this
// file lets the host refuse a second OWNER or a foreign principal that appears in the same
// database later.
type hostState struct {
	Version             int    `json:"version"`
	PrincipalRef        string `json:"principal_ref"`
	PrincipalID         string `json:"principal_id"`
	HostInstanceID      string `json:"host_instance_id"`
	BootstrapAt         string `json:"bootstrap_at"`
	CreatedOwner        bool   `json:"created_owner"`
	BootstrapIterations int    `json:"bootstrap_iterations"`
	// ActiveCredentialHash is the domain.Digest of the credential this host last handed out. It
	// lets a renewal revoke exactly the row it supersedes; the token itself is never stored here.
	ActiveCredentialHash string `json:"active_credential_hash"`
}

func loadHostState(dir string) (*hostState, error) {
	var s hostState
	if err := readPrivate(dir, stateFile, &s); err != nil {
		return nil, fmt.Errorf("%w: %v", ErrBadState, err)
	}
	if s.PrincipalID == "" && s.Version != 0 {
		return nil, fmt.Errorf("%w: state file without principal", ErrBadState)
	}
	return &s, nil
}

func (h *Host) saveState(s *hostState) error {
	return writePrivate(h.dir, stateFile, s)
}

// boundPrincipal returns the principal this host directory was initialised for, or "" when
// the host has never been bootstrapped.
func (h *Host) boundPrincipal() string {
	if h.state == nil {
		return ""
	}
	return h.state.PrincipalID
}

var errNoState = errors.New("host state missing")

// nowUTC is the single clock the host uses so qualification can pin time without touching
// the identity or storage layers.
func (h *Host) nowUTC() time.Time { return h.now().UTC() }
