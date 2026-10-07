package main

import (
	"encoding/base64"
	"encoding/json"
	"strings"
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

func TestWirePrivatePacketExactKeysAndTypes(t *testing.T) {
	request := `{"protocol_version":"researchos-client/2","command_id":"private-unit","client_id":"desktop-shell","method":"host.status","project_id":null,"session_id":null,"expected_revision":null,"writer_epoch":null,"payload":{}}`
	fields := map[string]any{"schema": protocol, "phase": "REQUEST", "nonce": "12345678-1234-1234-1234-123456789abc", "http_status": nil, "request_raw_base64": base64.StdEncoding.EncodeToString([]byte(request)), "response_raw_base64": ""}
	raw, _ := json.Marshal(fields)
	if got := validate(raw); got.Outcome != "VALID" {
		t.Fatalf("positive request: %+v", got)
	}
	for _, key := range []string{"schema", "phase", "nonce", "request_raw_base64", "response_raw_base64"} {
		for _, bad := range []any{nil, true, 1, []any{}, map[string]any{}} {
			t.Run(key+"/"+string(mustWireJSON(bad)), func(t *testing.T) {
				copy := map[string]any{}
				for k, v := range fields {
					copy[k] = v
				}
				copy[key] = bad
				if got := validate(mustWireJSON(copy)); got.Outcome != "REFUSED" || got.Reason != "PRIVATE_PACKET" {
					t.Fatalf("accepted wrong field type: %+v", got)
				}
			})
		}
	}
	for _, key := range []string{"schema", "phase", "nonce", "http_status", "request_raw_base64", "response_raw_base64"} {
		for _, kind := range []string{"case-alias", "missing", "extra", "duplicate"} {
			t.Run(key+"/"+kind, func(t *testing.T) {
				copy := map[string]any{}
				for k, v := range fields {
					copy[k] = v
				}
				switch kind {
				case "case-alias":
					delete(copy, key)
					copy[strings.ToUpper(key)] = fields[key]
				case "missing":
					delete(copy, key)
				case "extra":
					copy["extra"] = nil
				}
				candidate := mustWireJSON(copy)
				if kind == "duplicate" {
					candidate = append(candidate[:len(candidate)-1], []byte(`,"`+key+`":null}`)...)
				}
				if got := validate(candidate); got.Outcome != "REFUSED" || got.Reason != "PRIVATE_PACKET" {
					t.Fatalf("accepted wrong member set: %+v", got)
				}
			})
		}
	}
	for _, literal := range []string{"null", "true", `"200"`, "99", "600", "200.0000000000000001", "{}", "[]"} {
		t.Run("response-status/"+literal, func(t *testing.T) {
			candidate := strings.Replace(string(raw), `"REQUEST"`, `"RESPONSE"`, 1)
			candidate = strings.Replace(candidate, `"http_status":null`, `"http_status":`+literal, 1)
			if got := validate([]byte(candidate)); got.Outcome != "REFUSED" || got.Reason != "PRIVATE_PACKET" {
				t.Fatalf("accepted invalid status: %+v", got)
			}
		})
	}
	for _, literal := range []string{"100", "100.0", "1e2", "599"} {
		t.Run("valid-response-status/"+literal, func(t *testing.T) {
			candidate := strings.Replace(string(raw), `"REQUEST"`, `"RESPONSE"`, 1)
			candidate = strings.Replace(candidate, `"http_status":null`, `"http_status":`+literal, 1)
			if got := validate([]byte(candidate)); got.Outcome != "HTTP_ERROR" {
				t.Fatalf("rejected integral status: %+v", got)
			}
		})
	}
	for _, prefix := range []string{"\u00a0", "\ufeff", "\v", "\f"} {
		if got := validate(append([]byte(prefix), raw...)); got.Outcome != "REFUSED" {
			t.Fatal("accepted non-JSON whitespace")
		}
	}
	if got := validate(append([]byte(" \t\r\n"), raw...)); got.Outcome != "VALID" {
		t.Fatal("rejected JSON whitespace")
	}
}

func mustWireJSON(value any) []byte {
	raw, err := json.Marshal(value)
	if err != nil {
		panic(err)
	}
	return raw
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
