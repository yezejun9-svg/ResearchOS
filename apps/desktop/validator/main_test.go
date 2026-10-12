package main

import (
	"encoding/base64"
	"encoding/json"
	"os"
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

func TestWireFirstUseHostStatusAcceptsCoreRevisionAndKeepsIdentity(t *testing.T) {
	const request = `{"protocol_version":"researchos-client/2","command_id":"private-unit","client_id":"desktop-shell","method":"host.status","project_id":null,"session_id":null,"expected_revision":null,"writer_epoch":null,"payload":{}}`
	raw, err := os.ReadFile("../../../tests/contracts/fixtures/client_protocol_v2_fixtures.json")
	if err != nil {
		t.Fatal(err)
	}
	var catalog struct {
		Fixtures []struct {
			Name  string         `json:"name"`
			Value map[string]any `json:"value"`
		} `json:"fixtures"`
	}
	if err := json.Unmarshal(raw, &catalog); err != nil {
		t.Fatal(err)
	}
	var template map[string]any
	for _, row := range catalog.Fixtures {
		if row.Name == "valid_response_host_status" {
			template = row.Value
			break
		}
	}
	if template == nil {
		t.Fatal("published host.status response fixture missing")
	}
	check := func(name, expected, reason string, mutate func(map[string]any)) {
		t.Helper()
		t.Run(name, func(t *testing.T) {
			var response map[string]any
			if err := json.Unmarshal(mustWireJSON(template), &response); err != nil {
				t.Fatal(err)
			}
			response["command_id"] = "private-unit"
			response["session_id"] = nil
			response["revision"] = float64(1) // Core's actual complete(1, result) projection.
			response["result"].(map[string]any)["client_id"] = "desktop-shell"
			mutate(response)
			packet := map[string]any{"schema": protocol, "phase": "RESPONSE",
				"nonce": "12345678-1234-1234-1234-123456789abc", "http_status": 200,
				"request_raw_base64":  base64.StdEncoding.EncodeToString([]byte(request)),
				"response_raw_base64": base64.StdEncoding.EncodeToString(mustWireJSON(response))}
			got := validate(mustWireJSON(packet))
			if got.Outcome != expected || got.Reason != reason {
				t.Fatalf("host.status %s: %+v", name, got)
			}
		})
	}
	check("revision-one", "VALID", "", func(map[string]any) {})
	check("revision-null-schema-valid", "VALID", "", func(r map[string]any) { r["revision"] = nil })
	check("foreign-client", "REFUSED", "RESPONSE_IDENTITY", func(r map[string]any) { r["result"].(map[string]any)["client_id"] = "other-client" })
	check("foreign-session", "REFUSED", "RESPONSE_IDENTITY", func(r map[string]any) { r["session_id"] = "other-session" })
	check("foreign-command", "REFUSED", "RESPONSE_IDENTITY", func(r map[string]any) { r["command_id"] = "other-command" })
	check("schema-invalid-revision", "REFUSED", "INVALID_RESPONSE_SCHEMA", func(r map[string]any) { r["revision"] = float64(0) })
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
