package main

import (
	"encoding/json"
	"testing"
)

// These pure controls are compiled with the product graph. The registered Node
// leaves exercise the same cases through the actual child executable.
func TestWireParserPreservesAdjacentIntegers(t *testing.T) {
	for _, literal := range []string{"9007199254740992", "9007199254740993", "1.0000000000000001"} {
		value, err := decode([]byte(literal), &budget{})
		if err != nil || value.(json.Number).String() != literal {
			t.Fatalf("numeric lexeme lost: %v", err)
		}
	}
}
func TestWireParserRejectsAmbiguousJSONAndWorkExhaustion(t *testing.T) {
	for _, raw := range []string{`{"a":1,"\u0061":2}`, `"\ud800"`, `{} {}`} {
		if _, err := decode([]byte(raw), &budget{}); err == nil {
			t.Fatal("accepted ambiguous JSON")
		}
	}
	if _, err := decode([]byte(`1e4097`), &budget{}); err != resourceLimit {
		t.Fatalf("expected local resource limit, got %v", err)
	}
}
