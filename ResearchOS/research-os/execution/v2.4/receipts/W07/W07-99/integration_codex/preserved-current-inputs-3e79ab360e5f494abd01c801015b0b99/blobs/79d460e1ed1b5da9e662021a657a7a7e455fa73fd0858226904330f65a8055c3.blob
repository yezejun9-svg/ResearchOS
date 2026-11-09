package domain

// Token resolution for the typed v2 boundary (W03-02).
//
// The route must never accept a client-claimed identity, so this wrapper reuses the exact
// credential path the v1 host already uses (auth_credentials / auth_principals / auth_grants
// with the remote-principal constraints of W17). It adds no second identity system: the
// exported function is a read-only entry point onto the existing authenticate() logic so the
// api package can bind a CommandEnvelope to a real principal.

import (
	"context"
	"database/sql"
	"errors"
)

// ErrNoCredential is returned when the caller supplied no bearer credential at all; the
// typed service answers UNAUTHENTICATED rather than treating the request as an anonymous
// local user.
var ErrNoCredential = errors.New("UNAUTHENTICATED")

// AuthenticateToken resolves a bearer token to the authenticated principal, including its
// project grants. An expired or revoked credential never resolves.
func AuthenticateToken(ctx context.Context, db *sql.DB, token string) (Principal, error) {
	if token == "" {
		return Principal{}, ErrNoCredential
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return Principal{}, err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return p, err
	}
	return p, tx.Commit()
}
