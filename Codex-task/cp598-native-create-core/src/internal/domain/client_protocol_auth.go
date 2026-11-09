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
	"time"
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

// These facts represent only a credential resolved from the authoritative tables.
// They carry no native/client/same-OS assertion and are never a wire value.
type authenticatedCredential struct {
	principal string
	hash      string
	expiresAt time.Time
}

type commandCredentialKey struct{}
type commandCredentialContext struct {
	credential authenticatedCredential
	tx         *sql.Tx
	service    *ClientService
}

// AuthenticateCommandTx resolves a real bearer in the very transaction that will
// execute the command. No caller-supplied identity/context setter can mint its
// opaque facts. Legacy AuthenticateToken retains ownership of its own transaction.
func AuthenticateCommandTx(ctx context.Context, tx *sql.Tx, token string, service *ClientService) (context.Context, Principal, error) {
	if ctx == nil || tx == nil || token == "" || service == nil {
		return nil, Principal{}, ErrNoCredential
	}
	principal, credential, err := authenticateWithCredential(tx, token)
	if err != nil {
		return nil, Principal{}, err
	}
	return context.WithValue(ctx, commandCredentialKey{}, commandCredentialContext{credential: credential, tx: tx, service: service}), principal, nil
}

// A context from a different transaction (or a zero value) is not a command
// credential. Future native authorization must separately verify Host evidence;
// these ordinary bearer facts cannot be promoted into that evidence.
func commandCredentialFromContext(ctx context.Context, tx *sql.Tx, service *ClientService, principal string) (authenticatedCredential, bool) {
	if ctx == nil || tx == nil || service == nil || principal == "" {
		return authenticatedCredential{}, false
	}
	value, ok := ctx.Value(commandCredentialKey{}).(commandCredentialContext)
	if !ok || value.tx != tx || value.service != service || value.credential.principal != principal || value.credential.hash == "" || value.credential.expiresAt.IsZero() {
		return authenticatedCredential{}, false
	}
	return value.credential, true
}

func NativeCreatePreparedSchemaAvailable(ctx context.Context,tx *sql.Tx)(bool,error){ if tx==nil{return false,ErrNoCredential};return nativeOriginSchemaState(ctx,tx) }
