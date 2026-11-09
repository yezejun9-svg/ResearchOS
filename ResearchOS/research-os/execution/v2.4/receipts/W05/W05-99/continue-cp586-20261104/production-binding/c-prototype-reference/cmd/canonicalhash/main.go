// canonicalhash is a C-fixture helper, not a source compiler or product writer.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"

	"researchos.local/binding-schema-prototype/canonical"
)

const maxInputBytes = 65536

// hashValue follows domain.Hash: json.Marshal(value), canonical.JSON, Digest.
// The raw input is first checked with the copied strict canonicalizer so that
// JSON map decoding cannot silently collapse duplicate names or bad Unicode.
func hashValue(raw []byte) ([]byte, string, error) {
	if len(raw) == 0 || len(raw) > maxInputBytes {
		return nil, "", fmt.Errorf("input limit")
	}
	if _, err := canonical.JSON(raw); err != nil {
		return nil, "", err
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	var value any
	if err := decoder.Decode(&value); err != nil {
		return nil, "", err
	}
	if err := decoder.Decode(new(any)); err != io.EOF {
		return nil, "", fmt.Errorf("one JSON value required")
	}
	marshaled, err := json.Marshal(value)
	if err != nil {
		return nil, "", err
	}
	canon, err := canonical.JSON(marshaled)
	if err != nil {
		return nil, "", err
	}
	digest := sha256.Sum256(canon)
	return canon, "sha256:" + hex.EncodeToString(digest[:]), nil
}

func main() {
	raw, err := io.ReadAll(io.LimitReader(os.Stdin, maxInputBytes+1))
	if err != nil {
		os.Exit(2)
	}
	canon, digest, err := hashValue(raw)
	if err != nil {
		_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"valid": false, "error": "strict canonical input rejected"})
		os.Exit(2)
	}
	_ = json.NewEncoder(os.Stdout).Encode(map[string]any{"valid": true, "canonical_base64": base64.StdEncoding.EncodeToString(canon), "hash": digest})
}
