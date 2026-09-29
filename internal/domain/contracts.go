package domain

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/santhosh-tekuri/jsonschema/v6"
	"researchos.local/research-os/internal/canonical"
)

type Object = map[string]any
type Contracts struct {
	Schemas    map[string]*jsonschema.Schema
	Entities   map[string]bool
	Operations []Operation
}
type Operation struct {
	ID, Method, Path, Request, Response, Target, Owner string
	Roles                                              []string
	Implemented                                        bool
}
type localOnly struct{}

func (localOnly) Load(url string) (any, error) {
	return nil, fmt.Errorf("unregistered schema resource: %s", url)
}
func Decode(raw []byte) (Object, error) {
	b, e := canonical.JSON(raw)
	if e != nil {
		return nil, e
	}
	var o Object
	d := json.NewDecoder(bytes.NewReader(b))
	d.UseNumber()
	e = d.Decode(&o)
	if o == nil && e == nil {
		e = fmt.Errorf("object required")
	}
	return o, e
}
func Bytes(v any) []byte {
	b, e := json.Marshal(v)
	if e != nil {
		panic(e)
	}
	return b
}
func Digest(b []byte) string { h := sha256.Sum256(b); return "sha256:" + hex.EncodeToString(h[:]) }
func Hash(v any) string {
	b, e := canonical.JSON(Bytes(v))
	if e != nil {
		panic(e)
	}
	return Digest(b)
}
func Receipt(o Object) string {
	c := Object{}
	for k, v := range o {
		if k != "receipt_hash" {
			c[k] = v
		}
	}
	return Hash(c)
}
func Str(o Object, k string) string { s, _ := o[k].(string); return s }
func Num(o Object, k string) int64 {
	switch n := o[k].(type) {
	case json.Number:
		v, _ := n.Int64()
		return v
	case int:
		return int64(n)
	case int64:
		return n
	case float64:
		return int64(n)
	}
	return 0
}
func Arr(o Object, k string) []any { a, _ := o[k].([]any); return a }
func Ref(o Object, kind string) Object {
	var h any
	if kind == "Artifact" {
		h = o["content_hash"]
	} else if v, ok := o["receipt_hash"]; ok {
		h = v
	}
	return Object{"entity_type": kind, "id": o["id"], "revision": o["revision"], "content_hash": h}
}
func (c *Contracts) Validate(name string, v any) error {
	s, ok := c.Schemas[name]
	if !ok {
		return fmt.Errorf("unknown schema %s", name)
	}
	var j any
	d := json.NewDecoder(bytes.NewReader(Bytes(v)))
	d.UseNumber()
	if e := d.Decode(&j); e != nil {
		return e
	}
	return s.Validate(j)
}
func LoadContracts(dir string) (*Contracts, error) {
	raw, e := os.ReadFile(filepath.Join(dir, "domain.schema.json"))
	if e != nil {
		return nil, e
	}
	doc, e := Decode(raw)
	if e != nil {
		return nil, e
	}
	compiler := jsonschema.NewCompiler()
	compiler.UseLoader(localOnly{})
	compiler.AssertFormat()
	compiler.DefaultDraft(jsonschema.Draft2020)
	const location = "https://researchos.invalid/domain.schema.json"
	if e = compiler.AddResource(location, doc); e != nil {
		return nil, e
	}
	c := &Contracts{Schemas: map[string]*jsonschema.Schema{}, Entities: map[string]bool{}}
	for name := range doc["$defs"].(map[string]any) {
		s, e := compiler.Compile(location + "#/$defs/" + name)
		if e != nil {
			return nil, e
		}
		c.Schemas[name] = s
	}
	for _, v := range doc["oneOf"].([]any) {
		c.Entities[strings.TrimPrefix(v.(map[string]any)["$ref"].(string), "#/$defs/")] = true
	}
	raw, e = os.ReadFile(filepath.Join(dir, "openapi.json"))
	if e != nil {
		return nil, e
	}
	api, e := Decode(raw)
	if e != nil {
		return nil, e
	}
	if e = compiler.AddResource("https://researchos.invalid/openapi.json", api); e != nil {
		return nil, e
	}
	for name := range api["components"].(map[string]any)["schemas"].(map[string]any) {
		if _, ok := c.Schemas[name]; !ok {
			sch, e := compiler.Compile("https://researchos.invalid/openapi.json#/components/schemas/" + name)
			if e != nil {
				return nil, e
			}
			c.Schemas[name] = sch
		}
	}
	for path, p := range api["paths"].(map[string]any) {
		for method, v := range p.(map[string]any) {
			o, ok := v.(map[string]any)
			if !ok || o["operationId"] == nil {
				continue
			}
			op := Operation{ID: Str(o, "operationId"), Method: strings.ToUpper(method), Path: path, Target: Str(o, "x-precondition-target")}
			for _, r := range Arr(o, "x-required-roles") {
				op.Roles = append(op.Roles, r.(string))
			}
			if rb, ok := o["requestBody"].(map[string]any); ok {
				op.Request = schemaName(rb)
			}
			if rs, ok := o["responses"].(map[string]any); ok {
				for code, r := range rs {
					if strings.HasPrefix(code, "2") {
						op.Response = schemaName(r.(map[string]any))
					}
				}
			}
			op.Owner = operationOwner(op.ID)
			op.Implemented = implemented[op.ID]
			c.Operations = append(c.Operations, op)
		}
	}
	return c, nil
}
func schemaName(o Object) string {
	if c, ok := o["content"].(map[string]any); ok {
		if j, ok := c["application/json"].(map[string]any); ok {
			if s, ok := j["schema"].(map[string]any); ok {
				r := Str(s, "$ref")
				return r[strings.LastIndex(r, "/")+1:]
			}
		}
	}
	return ""
}

var implemented = map[string]bool{}

func init() {
	for _, s := range strings.Fields("listProjects createProject getProjectProfile getProjectState listRequirement getRequirement createRequirement actOnRequirement listGoal getGoal createGoal listTask getTask createTask actOnTask listArtifact getArtifact uploadContent sealArtifact getArtifactContent getGlobalBudgetPolicy getGlobalRunPolicy getBudgetPolicy getRunPolicy getGoalBudgetPolicy listEvents") {
		implemented[s] = true
	}
}
func operationOwner(id string) string {
	if implemented[id] {
		return "W03"
	}
	for _, x := range []struct{ owner, words string }{{"W17", "Device Pairing Session"}, {"W05", "Runtime heartbeatRun reportRun cancelRun acknowledgeRunCancellation reconcileRun listRun getRun"}, {"W04", "Requirement Change Context Impact Conflict Message"}, {"W06", "Goal Task Acceptance"}, {"W07", "Evidence SourceCursor"}, {"W08", "ResearchCycle"}, {"W09", "searchEvidence"}, {"W10", "Experiment"}, {"W11", "Decision Qualification"}, {"W12", "Budget RunPolicy Resource NoProgress"}, {"W13", "Milestone Notification Progress streamEvents"}, {"W15", "Skill"}, {"W16", "SystemCandidate"}} {
		for _, w := range strings.Fields(x.words) {
			if strings.Contains(id, w) {
				return x.owner
			}
		}
	}
	return "W12"
}
