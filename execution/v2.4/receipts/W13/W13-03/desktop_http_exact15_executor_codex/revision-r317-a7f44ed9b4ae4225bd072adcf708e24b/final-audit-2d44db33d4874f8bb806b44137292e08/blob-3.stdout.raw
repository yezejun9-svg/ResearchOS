// Command client-wire-validator validates one bounded, private Desktop packet.
// It never opens a Host, database, credential store, or network connection.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"encoding/json/jsontext"
	"errors"
	"fmt"
	"io"
	"math/big"
	"os"
	"researchos.local/research-os/internal/api"
	"sort"
	"strconv"
)

const protocol = "researchos.desktop.http-validation/1"
const requestLimit = 8388608
const responseLimit = 16777216
const frameLimit = 33555460
const outputLimit = 67108864
const schemaHash = "8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b"
const domainHash = "b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54"

// Filled by the local, source-bound builder, not by a caller or environment.
var buildInputDigest = "UNBUILT"
var resourceLimit = errors.New("LOCAL_RESOURCE_LIMIT")
var invalidJSON = errors.New("INVALID_JSON")

type packet struct {
	Schema   string `json:"schema"`
	Phase    string `json:"phase"`
	Nonce    string `json:"nonce"`
	Status   *int   `json:"http_status"`
	Request  string `json:"request_raw_base64"`
	Response string `json:"response_raw_base64"`
}
type verdict struct {
	Schema       string   `json:"schema"`
	Phase        string   `json:"phase"`
	Nonce        string   `json:"nonce"`
	Status       *int     `json:"http_status"`
	RequestHash  string   `json:"request_sha256"`
	ResponseHash string   `json:"response_sha256"`
	SchemaHashes []string `json:"schema_sha256_pair"`
	Build        string   `json:"build_input_digest"`
	Outcome      string   `json:"outcome"`
	Reason       string   `json:"reason"`
	Value        any      `json:"value"`
}

func digest(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func uuid(s string) bool {
	if len(s) != 36 {
		return false
	}
	for i, c := range s {
		if i == 8 || i == 13 || i == 18 || i == 23 {
			if c != '-' {
				return false
			}
		} else if !(c >= '0' && c <= '9' || c >= 'a' && c <= 'f') {
			return false
		}
	}
	return true
}
func decode64(s string, max int) ([]byte, error) {
	if len(s) > 4*((max+2)/3) {
		return nil, resourceLimit
	}
	b, e := base64.StdEncoding.Strict().DecodeString(s)
	if e != nil || base64.StdEncoding.EncodeToString(b) != s {
		return nil, errors.New("PRIVATE_BASE64")
	}
	if len(b) > max {
		return nil, resourceLimit
	}
	return b, nil
}

// Bound work before either the JSON decoder or jsonschema's big.Rat sees a number.
// The JSON validator below remains the grammar authority; this scanner only caps work.
func precheck(raw []byte) error {
	depth, nodes := 0, 0
	for i := 0; i < len(raw); i++ {
		c := raw[i]
		if c == '"' {
			nodes++
			i++
			for i < len(raw) && raw[i] != '"' {
				if raw[i] == '\\' {
					i++
				}
				i++
			}
		}
		if c == '{' || c == '[' {
			depth++
			nodes++
			if depth > 256 {
				return resourceLimit
			}
		}
		if c == '}' || c == ']' {
			depth--
		}
		if c == '-' || c >= '0' && c <= '9' {
			start := i
			digits := 0
			exponent := false
			exp := 0
			for i < len(raw) {
				d := raw[i]
				if d == 'e' || d == 'E' {
					exponent = true
				} else if d >= '0' && d <= '9' {
					if exponent {
						if exp <= 4096 {
							exp = exp*10 + int(d-'0')
						}
					} else {
						digits++
					}
				} else if d != '.' && d != '+' && d != '-' {
					break
				}
				i++
			}
			if i-start > 8192 || digits > 4096 || exp > 4096 {
				return resourceLimit
			}
			i--
			nodes++
		}
		if c == 't' || c == 'f' || c == 'n' {
			nodes++
		}
		if nodes > 262144 {
			return resourceLimit
		}
	}
	return nil
}

type budget struct{ nodes, strings int }

func (b *budget) walk(v any) error {
	b.nodes++
	if b.nodes > 262144 {
		return resourceLimit
	}
	switch x := v.(type) {
	case string:
		b.strings += len(x)
	case map[string]any:
		for k, v := range x {
			b.strings += len(k)
			if e := b.walk(v); e != nil {
				return e
			}
		}
	case []any:
		for _, v := range x {
			if e := b.walk(v); e != nil {
				return e
			}
		}
	}
	if b.strings > requestLimit+responseLimit {
		return resourceLimit
	}
	return nil
}
func decode(raw []byte, b *budget) (any, error) {
	if e := precheck(raw); e != nil {
		return nil, e
	}
	if !jsontext.Value(raw).IsValid() {
		return nil, invalidJSON
	}
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var v any
	if e := dec.Decode(&v); e != nil {
		return nil, invalidJSON
	}
	if e := b.walk(v); e != nil {
		return nil, e
	}
	return v, nil
}
func equal(a, b any) bool {
	if an, ok := a.(json.Number); ok {
		bn, ok := b.(json.Number)
		if !ok {
			return false
		}
		ar, aok := new(big.Rat).SetString(string(an))
		br, bok := new(big.Rat).SetString(string(bn))
		return aok && bok && ar.Cmp(br) == 0
	}
	return a == b
}
func obj(v any) map[string]any { m, _ := v.(map[string]any); return m }
func identity(req, res map[string]any) error {
	bad := errors.New("RESPONSE_IDENTITY")
	for _, k := range []string{"protocol_version", "command_id", "method"} {
		if !equal(req[k], res[k]) {
			return bad
		}
	}
	method, _ := req["method"].(string)
	complete := res["status"] == "COMPLETED"
	result := obj(res["result"])
	derived := complete && method == "session.create"
	if !derived && !equal(req["session_id"], res["session_id"]) {
		return bad
	}
	if derived {
		if _, ok := res["session_id"].(string); !ok {
			return bad
		}
	}
	if !complete {
		return nil
	}
	if method == "host.status" {
		if !equal(result["client_id"], req["client_id"]) {
			return bad
		}
		if res["session_id"] != nil || res["revision"] != nil {
			return bad
		}
	}
	snapshot := obj(result["snapshot"])
	if method == "session.get" || method == "session.create" || method == "session.update" {
		snapshot = result
	}
	if snapshot != nil {
		if !equal(snapshot["project_id"], req["project_id"]) {
			return bad
		}
		if method == "goal.start" && req["session_id"] == nil {
			// Project goal creates a result session without adopting it as request context.
			if res["session_id"] != nil {
				return bad
			}
		} else if !equal(snapshot["session_id"], res["session_id"]) {
			return bad
		}
		if res["session_id"] != nil && res["revision"] == nil {
			return bad
		}
		if res["revision"] != nil && !equal(snapshot["revision"], res["revision"]) {
			return bad
		}
		if method == "session.attach" && result["write_owner_acquired"] == true {
			if !equal(obj(snapshot["writer"])["client_id"], req["client_id"]) {
				return bad
			}
		}
	}
	if method == "session.events" {
		events, _ := result["events"].([]any)
		for _, e := range events {
			m := obj(e)
			if !equal(m["session_id"], req["session_id"]) {
				return bad
			}
			if p, ok := m["project_id"]; ok && !equal(p, req["project_id"]) {
				return bad
			}
		}
	}
	if method == "session.list" {
		sessions, _ := result["items"].([]any)
		for _, s := range sessions {
			if !equal(obj(s)["project_id"], req["project_id"]) {
				return bad
			}
		}
	}
	if method == "host.configure" {
		payload := obj(req["payload"])
		for _, key := range []string{"config_revision", "provider_id", "base_url", "model_id", "credential_ref"} {
			if !equal(result[key], payload[key]) {
				return bad
			}
		}
	}
	return nil
}

// Uniform nodes prevent an ordinary JSON object from masquerading as a numeric tag.
func tree(v any) any {
	switch x := v.(type) {
	case nil:
		return []any{"null"}
	case bool:
		return []any{"bool", x}
	case string:
		return []any{"string", x}
	case json.Number:
		rat, ok := new(big.Rat).SetString(string(x))
		if !ok {
			panic("validated numeric invariant")
		}
		if rat.IsInt() {
			return []any{"integer", string(x), rat.Num().String()}
		}
		return []any{"decimal", string(x), rat.Num().String(), rat.Denom().String()}
	case []any:
		a := make([]any, len(x))
		for i, v := range x {
			a[i] = tree(v)
		}
		return []any{"array", a}
	case map[string]any:
		keys := make([]string, 0, len(x))
		for k := range x {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		a := make([]any, 0, len(x))
		for _, k := range keys {
			a = append(a, []any{k, tree(x[k])})
		}
		return []any{"object", a}
	}
	panic("validated type invariant")
}
func validate(raw []byte) verdict {
	out := verdict{Schema: protocol, SchemaHashes: []string{schemaHash, domainHash}, Build: buildInputDigest, Outcome: "REFUSED", Reason: "PRIVATE_PACKET"}
	if len(raw) > frameLimit {
		out.Reason = resourceLimit.Error()
		return out
	}
	if e := precheck(raw); e != nil {
		out.Reason = e.Error()
		return out
	}
	if !jsontext.Value(raw).IsValid() {
		return out
	}
	// Check exact decoded member names and non-null types before encoding/json's
	// struct projection can accept case aliases or silently zero a null string.
	var keys map[string]json.RawMessage
	if json.Unmarshal(raw, &keys) != nil || len(keys) != 6 {
		return out
	}
	for _, key := range []string{"schema", "phase", "nonce", "request_raw_base64", "response_raw_base64"} {
		value, exists := keys[key]
		var text string
		if !exists || len(value) == 0 || value[0] != '"' || json.Unmarshal(value, &text) != nil {
			return out
		}
	}
	if _, exists := keys["http_status"]; !exists {
		return out
	}
	var p packet
	for key, target := range map[string]*string{"schema": &p.Schema, "phase": &p.Phase, "nonce": &p.Nonce, "request_raw_base64": &p.Request, "response_raw_base64": &p.Response} {
		if json.Unmarshal(keys[key], target) != nil {
			return out
		}
	}
	if !bytes.Equal(keys["http_status"], []byte("null")) {
		value, err := decode(keys["http_status"], &budget{})
		number, ok := value.(json.Number)
		if err != nil || !ok {
			return out
		}
		rational, ok := new(big.Rat).SetString(string(number))
		if !ok || !rational.IsInt() || !rational.Num().IsInt64() || rational.Num().Int64() < 100 || rational.Num().Int64() > 599 {
			return out
		}
		status := int(rational.Num().Int64())
		p.Status = &status
	}
	if p.Schema != protocol || !uuid(p.Nonce) || (p.Phase != "REQUEST" && p.Phase != "RESPONSE") {
		return out
	}
	out.Nonce = p.Nonce
	out.Phase = p.Phase
	out.Status = p.Status
	if len(raw)-len(p.Request)-len(p.Response) > 1024 {
		out.Reason = resourceLimit.Error()
		return out
	}
	req, e := decode64(p.Request, requestLimit)
	if e != nil {
		out.Reason = e.Error()
		return out
	}
	res, e := decode64(p.Response, responseLimit)
	if e != nil {
		out.Reason = e.Error()
		return out
	}
	out.RequestHash = digest(req)
	out.ResponseHash = digest(res)
	if p.Phase == "REQUEST" {
		if p.Status != nil || len(res) != 0 {
			return out
		}
	} else if p.Status == nil || *p.Status < 100 || *p.Status > 599 {
		return out
	}
	b := &budget{}
	v, e := decode(req, b)
	if e != nil {
		out.Reason = e.Error()
		return out
	}
	doc, e := api.ClientProtocolDocument()
	if e != nil {
		out.Reason = "SCHEMA_RESOURCE"
		return out
	}
	if doc.ValidateDefInput("CommandEnvelope", v) != nil {
		out.Reason = "INVALID_REQUEST_SCHEMA"
		return out
	}
	request := obj(v)
	if request["method"] == "host.configure" && request["session_id"] == nil {
		for _, k := range []string{"project_id", "expected_revision", "writer_epoch"} {
			if request[k] != nil {
				out.Reason = "REQUEST_SCOPE"
				return out
			}
		}
	}
	if p.Phase == "REQUEST" {
		out.Outcome = "VALID"
		out.Reason = ""
		return out
	}
	// Short pre-envelope HTTP errors are a separate layer; never fabricate a full response.
	if *p.Status < 200 || *p.Status >= 300 {
		out.Outcome = "HTTP_ERROR"
		out.Reason = "HTTP_" + strconv.Itoa(*p.Status)
		return out
	}
	v, e = decode(res, b)
	if e != nil {
		out.Reason = e.Error()
		return out
	}
	if doc.ValidateDef("CommandResponse", v) != nil {
		out.Reason = "INVALID_RESPONSE_SCHEMA"
		return out
	}
	if e = identity(request, obj(v)); e != nil {
		out.Reason = e.Error()
		return out
	}
	out.Outcome = "VALID"
	out.Reason = ""
	out.Value = tree(v)
	return out
}
func main() {
	raw, e := io.ReadAll(io.LimitReader(os.Stdin, frameLimit+1))
	if e != nil {
		fmt.Fprintln(os.Stderr, "INPUT_IO")
		os.Exit(1)
	}
	out := validate(raw)
	encoded, e := json.Marshal(out)
	if e != nil || len(encoded) > outputLimit {
		out.Value = nil
		out.Outcome = "REFUSED"
		out.Reason = "LOCAL_RESOURCE_LIMIT"
		encoded, _ = json.Marshal(out)
	}
	if _, e = os.Stdout.Write(append(encoded, '\n')); e != nil {
		os.Exit(1)
	}
}
