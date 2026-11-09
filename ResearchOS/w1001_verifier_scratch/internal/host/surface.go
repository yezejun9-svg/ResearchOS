package host

// Exported host surface used by the local CLI/Desktop and by qualification. Each method keeps the
// boundary it belongs to: paths are resolved by the host, credentials only ever come back as a
// reference plus a state, and a selection reference is consumable once.

// ResolveWorkspace validates one published relative path against a bound root and returns the
// absolute path to open. Registration-time correctness is never assumed: the reparse chain and
// the pinned volume/file identity are re-checked on every call.
func (h *Host) ResolveWorkspace(ref, rel, wantAccess string) (string, error) {
	return h.roots.Resolve(ref, rel, wantAccess)
}

// RevokeWorkspace withdraws a root. Subsequent calls answer WORKSPACE_REVOKED rather than an empty
// listing, so an inaccessible directory can never be presented as "no files".
func (h *Host) RevokeWorkspace(ref string) error { return h.roots.Revoke(ref) }

// WorkspaceStatus reports the binding state of one root reference.
func (h *Host) WorkspaceStatus(ref string) string { return h.roots.Status(ref) }

// CredentialUsable answers whether a reference can still yield material to the host's own
// provider path. It reports a boolean only: no call in this package returns plaintext to a
// caller outside the host.
func (h *Host) CredentialUsable(ref string) bool {
	buf, err := h.vault.open(ref)
	if err != nil {
		return false
	}
	for i := range buf {
		buf[i] = 0
	}
	return true
}

// SelectionFor exposes an issued selection record's fields to the host's own configuration path
// (the reference itself is consumed by ConsumeSelection).
func (h *Host) OutstandingSelections() int { return h.selections.Outstanding() }

// VaultRefs lists credential references (never values) for host diagnostics and the CLI settings
// screen.
func (h *Host) VaultRefs() ([]string, error) { return h.vault.Refs() }
