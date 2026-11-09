package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"testing"
)

func TestIndependentCanonicalVectors(t *testing.T) {
	for _, tc := range []struct{ name, input, expected string }{
		{"ordered-fields", `{"z":"last","a":"first"}`, `{"a":"first","z":"last"}`},
		{"html-unicode", `{"z":"<script>&","a":"中文\u2028é"}`, "{\"a\":\"中文\u2028é\",\"z\":\"<script>&\"}"},
		{"utf16-key-order", `{"\ue000":"private","😀":"emoji","a":"first"}`, "{\"a\":\"first\",\"😀\":\"emoji\",\"\ue000\":\"private\"}"},
		{"large-int64-decimal-string", `{"revision":"9223372036854775807","epoch":"9007199254740993","schema_version":1}`, `{"epoch":"9007199254740993","revision":"9223372036854775807","schema_version":1}`},
	} {
		t.Run(tc.name, func(t *testing.T) {
			canonical, digest, err := hashValue([]byte(tc.input))
			if err != nil || !bytes.Equal(canonical, []byte(tc.expected)) {
				t.Fatalf("unexpected canonical bytes %q: %v", canonical, err)
			}
			want := sha256.Sum256([]byte(tc.expected))
			if digest != "sha256:"+hex.EncodeToString(want[:]) {
				t.Fatal("digest does not bind independent expected bytes")
			}
		})
	}
}

func TestStrictCanonicalRejections(t *testing.T) {
	for _, input := range []string{`{"a":1,"a":2}`, `{"a":1,"\u0061":2}`, `{"x":{"a":1,"a":2}}`, `{"x":"\ud800"}`, `{"x":NaN}`, `{"x":1e999}`, `{} {}`} {
		if _, _, err := hashValue([]byte(input)); err == nil {
			t.Fatalf("accepted invalid or ambiguous input %q", input)
		}
	}
}
