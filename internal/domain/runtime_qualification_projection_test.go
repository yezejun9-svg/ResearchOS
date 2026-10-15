package domain

import (
	"encoding/json"
	"testing"

	"researchos.local/research-os/internal/runtimepolicy"
)

func TestQualificationProjectionDomainCanonicalHash(t *testing.T) {
	value := Object{"😀": []any{Object{"中": json.Number("1e0"), "n": json.Number("2.500")}}, "tools": Empty()}
	policy, err := runtimepolicy.Hash(value)
	if err != nil {
		t.Fatal(err)
	}
	if policy != Hash(value) || policy != "sha256:bcce6b88b4df307036224038610c85590a86b6dc8254202f49f1dfe532131257" {
		t.Fatalf("domain/policy hash mismatch: %s %s", Hash(value), policy)
	}
}
