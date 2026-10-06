package auth

import (
	"crypto/sha256"
	"encoding/hex"
)

// shortHash keeps a local reference readable in receipts while making sure the raw SID or
// uid string (which is guessable and appears elsewhere on the machine) is not what callers
// pass around as an identity handle.
func shortHash(s string) string {
	sum := sha256.Sum256([]byte(s))
	return hex.EncodeToString(sum[:8])
}
