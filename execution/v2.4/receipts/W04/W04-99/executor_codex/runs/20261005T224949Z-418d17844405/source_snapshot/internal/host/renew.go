package host

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"
)

// ErrNotBound is returned when a client asks for a session before this host directory has
// been bootstrapped. The answer is never "create a second owner".
var ErrNotBound = errors.New("HOST_NOT_BOOTSTRAPPED")

// RenewSession re-verifies the OS principal and issues a fresh short credential. Expiry of the
// previous credential must never clear projects, sessions or messages, so renewal performs no
// business write at all: the only rows it touches are the new auth_credentials insert made
// through the existing domain.IssueCredential path, plus the single REVOKED flag on the row this
// host superseded. A superseded token stops working at renewal instead of surviving until its
// TTL, so "the file the local client reads" always names the only credential that works.
func (h *Host) RenewSession(ctx context.Context) (Session, error) {
	if _, err := h.reverify(); err != nil {
		return Session{}, err
	}
	principal := h.boundPrincipal()
	if principal == "" {
		return Session{}, ErrNotBound
	}
	var revoked int
	err := h.db.QueryRowContext(ctx, `SELECT revoked FROM auth_principals WHERE id=?`, principal).Scan(&revoked)
	if errors.Is(err, sql.ErrNoRows) {
		return Session{}, fmt.Errorf("%w: bound principal no longer exists", ErrNoOwner)
	}
	if err != nil {
		return Session{}, err
	}
	if revoked != 0 {
		return Session{}, ErrPrincipalRevoked
	}
	before, err := h.stateSnapshot(ctx)
	if err != nil {
		return Session{}, err
	}
	sess, err := h.issue(ctx, principal)
	if err != nil {
		return Session{}, err
	}
	h.state.BootstrapIterations++
	if err := h.saveState(h.state); err != nil {
		return Session{}, err
	}
	after, err := h.stateSnapshot(ctx)
	if err != nil {
		return Session{}, err
	}
	// The host guarantees renewal is state-preserving rather than trusting it: any change to
	// business rows would mean an expired credential was treated as a reason to reset data.
	if before != after {
		return Session{}, fmt.Errorf("%w: renewal changed business state", ErrBadState)
	}
	return sess, nil
}

// businessCensus counts the rows renewal must not disturb. schema_migrations and auth tables are
// excluded because they are not user-visible business state and are legitimately extended by
// other host paths.
type census struct {
	Objects  int64
	Sessions int64
	Outbox   int64
}

func (c census) String() string {
	return fmt.Sprintf("objects=%d;sessions=%d;outbox=%d", c.Objects, c.Sessions, c.Outbox)
}

func (h *Host) stateSnapshot(ctx context.Context) (census, error) {
	var c census
	if err := h.db.QueryRowContext(ctx, `SELECT count(*) FROM domain_objects`).Scan(&c.Objects); err != nil {
		return c, err
	}
	if err := h.db.QueryRowContext(ctx, `SELECT count(*) FROM client_sessions`).Scan(&c.Sessions); err != nil {
		return c, err
	}
	if err := h.db.QueryRowContext(ctx, `SELECT count(*) FROM outbox`).Scan(&c.Outbox); err != nil {
		return c, err
	}
	return c, nil
}

// ActiveCredentials reports how many unexpired credentials the bound principal holds. It exists
// so qualification (and the host's own diagnostics) can see session accumulation without any
// caller needing to read the credential table or a secret.
func (h *Host) ActiveCredentials(ctx context.Context, now time.Time) (int, error) {
	var n int
	err := h.db.QueryRowContext(ctx, `SELECT count(*) FROM auth_credentials c
		JOIN auth_principals p ON p.id=c.principal
		WHERE c.revoked=0 AND p.revoked=0 AND c.expires_at>?`, now.UTC().Format(time.RFC3339Nano)).Scan(&n)
	return n, err
}
