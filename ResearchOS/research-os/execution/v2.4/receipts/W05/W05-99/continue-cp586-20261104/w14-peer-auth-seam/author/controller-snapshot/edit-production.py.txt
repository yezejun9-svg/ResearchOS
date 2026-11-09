from pathlib import Path
import hashlib
import json

ROOT = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-peer-auth-seam-20261104')
SCOPE = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/w14-peer-auth-seam/scope.json')
scope = json.loads(SCOPE.read_text(encoding='utf-8-sig'))
assert scope['base_head'] == 'ebc340ef35cfdbf4449642ed559a05e5cdbaaee6'
texts = {}
for name in scope['production_paths']:
    path = ROOT/name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == scope['base_source_sha256'][name], name
    texts[name] = path.read_text(encoding='utf-8')

def replace(name, old, new):
    assert texts[name].count(old) == 1, (name, old[:100])
    texts[name] = texts[name].replace(old, new, 1)

p = 'internal/host/host.go'
replace(p, 'import (\n\t"crypto/sha256"', 'import (\n\t"crypto/rand"\n\t"crypto/sha256"')
replace(p, '\t"fmt"\n\t"os"', '\t"fmt"\n\t"io"\n\t"os"')
replace(p, '\tidentity auth.Identity\n', '\tidentity auth.Identity\n\t// Fresh for this Host object only; never a stable identity or a wire credential.\n\tbootGeneration [32]byte\n')
replace(p, 'func New(cfg Config) (*Host, error) {\n', '''func New(cfg Config) (*Host, error) {
	return newHost(cfg, rand.Reader)
}

// The entropy seam is private: production always uses crypto/rand, while tests
// can prove that failure precedes any directory, vault or database mutation.
func newHost(cfg Config, entropy io.Reader) (*Host, error) {
''')
replace(p, '\tif cfg.ReadOnlyModelVaultDir != "" {\n\t\tif cfg.ReadOnlyModelCredentialRef == ""', '''	var generation [32]byte
	if entropy == nil {
		return nil, fmt.Errorf("%w: boot generation entropy unavailable", ErrBadState)
	}
	if _, err := io.ReadFull(entropy, generation[:]); err != nil {
		return nil, fmt.Errorf("%w: boot generation entropy: %w", ErrBadState, err)
	}
	if generation == ([32]byte{}) {
		return nil, fmt.Errorf("%w: empty boot generation", ErrBadState)
	}
	if cfg.ReadOnlyModelVaultDir != "" {
		if cfg.ReadOnlyModelCredentialRef == ""''')
replace(p, 'identity: id, now: now, doc: doc}', 'identity: id, bootGeneration: generation, now: now, doc: doc}')

p = 'internal/host/native.go'
replace(p, '\t"researchos.local/research-os/internal/domain"', '\t"researchos.local/research-os/internal/auth"\n\t"researchos.local/research-os/internal/domain"')
old = '''// HandleNative processes one frame from a peer whose OS identity the transport already verified.
// clientVerified must be the reference of the same local principal the host started with.
func (h *Host) HandleNative(raw []byte, clientVerified bool, selectionHook func(path string) (string, error)) ([]byte, error) {
	if len(raw) == 0 || len(raw) > MaxNativeFrameBytes {
		return nil, ErrFrameTooLarge
	}
	if !clientVerified {
		return nil, ErrFrameUntrusted
	}
	var frame NativeFrame
'''
new = '''// verifiedNativePeer is an in-process capability produced from the OS transport,
// not from NativeFrame.ClientID or the legacy success boolean. It proves only the
// observed peer user, not a client instance, credential binding or writer grant.
type verifiedNativePeer struct {
	host       *Host
	generation [32]byte
	identity   auth.Identity
	pid        uint32
}

func (p verifiedNativePeer) validFor(h *Host) bool {
	return h != nil && p.host == h && p.pid != 0 &&
		h.bootGeneration != ([32]byte{}) && p.generation == h.bootGeneration &&
		verifiableKind(p.identity.Kind) && p.identity.Ref != "" &&
		h.identity.SameUser(p.identity)
}

// Only the OS transport calls this in production. A failed lookup or comparison
// never produces a capability, including when a caller supplies a matching label.
func (h *Host) verifyNativePeer(pid uint32) (verifiedNativePeer, error) {
	if h == nil || pid == 0 || h.peerLookup == nil || h.bootGeneration == ([32]byte{}) {
		return verifiedNativePeer{}, ErrFrameUntrusted
	}
	identity, err := h.peerLookup(pid)
	if err != nil {
		return verifiedNativePeer{}, fmt.Errorf("%w: peer identity unresolved: %v", ErrFrameUntrusted, err)
	}
	peer := verifiedNativePeer{host: h, generation: h.bootGeneration, identity: identity, pid: pid}
	if !peer.validFor(h) {
		return verifiedNativePeer{}, ErrHostIdentity
	}
	return peer, nil
}

// The peer remains attached at the handler dispatch boundary. A nil peer is an
// explicitly unproven legacy invocation, never a substitute for native evidence.
type nativeInvocation struct {
	frame NativeFrame
	peer  *verifiedNativePeer
}

// HandleNative preserves the legacy adapter for the existing operations. Its
// boolean does not mint or populate verifiedNativePeer.
func (h *Host) HandleNative(raw []byte, clientVerified bool, selectionHook func(path string) (string, error)) ([]byte, error) {
	if len(raw) == 0 || len(raw) > MaxNativeFrameBytes {
		return nil, ErrFrameTooLarge
	}
	if !clientVerified {
		return nil, ErrFrameUntrusted
	}
	invocation, err := h.prepareNativeInvocation(raw, nil)
	if err != nil {
		return nil, err
	}
	return h.dispatchNative(invocation, selectionHook)
}

func (h *Host) handleVerifiedNative(raw []byte, peer verifiedNativePeer, selectionHook func(string) (string, error)) ([]byte, error) {
	if !peer.validFor(h) {
		return nil, ErrFrameUntrusted
	}
	invocation, err := h.prepareNativeInvocation(raw, &peer)
	if err != nil {
		return nil, err
	}
	return h.dispatchNative(invocation, selectionHook)
}

func (h *Host) prepareNativeInvocation(raw []byte, peer *verifiedNativePeer) (nativeInvocation, error) {
	if len(raw) == 0 || len(raw) > MaxNativeFrameBytes {
		return nativeInvocation{}, ErrFrameTooLarge
	}
	if peer != nil && !peer.validFor(h) {
		return nativeInvocation{}, ErrFrameUntrusted
	}
	var frame NativeFrame
'''
replace(p, old, new)
# The original decoder/contract checks now return the prepared invocation.
start = texts[p].index('func (h *Host) prepareNativeInvocation(')
end = texts[p].index('\tvar reply []byte', start)
part = texts[p][start:end]
part = part.replace('return nil, ', 'return nativeInvocation{}, ')
texts[p] = texts[p][:start] + part + '''	return nativeInvocation{frame: frame, peer: peer}, nil
}

func (h *Host) dispatchNative(invocation nativeInvocation, selectionHook func(string) (string, error)) ([]byte, error) {
	if invocation.peer != nil && !invocation.peer.validFor(h) {
		return nil, ErrFrameUntrusted
	}
	frame := invocation.frame
''' + texts[p][end:]

p = 'internal/host/native_pipe_windows.go'
replace(p, '\tpeer, err := h.peerLookup(pid)\n', '\tpeer, err := h.verifyNativePeer(pid)\n')
replace(p, 'errorFrame(fmt.Errorf("%w: peer identity unresolved: %v", ErrFrameUntrusted, err))', 'errorFrame(err)')
replace(p, '''	if !h.Identity().SameUser(peer) {
		_ = writeNativeFrame(ph, errorFrame(ErrHostIdentity))
		return
	}
''', '')
replace(p, 'reply, err := h.HandleNative(raw, true, chooser)', 'reply, err := h.handleVerifiedNative(raw, peer, chooser)')

p = 'internal/domain/auth.go'
replace(p, '''func authenticate(tx *sql.Tx, token string) (Principal, error) {
	var p Principal
''', '''func authenticate(tx *sql.Tx, token string) (Principal, error) {
	p, _, err := authenticateWithCredential(tx, token)
	return p, err
}

func authenticateWithCredential(tx *sql.Tx, token string) (Principal, authenticatedCredential, error) {
	var p Principal
	hash := Digest([]byte(token))
''')
replace(p, 'Digest([]byte(token))).Scan(&p.ID, &roles, &p.CanCreateProject, &expires)', 'hash).Scan(&p.ID, &roles, &p.CanCreateProject, &expires)')
start = texts[p].index('func authenticateWithCredential(')
end = texts[p].index('func (p Principal) HasRole', start)
part = texts[p][start:end]
part = part.replace('return p, ', 'return p, authenticatedCredential{}, ')
part = part.replace('''	e = constrainRemotePrincipal(tx, &p)
	return p, authenticatedCredential{}, e
''', '''	if e = constrainRemotePrincipal(tx, &p); e != nil {
		return p, authenticatedCredential{}, e
	}
	return p, authenticatedCredential{principal: p.ID, hash: hash, expiresAt: t}, nil
''')
texts[p] = texts[p][:start] + part + texts[p][end:]

p = 'internal/domain/client_protocol_auth.go'
replace(p, '\t"errors"\n', '\t"errors"\n\t"time"\n')
texts[p] += '''
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
'''

p = 'internal/api/v2.go'
replace(p, '''	principal, authErr := domain.AuthenticateToken(r.Context(), v.db, bearerToken(r))
	if authErr != nil {
''', '''	// Authentication and command execution share one transaction, so credential
	// revocation, principal/grant checks and command effects see the same state.
	// Begin failure remains an auth-stage rejection, as in AuthenticateToken.
	tx, authErr := v.db.BeginTx(r.Context(), nil)
	var authContext context.Context
	var principal domain.Principal
	if authErr == nil {
		defer tx.Rollback()
		authContext, principal, authErr = domain.AuthenticateCommandTx(r.Context(), tx, bearerToken(r), v.svc)
	}
	if authErr != nil {
''')
replace(p, '''	tx, err := v.db.BeginTx(r.Context(), nil)
	if err != nil {
		writeTypedError(w, http.StatusInternalServerError, env, "INTERNAL_ERROR", "host transaction unavailable")
		return
	}
	defer tx.Rollback()
''', '')
replace(p, 'v.svc.Execute(r.Context(), tx, env, principal.ID)', 'v.svc.Execute(authContext, tx, env, principal.ID)')

for name, text in texts.items():
    (ROOT/name).write_text(text, encoding='utf-8', newline='\n')
print(json.dumps({'status': 'EDITED_ONLY_AUTHORIZED_SIX_PRODUCTION_FILES', 'files': list(texts)}, ensure_ascii=False))
