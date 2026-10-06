package host

import (
	"crypto/sha256"
	"encoding/hex"
)

// digestBytes is the non-reversible fingerprint used to prove a vault round-trip without ever
// exposing or comparing plaintext at a call site.
func digestBytes(b []byte) string {
	sum := sha256.Sum256(b)
	return "sha256:" + hex.EncodeToString(sum[:])
}
