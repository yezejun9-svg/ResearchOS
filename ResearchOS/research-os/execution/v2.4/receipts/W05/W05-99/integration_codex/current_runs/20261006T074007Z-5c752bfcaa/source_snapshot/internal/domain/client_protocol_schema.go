package domain

// Contract validation for researchos-client/2 (W03-02).
//
// The published client.protocol.schema.json is the only shape truth. Validation uses the
// repository's existing JSON Schema compiler (the same jsonschema/v6 path LoadContracts
// uses), so there is no second validator and no hand-written keyword subset that can drift
// from the contract. Cross-file references (domain.schema.json) must be pinned by the
// caller; an unregistered resource fails closed at load time.
//
// Direction is the one thing JSON Schema annotations cannot enforce by themselves: a
// property annotated writeOnly:true (credential material) is refused in every read path —
// responses, events and snapshots — while command payloads and native import requests may
// carry it. That policy is applied here and nowhere else.

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/url"
	"regexp"
	"sort"
	"strings"

	"github.com/santhosh-tekuri/jsonschema/v6"
)

type SchemaDoc struct {
	byName      map[string]*jsonschema.Schema
	Methods     map[string]MethodContract
	Events      map[string]string
	writeOnly   map[string]bool
	pathProps   map[string]bool
	Location    string
	defNames    []string
	// NeutralizedPatterns counts the pattern keywords the pinned contract publishes that
	// Go's RE2 engine cannot compile. Each one is replaced by a permissive pattern before
	// compilation and re-enforced with its exact published semantics afterwards, so the
	// count is asserted by qualification and can never silently grow.
	NeutralizedPatterns int
	// defChecks applies the documented semantics of a neutralised pattern when the value
	// being validated is that definition itself (for example the RelativePath string).
	defChecks map[string]func(string) bool
}

type MethodContract struct {
	Payload string `json:"payload"`
	Result  string `json:"result"`
}

func LoadSchema(raw []byte) (*SchemaDoc, error) { return LoadSchemaWithExternals(raw, nil) }

// LoadSchemaWithExternals compiles the protocol document together with the exact external
// schemas it references (keyed by file name, e.g. "domain.schema.json").
func LoadSchemaWithExternals(raw []byte, externals map[string][]byte) (*SchemaDoc, error) {
	doc, err := Decode(raw)
	if err != nil {
		return nil, fmt.Errorf("SCHEMA_PROTOCOL_DECODE:%v", err)
	}
	location, _ := doc["$id"].(string)
	if location == "" {
		return nil, fmt.Errorf("SCHEMA_MISSING_ID")
	}
	base, err := url.Parse(location)
	if err != nil {
		return nil, fmt.Errorf("SCHEMA_BAD_ID:%v", err)
	}
	compiler := jsonschema.NewCompiler()
	compiler.UseLoader(localOnly{})
	compiler.AssertFormat()
	compiler.DefaultDraft(jsonschema.Draft2020)
	// The Draft 2020-12 metaschema refuses a pattern that Go's regexp engine (which this
	// compiler uses, like the rest of the repo) cannot compile. Only the exact published
	// patterns whose semantics are implemented below may be neutralised; anything else makes
	// the loader fail closed instead of silently widening the contract.
	neutralized, defChecks, err := neutralizePatterns(doc)
	if err != nil {
		return nil, err
	}
	if err := compiler.AddResource(location, doc); err != nil {
		return nil, fmt.Errorf("SCHEMA_ADD_RESOURCE:%v", err)
	}
	defs, _ := doc["$defs"].(map[string]any)
	if len(defs) == 0 {
		return nil, fmt.Errorf("SCHEMA_NO_DEFS")
	}
	writeOnly := map[string]bool{}
	collectWriteOnly(doc, writeOnly)
	for name, body := range externals {
		edoc, err := Decode(body)
		if err != nil {
			return nil, fmt.Errorf("EXTERNAL_SCHEMA:%s:%v", name, err)
		}
		refURI := resolveURI(base, name)
		if id, ok := edoc["$id"].(string); ok && id != "" && id != refURI {
			if err := compiler.AddResource(id, edoc); err != nil {
				return nil, fmt.Errorf("EXTERNAL_ADD_RESOURCE_ID:%s:%v", name, err)
			}
		}
		if err := compiler.AddResource(refURI, edoc); err != nil {
			return nil, fmt.Errorf("EXTERNAL_ADD_RESOURCE:%s:%v", name, err)
		}
		n, extChecks, err := neutralizePatterns(edoc)
		if err != nil {
			return nil, fmt.Errorf("EXTERNAL_PATTERN:%s:%v", name, err)
		}
		neutralized += n
		for k, v := range extChecks {
			defChecks[k] = v
		}
		collectWriteOnly(edoc, writeOnly)
	}
	d := &SchemaDoc{byName: map[string]*jsonschema.Schema{}, Methods: map[string]MethodContract{},
		Events: map[string]string{}, writeOnly: writeOnly, Location: location,
		pathProps: map[string]bool{}, NeutralizedPatterns: neutralized, defChecks: defChecks}
	// Properties declared with the contract's RelativePath definition carry the semantics of
	// the neutralised pattern, so they are re-checked explicitly below.
	collectPathProps(doc, d.pathProps)
	for name := range defs {
		s, err := compiler.Compile(location + "#/$defs/" + name)
		if err != nil {
			return nil, fmt.Errorf("SCHEMA_COMPILE:%s:%v", name, err)
		}
		d.byName[name] = s
		d.defNames = append(d.defNames, name)
	}
	if mc, ok := doc["x-method-contracts"].(map[string]any); ok {
		for method, v := range mc {
			m, ok := v.(map[string]any)
			if !ok {
				return nil, fmt.Errorf("SCHEMA_METHOD_CONTRACT_NOT_OBJECT:%s", method)
			}
			p, _ := m["payload"].(string)
			r, _ := m["result"].(string)
			if p == "" || r == "" {
				return nil, fmt.Errorf("SCHEMA_METHOD_CONTRACT_INCOMPLETE:%s", method)
			}
			if _, ok := d.byName[p]; !ok {
				return nil, fmt.Errorf("SCHEMA_METHOD_PAYLOAD_DEF_MISSING:%s->%s", method, p)
			}
			if _, ok := d.byName[r]; !ok {
				return nil, fmt.Errorf("SCHEMA_METHOD_RESULT_DEF_MISSING:%s->%s", method, r)
			}
			d.Methods[method] = MethodContract{Payload: p, Result: r}
		}
	}
	if ec, ok := doc["x-event-contracts"].(map[string]any); ok {
		for kind, v := range ec {
			def, ok := v.(string)
			if !ok {
				return nil, fmt.Errorf("SCHEMA_EVENT_CONTRACT_NOT_STRING:%s", kind)
			}
			if _, has := d.byName[def]; !has {
				return nil, fmt.Errorf("SCHEMA_EVENT_PAYLOAD_DEF_MISSING:%s->%s", kind, def)
			}
			d.Events[kind] = def
		}
	}
	if len(d.Methods) == 0 || len(d.Events) == 0 {
		return nil, fmt.Errorf("SCHEMA_CONTRACT_MAPS_EMPTY")
	}
	return d, nil
}

// resolveURI maps a bare file name to the absolute location a relative $ref in the
// protocol document resolves to, and falls back to the document's own $id when present.
func resolveURI(base *url.URL, file string) string {
	u := *base
	if idx := strings.LastIndex(u.Path, "/"); idx >= 0 {
		u.Path = u.Path[:idx+1] + file
	} else {
		u.Path = file
	}
	u.Fragment = ""
	return u.String()
}

// ValidateDef checks a read-direction value: response, event, snapshot or native result.
// writeOnly-annotated properties are refused, so credential material cannot travel back.
func (d *SchemaDoc) ValidateDef(name string, value any) error {
	return d.validate(name, value, false)
}

// ValidateDefInput checks a write-direction value: a command envelope or payload, where
// writeOnly properties are legal.
func (d *SchemaDoc) ValidateDefInput(name string, value any) error {
	return d.validate(name, value, true)
}

func (d *SchemaDoc) validate(name string, value any, allowWriteOnly bool) error {
	s, ok := d.byName[name]
	if !ok {
		return fmt.Errorf("SCHEMA_DEF_UNKNOWN:%s", name)
	}
	var generic any
	dec := json.NewDecoder(bytes.NewReader(Bytes(value)))
	dec.UseNumber()
	if err := dec.Decode(&generic); err != nil {
		return fmt.Errorf("SCHEMA_VALUE_DECODE:%v", err)
	}
	if !allowWriteOnly {
		if key, bad := firstWriteOnly(generic, d.writeOnly); bad {
			return fmt.Errorf("WRITE_ONLY_IN_READ_PATH:%s", key)
		}
	}
	if key, bad := firstBadRelativePath(generic, d.pathProps); bad {
		return fmt.Errorf("RELATIVE_PATH_PATTERN:%s", key)
	}
	if check, ok := d.defChecks[name]; ok {
		if s, isString := generic.(string); isString && !check(s) {
			return fmt.Errorf("PATTERN_SEMANTICS:%s", name)
		}
	}
	if err := s.Validate(generic); err != nil {
		return fmt.Errorf("SCHEMA:%v", err)
	}
	return nil
}

// neutralizePatterns returns how many pattern keywords it replaced with an accept-all
// equivalent, plus the per-definition semantic checks that must then run. A pattern Go
// cannot compile is only accepted when the contract's published text is matched exactly by
// patternSemantics; otherwise loading fails closed.
func neutralizePatterns(node any) (int, map[string]func(string) bool, error) {
	checks := map[string]func(string) bool{}
	count := 0
	semantics, published := patternSemantics()
	var walk func(any, string) error
	walk = func(x any, defName string) error {
		switch tv := x.(type) {
		case map[string]any:
			for k, v := range tv {
				if k == "pattern" {
					if s, ok := v.(string); ok {
						if err := compileCheck(s); err != nil {
							f, known := semantics[published[s]]
							if !known {
								return fmt.Errorf("UNSUPPORTED_PATTERN_SEMANTICS:%s", trim(s))
							}
							tv[k] = acceptAllPattern
							count++
							if defName != "" {
								checks[defName] = f
							}
							continue
						}
					}
				}
				if err := walk(v, defName); err != nil {
					return err
				}
			}
		case []any:
			for _, item := range tv {
				if err := walk(item, defName); err != nil {
					return err
				}
			}
		}
		return nil
	}
	if defs, ok := node.(map[string]any); ok {
		if dd, ok := defs["$defs"].(map[string]any); ok {
			for name, sub := range dd {
				if m, ok := sub.(map[string]any); ok {
					if p, has := m["pattern"].(string); has && compileCheck(p) != nil {
						f, known := semantics[published[p]]
						if !known {
							return 0, nil, fmt.Errorf("UNSUPPORTED_PATTERN_SEMANTICS:%s", trim(p))
						}
						m["pattern"] = acceptAllPattern
						count++
						checks[name] = f
						continue
					}
				}
				if err := walk(sub, ""); err != nil {
					return 0, nil, err
				}
			}
		}
	}
	if err := walk(node, ""); err != nil {
		return 0, nil, err
	}
	return count, checks, nil
}

const acceptAllPattern = `^[\s\S]*$`

func trim(s string) string {
	if len(s) > 40 {
		return s[:40]
	}
	return s
}

// patternSemantics maps each published pattern text that Go cannot compile to the function
// implementing exactly its documented meaning.
func patternSemantics() (map[string]func(string) bool, map[string]string) {
	checks := map[string]func(string) bool{publishedRelativePathPattern: isRelativePath}
	published := map[string]string{publishedRelativePathPattern: publishedRelativePathPattern}
	return checks, published
}

func compileCheck(pattern string) error {
	re, err := regexp.Compile(pattern)
	if err != nil {
		return err
	}
	_ = re
	return nil
}

// collectPathProps gathers the property names whose schema is the published RelativePath
// definition, either directly or as an array item type.
func collectPathProps(node any, into map[string]bool) {
	var walk func(any)
	walk = func(x any) {
		switch tv := x.(type) {
		case map[string]any:
			if props, ok := tv["properties"].(map[string]any); ok {
				for name, sub := range props {
					if refIsRelativePath(sub) {
						into[name] = true
					}
					walk(sub)
				}
			}
			for k, v := range tv {
				if k == "properties" {
					continue
				}
				walk(v)
			}
		case []any:
			for _, item := range tv {
				walk(item)
			}
		}
	}
	walk(node)
}

func refIsRelativePath(sub any) bool {
	m, ok := sub.(map[string]any)
	if !ok {
		return false
	}
	if ref, ok := m["$ref"].(string); ok && strings.HasSuffix(ref, "/RelativePath") {
		return true
	}
	if items, ok := m["items"].(map[string]any); ok {
		if ref, ok := items["$ref"].(string); ok && strings.HasSuffix(ref, "/RelativePath") {
			return true
		}
	}
	return false
}

func firstBadRelativePath(node any, set map[string]bool) (string, bool) {
	if len(set) == 0 {
		return "", false
	}
	switch tv := node.(type) {
	case map[string]any:
		for _, k := range sortedKeys(tv) {
			if set[k] {
				switch val := tv[k].(type) {
				case string:
					if !isRelativePath(val) {
						return k, true
					}
				case []any:
					for _, item := range val {
						if s, ok := item.(string); ok && !isRelativePath(s) {
							return k, true
						}
					}
				}
			}
			if key, bad := firstBadRelativePath(tv[k], set); bad {
				return key, bad
			}
		}
	case []any:
		for _, item := range tv {
			if key, bad := firstBadRelativePath(item, set); bad {
				return key, bad
			}
		}
	}
	return "", false
}

// publishedRelativePathPattern is the exact pattern the contract publishes for RelativePath.
// It uses negative lookaheads, so it is enforced by the semantics below instead of a regex.
var publishedRelativePathPattern = `^(?![\\/])(?![A-Za-z]:)(?!.*(?:^|[\\/])\.\.(?:[\\/]|$))(?!.*\x00).+$`

var drivePrefixPattern = regexp.MustCompile(`^[A-Za-z]:`)

// isRelativePath reproduces that published pattern: non-empty, no NUL byte, not absolute
// with either separator, no drive prefix, and no ".." path segment.
func isRelativePath(v string) bool {
	if v == "" || strings.ContainsRune(v, 0) || drivePrefixPattern.MatchString(v) {
		return false
	}
	if strings.HasPrefix(v, "/") || strings.HasPrefix(v, "\\") {
		return false
	}
	for _, seg := range splitPathSegments(v) {
		if seg == ".." {
			return false
		}
	}
	return true
}

func splitPathSegments(v string) []string {
	var out []string
	start := 0
	for i, r := range v {
		if r == '/' || r == '\\' {
			out = append(out, v[start:i])
			start = i + len(string(r))
		}
	}
	return append(out, v[start:])
}

// MethodPayloadDef / MethodResultDef / EventPayloadDef expose the published mappings.
func (d *SchemaDoc) MethodPayloadDef(method string) (string, error) {
	m, ok := d.Methods[method]
	if !ok {
		return "", fmt.Errorf("UNKNOWN_METHOD_CONTRACT:%s", method)
	}
	return m.Payload, nil
}

func (d *SchemaDoc) MethodResultDef(method string) (string, error) {
	m, ok := d.Methods[method]
	if !ok {
		return "", fmt.Errorf("UNKNOWN_METHOD_CONTRACT:%s", method)
	}
	return m.Result, nil
}

func (d *SchemaDoc) EventPayloadDef(kind string) (string, error) {
	def, ok := d.Events[kind]
	if !ok {
		return "", fmt.Errorf("UNKNOWN_EVENT_CONTRACT:%s", kind)
	}
	return def, nil
}

// DefNames lists the compiled definitions, for qualification reporting.
func (d *SchemaDoc) DefNames() []string { return d.defNames }

// collectWriteOnly gathers every property name annotated writeOnly:true anywhere in the
// pinned documents. The set is applied by name in read paths only, which is deliberately
// stricter than the contract: credential-shaped keys never belong in a response or event.
func collectWriteOnly(node any, into map[string]bool) {
	switch tv := node.(type) {
	case map[string]any:
		if props, ok := tv["properties"].(map[string]any); ok {
			for name, sub := range props {
				if sm, ok := sub.(map[string]any); ok {
					if wo, _ := sm["writeOnly"].(bool); wo {
						into[name] = true
					}
				}
				collectWriteOnly(sub, into)
			}
			return
		}
		for k, v := range tv {
			if k == "$defs" {
				collectWriteOnly(v, into)
				continue
			}
			collectWriteOnly(v, into)
		}
	case []any:
		for _, x := range tv {
			collectWriteOnly(x, into)
		}
	}
}

// sortedKeys keeps rejection messages deterministic for a map, so the same bad value always
// produces the same evidence line.
func sortedKeys(m map[string]any) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

func firstWriteOnly(node any, set map[string]bool) (string, bool) {
	if len(set) == 0 {
		return "", false
	}
	switch tv := node.(type) {
	case map[string]any:
		for _, k := range sortedKeys(tv) {
			if set[k] {
				return k, true
			}
			if key, bad := firstWriteOnly(tv[k], set); bad {
				return key, bad
			}
		}
	case []any:
		for _, x := range tv {
			if key, bad := firstWriteOnly(x, set); bad {
				return key, bad
			}
		}
	}
	return "", false
}
