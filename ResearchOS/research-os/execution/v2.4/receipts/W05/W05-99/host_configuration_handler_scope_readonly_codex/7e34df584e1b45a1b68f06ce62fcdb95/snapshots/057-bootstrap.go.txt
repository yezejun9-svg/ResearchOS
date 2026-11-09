package host

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"researchos.local/research-os/internal/auth"
	"researchos.local/research-os/internal/domain"
)

// Session is a short-lived host credential. It is handed to the trusted local client in
// process (or over the OS-protected native bridge) and is never written into a log, an event,
// a CommandEnvelope, or a renderer-visible structure.
type Session struct {
	PrincipalID  string    `json:"-"`
	PrincipalRef string    `json:"principal_ref"`
	Token        string    `json:"-"`
	IssuedAt     time.Time `json:"issued_at"`
	ExpiresAt    time.Time `json:"expires_at"`
	TTLSec       int64     `json:"expires_in_seconds"`
}

// BootstrapResult distinguishes the two legitimate outcomes, because the contract requires
// different behaviour for each: a first local user establishes exactly one OWNER, while every
// later start binds the existing OWNER without touching permissions or data.
type BootstrapResult struct {
	PrincipalID   string
	PrincipalRef  string
	CreatedOwner  bool
	BoundExisting bool
	Iterations    int
	Session       Session
}

// BootstrapOwner implements 22 §OS bootstrap: verify the OS principal, then bind an existing
// OWNER or, only when the database has no principal at all, initialise one exactly once.
// There is no route by which an untrusted caller (renderer, ordinary HTTP request, phone
// pairing) reaches this function, and it never resets permissions or data.
func (h *Host) BootstrapOwner(ctx context.Context) (*BootstrapResult, error) {
	fresh, err := h.reverify()
	if err != nil {
		return nil, err
	}
	owners, total, ownerID := h.scanPrincipals(ctx)
	switch {
	case owners > 1:
		// A database with more than one OWNER is a corrupted or tampered state; refusing is
		// safer than picking one, because either choice could hand another user's project set
		// to the current caller.
		return nil, ErrMultipleOwners
	case owners == 1:
		if bound := h.boundPrincipal(); bound != "" && bound != ownerID {
			return nil, fmt.Errorf("%w: this host directory belongs to a different local principal", ErrHostIdentity)
		}
		sess, err := h.issue(ctx, ownerID)
		if err != nil {
			return nil, err
		}
		h.state.PrincipalID = ownerID
		h.state.PrincipalRef = fresh.Ref
		if h.state.HostInstanceID == "" {
			h.state.HostInstanceID = h.InstanceID()
			h.state.BootstrapAt = h.nowUTC().Format(time.RFC3339Nano)
		}
		h.state.BootstrapIterations++
		h.state.CreatedOwner = h.state.CreatedOwner || false
		if err := h.saveState(h.state); err != nil {
			return nil, err
		}
		return &BootstrapResult{PrincipalID: ownerID, PrincipalRef: fresh.Ref, BoundExisting: true,
			CreatedOwner: false, Iterations: h.state.BootstrapIterations, Session: sess}, nil
	case owners == 0 && total > 0:
		// Principals exist but none is an OWNER: the local admin path created them, and this
		// bootstrap must not silently promote one of them.
		return nil, ErrNoOwner
	case owners == 0 && total == 0:
		id := "owner-" + domain.ID()
		if err := h.domain.ProvisionPrincipal(ctx, domain.Principal{
			ID: id, Roles: []string{"OWNER"}, CanCreateProject: true,
		}); err != nil {
			return nil, fmt.Errorf("owner initialisation failed: %w", err)
		}
		sess, err := h.issue(ctx, id)
		if err != nil {
			return nil, fmt.Errorf("owner session failed: %w", err)
		}
		h.state = &hostState{Version: 1, PrincipalID: id, PrincipalRef: fresh.Ref,
			HostInstanceID: h.InstanceID(), BootstrapAt: h.nowUTC().Format(time.RFC3339Nano),
			CreatedOwner: true, BootstrapIterations: 1}
		h.state.ActiveCredentialHash = domain.Digest([]byte(sess.Token))
		if err := h.saveState(h.state); err != nil {
			return nil, err
		}
		return &BootstrapResult{PrincipalID: id, PrincipalRef: fresh.Ref, CreatedOwner: true,
			Iterations: 1, Session: sess}, nil
	}
	return nil, errors.New("unreachable bootstrap state")
}

// issue creates the short credential and hands it to the local user through the host's private
// 0600 file. The bridge reply deliberately does not carry it, so the renderer never sees a token
// and the user never copies one out of a log or console. A renewal supersedes the credential it
// replaces: the old one is revoked immediately rather than left live for the rest of its TTL,
// because "the token in the file" must be the only token that works.
func (h *Host) issue(ctx context.Context, principalID string) (Session, error) {
	previous := ""
	if h.state != nil {
		previous = h.state.ActiveCredentialHash
	}
	token, err := h.domain.IssueCredential(ctx, principalID, h.ttl)
	if err != nil {
		return Session{}, err
	}
	hash := domain.Digest([]byte(token))
	if previous != "" && previous != hash {
		if err := h.revokeCredentialByHash(ctx, principalID, previous); err != nil {
			return Session{}, err
		}
	}
	now := h.nowUTC()
	sess := Session{PrincipalID: principalID, PrincipalRef: h.identity.Ref, Token: token,
		IssuedAt: now, ExpiresAt: now.Add(h.ttl), TTLSec: int64(h.ttl / time.Second)}
	if err := h.writeSessionFile(sess); err != nil {
		return Session{}, err
	}
	if h.state != nil {
		h.state.ActiveCredentialHash = hash
	}
	return sess, nil
}

// revokeCredentialByHash marks exactly one credential row revoked, identified by the hash the
// host itself issued. The host never searches or decrypts a token and never touches another
// principal's rows: an already-absent row is not an error.
func (h *Host) revokeCredentialByHash(ctx context.Context, principalID, tokenHash string) error {
	if principalID == "" || tokenHash == "" {
		return nil
	}
	_, err := h.db.ExecContext(ctx, `UPDATE auth_credentials SET revoked=1 WHERE principal=? AND token_hash=?`,
		principalID, tokenHash)
	return err
}

// scanPrincipals counts OWNER principals and all principals. Roles are stored as a JSON array
// by the domain layer; an unparsable row counts as "not an OWNER" rather than being trusted.
func (h *Host) scanPrincipals(ctx context.Context) (owners, total int, ownerID string) {
	rows, err := h.db.QueryContext(ctx, `SELECT id, roles, revoked FROM auth_principals ORDER BY id`)
	if err != nil {
		return -1, -1, ""
	}
	defer rows.Close()
	for rows.Next() {
		var id, roles string
		var revoked int
		if err := rows.Scan(&id, &roles, &revoked); err != nil {
			return -1, -1, ""
		}
		total++
		if revoked != 0 {
			continue
		}
		var list []string
		if err := json.Unmarshal([]byte(roles), &list); err != nil {
			continue
		}
		for _, r := range list {
			if r == "OWNER" {
				owners++
				ownerID = id
			}
		}
	}
	if err := rows.Err(); err != nil {
		return -1, -1, ""
	}
	return owners, total, ownerID
}

// reverify is the identity check every privileged host operation performs first: the OS
// principal asking now must be the same principal this host was started for.
func (h *Host) reverify() (identitySnapshot, error) {
	fresh, err := auth.Current()
	if err != nil {
		return identitySnapshot{}, err
	}
	if !h.identity.SameUser(fresh) {
		return identitySnapshot{}, ErrHostIdentity
	}
	return identitySnapshot{Ref: fresh.Ref}, nil
}

type identitySnapshot struct{ Ref string }
