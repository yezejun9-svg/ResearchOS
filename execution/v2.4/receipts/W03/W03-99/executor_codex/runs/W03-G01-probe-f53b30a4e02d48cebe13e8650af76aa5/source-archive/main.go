// W03 parent development probes. No formal case or acceptance authority.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
)

type O = map[string]any
type check struct {
	ID     string `json:"id"`
	Group  string `json:"group"`
	Passed bool   `json:"passed"`
	Detail any    `json:"detail"`
}
type fixture struct {
	Name          string          `json:"name"`
	SchemaDef     string          `json:"schema_definition"`
	ExpectedValid bool            `json:"expected_valid"`
	Value         json.RawMessage `json:"value"`
}

var checks = []check{}

func add(group, id string, passed bool, detail any) {
	checks = append(checks, check{id, group, passed, detail})
}
func read(path string) O {
	raw, e := os.ReadFile(path)
	if e != nil {
		panic(e)
	}
	o, e := domain.Decode(raw)
	if e != nil {
		panic(e)
	}
	return o
}
func obj(v any) O { return v.(map[string]any) }
func clone(v O) O {
	o, e := domain.Decode(domain.Bytes(v))
	if e != nil {
		panic(e)
	}
	return o
}
func keys(v map[string]bool) []string {
	a := []string{}
	for k := range v {
		a = append(a, k)
	}
	sort.Strings(a)
	return a
}
func same(a, b any) bool { return domain.Hash(a) == domain.Hash(b) }

// Same schema and runtime decoding sequence as tests/contracts/check/main.go.
// Kept local so the obsolete aggregate checker is never imported or executed.
func validateFixture(doc *domain.SchemaDoc, fx fixture) error {
	var v any
	if e := json.Unmarshal(fx.Value, &v); e != nil {
		return e
	}
	switch fx.SchemaDef {
	case "CommandEnvelope":
		if e := doc.ValidateDefInput(fx.SchemaDef, v); e != nil {
			return e
		}
		_, e := domain.DecodeEnvelope(fx.Value)
		return e
	case "CommandResponse":
		if e := doc.ValidateDef(fx.SchemaDef, v); e != nil {
			return e
		}
		_, e := domain.DecodeResponse(fx.Value)
		return e
	case "SessionEvent":
		if e := doc.ValidateDef(fx.SchemaDef, v); e != nil {
			return e
		}
		ev, e := domain.DecodeEvent(fx.Value)
		if e != nil {
			return e
		}
		return domain.ValidateEventPayload(doc, ev)
	case "SessionSnapshot":
		return doc.ValidateDef(fx.SchemaDef, v)
	default:
		if strings.HasPrefix(fx.SchemaDef, "Native") {
			return domain.ValidateNativeTransient(doc, fx.SchemaDef, fx.Value, strings.HasSuffix(fx.SchemaDef, "Request"))
		}
		return doc.ValidateDef(fx.SchemaDef, v)
	}
}
func fixtures() {
	dir := "tests/contracts/fixtures"
	s, e := os.ReadFile(filepath.Join(dir, "client.protocol.schema.json"))
	if e != nil {
		panic(e)
	}
	d, e := os.ReadFile(filepath.Join(dir, "domain.schema.json"))
	if e != nil {
		panic(e)
	}
	doc, e := domain.LoadSchemaWithExternals(s, map[string][]byte{"domain.schema.json": d})
	if e != nil {
		panic(e)
	}
	raw, e := os.ReadFile(filepath.Join(dir, "client_protocol_v2_fixtures.json"))
	if e != nil {
		panic(e)
	}
	var corpus struct {
		Fixtures []fixture `json:"fixtures"`
	}
	if e = json.Unmarshal(raw, &corpus); e != nil {
		panic(e)
	}
	pos, neg := 0, 0
	for _, fx := range corpus.Fixtures {
		e := validateFixture(doc, fx)
		actual := e == nil
		detail := O{"expected_valid": fx.ExpectedValid, "actual_valid": actual, "schema_definition": fx.SchemaDef}
		if e != nil {
			detail["error"] = e.Error()
		}
		add("fixtures", "FIXTURE/"+fx.Name, actual == fx.ExpectedValid, detail)
		if fx.ExpectedValid {
			pos++
		} else {
			neg++
		}
	}
	add("fixture_metadata", "CORPUS-SHAPE", len(corpus.Fixtures) == 106 && pos == 76 && neg == 30, O{"total": len(corpus.Fixtures), "positive": pos, "negative": neg})
	add("fixture_metadata", "PROTOCOL-INVENTORY", len(doc.Methods) == 23 && len(doc.Events) == 14, O{"methods": len(doc.Methods), "events": len(doc.Events)})
}

// Resolve every $ref against the registered local JSON resources, including
// non-schema OpenAPI refs; no network loader and no silent unknown reference.
func localRefs(docs map[string]O) []string {
	failures := []string{}
	var walk func(any, string)
	walk = func(v any, current string) {
		switch x := v.(type) {
		case map[string]any:
			if ref, ok := x["$ref"].(string); ok {
				parts := strings.SplitN(ref, "#", 2)
				file := parts[0]
				if file == "" {
					file = current
				}
				file = strings.TrimPrefix(file, "./")
				target, ok := docs[file]
				if !ok || len(parts) != 2 || !strings.HasPrefix(parts[1], "/") {
					failures = append(failures, current+":"+ref)
				} else {
					var node any = target
					for _, p := range strings.Split(strings.TrimPrefix(parts[1], "/"), "/") {
						p = strings.ReplaceAll(strings.ReplaceAll(p, "~1", "/"), "~0", "~")
						m, valid := node.(map[string]any)
						if !valid {
							node = nil
							break
						}
						node = m[p]
					}
					if node == nil {
						failures = append(failures, current+":"+ref)
					}
				}
			}
			for _, v := range x {
				walk(v, current)
			}
		case []any:
			for _, v := range x {
				walk(v, current)
			}
		}
	}
	for name, d := range docs {
		walk(d, name)
	}
	sort.Strings(failures)
	return failures
}
func schemaProbes(spec string) {
	frozen := read(filepath.Join(spec, "domain.schema.json"))
	openapi := read(filepath.Join(spec, "openapi.json"))
	old := read("spec/v2.0/contracts/domain.schema.json")
	embedded := read("internal/api/contracts/domain.schema.json")
	overlay := read("internal/domain/contracts/evaluation-v24.schema.json")
	current, e := domain.LoadContracts(spec)
	add("projection", "CURRENT-SCHEMA-COMPILE", e == nil, fmt.Sprint(e))
	if e != nil {
		return
	}
	runtime, e := domain.LoadContracts("spec/v2.0/contracts")
	add("projection", "RUNTIME-SCHEMA-LOAD", e == nil, fmt.Sprint(e))
	if e != nil {
		return
	}
	refs := localRefs(map[string]O{"domain.schema.json": frozen, "openapi.json": openapi})
	add("projection", "CURRENT-LOCAL-REFS", len(refs) == 0, refs)
	add("projection", "RUNTIME-ENTITY-PROJECTION", reflect.DeepEqual(keys(current.Entities), keys(runtime.Entities)), O{"current": keys(current.Entities), "runtime": keys(runtime.Entities)})
	byID := map[string]domain.Operation{}
	for _, op := range runtime.Operations {
		byID[op.ID] = op
	}
	mismatches := []string{}
	for _, op := range current.Operations {
		if old, ok := byID[op.ID]; !ok || !reflect.DeepEqual(old, op) {
			mismatches = append(mismatches, op.ID)
		}
	}
	sort.Strings(mismatches)
	add("projection", "RUNTIME-OPERATION-PROJECTION", len(mismatches) == 0 && len(current.Operations) == len(runtime.Operations), O{"current_count": len(current.Operations), "runtime_count": len(runtime.Operations), "mismatches": mismatches})
	changed := []string{}
	defs := obj(frozen["$defs"])
	runtimeDefs := obj(old["$defs"])
	for name, v := range defs {
		actual := runtimeDefs[name]
		if name == "EvaluationReport" {
			actual = obj(overlay["$defs"])[name]
		}
		if !same(v, actual) {
			changed = append(changed, name)
		}
	}
	sort.Strings(changed)
	add("projection", "RUNTIME-DEFINITION-PROJECTION", len(changed) == 0, O{"missing_or_different_definitions": changed, "evaluation_report_overlay": "internal/domain/contracts/evaluation-v24.schema.json"})
	add("projection", "API-EMBEDDED-SCHEMA-EXACT", same(frozen, embedded), O{"current_hash": domain.Hash(frozen), "embedded_hash": domain.Hash(embedded)})
	_, e = api.ClientProtocolDocument()
	add("projection", "API-SCHEMA-LOAD", e == nil, fmt.Sprint(e))
	diffs := []string{}
	for name, v := range obj(overlay["$defs"]) {
		if !same(v, defs[name]) {
			diffs = append(diffs, name)
		}
	}
	sort.Strings(diffs)
	add("projection", "EVALUATION-OVERLAY-EXACT", len(diffs) == 0, diffs)
	required := strings.Fields("ProjectState Goal Task Run Artifact Evidence Experiment DecisionReceipt AcceptanceReceipt ResourceRequest")
	missing := []string{}
	for _, name := range required {
		if !current.Entities[name] {
			missing = append(missing, name)
		}
	}
	counts := map[string]int{}
	for _, v := range frozen["oneOf"].([]any) {
		counts[domain.Str(obj(v), "$ref")]++
	}
	unique := true
	for _, n := range counts {
		if n != 1 {
			unique = false
		}
	}
	add("aggregate", "CORE-AGGREGATES-UNIQUE", len(missing) == 0 && unique && counts["#/$defs/ProjectState"] == 1, O{"missing": missing, "entity_count": len(counts), "project_state_count": counts["#/$defs/ProjectState"]})
	add("aggregate", "NO-EVALUATION-SCHEDULING-ENTITY", !current.Entities["EvaluationReport"] && !current.Entities["EvaluationSummary"], keys(current.Entities))
	add("aggregate", "STATE-ENUMS-UNCHANGED", same(defs["TaskStatus"], runtimeDefs["TaskStatus"]) && same(defs["AcceptanceReceipt"], runtimeDefs["AcceptanceReceipt"]), O{"TaskStatus": defs["TaskStatus"], "acceptance_receipt_equal": same(defs["AcceptanceReceipt"], runtimeDefs["AcceptanceReceipt"])})
	ac := obj(obj(defs["AcceptanceContract"])["properties"])
	add("aggregate", "ACCEPTANCE-INDEPENDENT-EXACT", obj(ac["require_independent_verifier"])["const"] == true && obj(ac["version_policy"])["const"] == "EXACT", ac)
	art := obj(obj(defs["Artifact"])["properties"])
	add("aggregate", "ARTIFACT-ACCESS-FIELD", art["access_class"] != nil && same(defs["Artifact"], runtimeDefs["Artifact"]), art["access_class"])
	binding := O{"route": "MU_FORK", "upstream_project_id": nil, "upstream_goal_id": nil, "upstream_task_id": nil}
	e = runtime.Validate("ProjectBinding", binding)
	fe := current.Validate("ProjectBinding", binding)
	add("aggregate", "CURRENT-PROJECT-BINDING", e == nil && fe == nil, O{"runtime_error": fmt.Sprint(e), "current_error": fmt.Sprint(fe), "input": binding})
	h := domain.Digest([]byte("w03-development-only"))
	countsV := O{"expected_count": 1, "observed_count": 1, "pass_count": 1, "fail_count": 0, "error_count": 0, "abstain_count": 0, "missing_count": 0, "duplicate_count": 0}
	summary := O{"schema_version": "2.4.0", "project_id": "p", "experiment_id": "e", "run_id": "r", "report_artifact_ref": O{"entity_type": "Artifact", "id": "a", "revision": 1, "content_hash": h}, "dataset_split": "DEVELOPMENT", "counts": countsV, "dataset_hash": h, "candidate_hash": h, "baseline_hash": h, "rubric_hash": h, "integrity_status": "COMPLETE", "duration_ms": 0, "cost": nil, "limitations": []any{}, "created_at": "2026-10-06T00:00:00Z"}
	e = runtime.Validate("EvaluationSummary", summary)
	fe = current.Validate("EvaluationSummary", summary)
	add("aggregate", "CURRENT-EVALUATION-SUMMARY", e == nil && fe == nil, O{"runtime_error": fmt.Sprint(e), "current_error": fmt.Sprint(fe), "input": summary})
}
func scalarProbes(spec string) {
	runtime, e := domain.LoadContracts("spec/v2.0/contracts")
	if e != nil {
		panic(e)
	}
	current, e := domain.LoadContracts(spec)
	if e != nil {
		panic(e)
	}
	cases := []struct {
		id, name string
		value    any
		valid    bool
	}{
		{"MONEY-DECIMAL", "Money", O{"amount": "12.500000000000000001", "currency": "USD"}, true},
		{"MONEY-NUMERIC-REJECT", "Money", O{"amount": 12.5, "currency": "USD"}, false},
		{"MONEY-EXPONENT-REJECT", "Money", O{"amount": "1e3", "currency": "USD"}, false},
		{"MONEY-NEGATIVE-REJECT", "Money", O{"amount": "-1", "currency": "USD"}, false},
		{"MONEY-LEADING-ZERO-REJECT", "Money", O{"amount": "01", "currency": "USD"}, false},
		{"UTC-POSITIVE", "UtcTime", "2026-10-06T00:00:00Z", true},
		{"UTC-OFFSET-REJECT", "UtcTime", "2026-10-06T08:00:00+08:00", false},
		{"UTC-NAIVE-REJECT", "UtcTime", "2026-10-06T00:00:00", false},
		{"UTC-CALENDAR-REJECT", "UtcTime", "2026-02-30T00:00:00Z", false},
	}
	budget := O{"id": "budget", "project_id": nil, "revision": 1, "created_at": "2026-10-06T00:00:00Z", "updated_at": "2026-10-06T00:00:00Z", "scope_type": "GLOBAL", "scope_id": "global", "parent_policy_id": nil, "mode": "UNLIMITED_AMOUNT", "cap": nil, "enforcement": "ACCOUNTING_ONLY", "period": "LIFETIME", "timezone": "Asia/Shanghai", "effective_from": "2026-10-06T00:00:00Z", "unknown_cost_action": "ALLOW_AND_RECORD"}
	cases = append(cases, struct {
		id, name string
		value    any
		valid    bool
	}{"UNLIMITED-NULL", "BudgetPolicy", clone(budget), true})
	budget["cap"] = O{"amount": "0", "currency": "USD"}
	cases = append(cases, struct {
		id, name string
		value    any
		valid    bool
	}{"UNLIMITED-NONNULL-REJECT", "BudgetPolicy", clone(budget), false})
	budget["mode"] = "CAPPED"
	budget["enforcement"] = "ESTIMATED"
	budget["cap"] = nil
	cases = append(cases, struct {
		id, name string
		value    any
		valid    bool
	}{"CAPPED-NULL-REJECT", "BudgetPolicy", clone(budget), false})
	for _, c := range cases {
		a, b := runtime.Validate(c.name, c.value), current.Validate(c.name, c.value)
		add("types", c.id, (a == nil) == c.valid && (b == nil) == c.valid, O{"expected_valid": c.valid, "runtime_error": fmt.Sprint(a), "current_error": fmt.Sprint(b), "input": c.value})
	}
	h := domain.Digest([]byte("w03-fixture"))
	ref := O{"entity_type": "Artifact", "id": "artifact", "revision": 1, "content_hash": h}
	add("bindings", "VERSION-REF-POSITIVE", runtime.Validate("VersionRef", ref) == nil && current.Validate("VersionRef", ref) == nil, ref)
	invalid := clone(ref)
	invalid["revision"] = 0
	add("bindings", "VERSION-REF-ZERO-REJECT", runtime.Validate("VersionRef", invalid) != nil && current.Validate("VersionRef", invalid) != nil, invalid)
	invalid = clone(ref)
	delete(invalid, "content_hash")
	add("bindings", "VERSION-REF-HASH-REQUIRED", runtime.Validate("VersionRef", invalid) != nil && current.Validate("VersionRef", invalid) != nil, invalid)
	checkV := O{"check_id": "development-fixture", "status": "PASS", "evidence_refs": []any{ref}, "command_key": "test.domain", "actual": "synthetic hash boundary only", "exit_code": 0, "started_at": "2026-10-06T00:00:00Z", "finished_at": "2026-10-06T00:00:00Z"}
	receipt := O{"id": "receipt", "project_id": "p", "revision": 1, "created_at": "2026-10-06T00:00:00Z", "receipt_hash": h, "subject_ref": O{"entity_type": "Task", "id": "task", "revision": 2, "content_hash": nil}, "run_id": "r", "contract_hash": h, "input_refs": []any{ref}, "artifact_refs": []any{ref}, "checks": []any{checkV}, "verdict": "PASS", "verifier_principal_id": "verifier", "executor_principal_ids": []any{"executor"}, "independence_basis": "SEPARATE_PRINCIPAL_AND_RUN", "blocking_conflict_ids": []any{}, "qualification_ids": []any{}, "policy_revision": 1, "measurement_mode": "FIXTURE", "reason": "schema and hash probe; no actual acceptance"}
	receipt["receipt_hash"] = domain.Receipt(receipt)
	add("bindings", "RECEIPT-SHAPE-POSITIVE", runtime.Validate("AcceptanceReceipt", receipt) == nil && current.Validate("AcceptanceReceipt", receipt) == nil, receipt)
	invalid = clone(receipt)
	invalid["revision"] = 2
	add("bindings", "RECEIPT-REVISION-IMMUTABLE", runtime.Validate("AcceptanceReceipt", invalid) != nil && current.Validate("AcceptanceReceipt", invalid) != nil, invalid["revision"])
	for _, field := range []string{"input_refs", "artifact_refs"} {
		for _, part := range []string{"revision", "content_hash"} {
			mutated := clone(receipt)
			r := obj(mutated[field].([]any)[0])
			if part == "revision" {
				r[part] = 2
			} else {
				r[part] = domain.Digest([]byte("mutated"))
			}
			add("bindings", "RECEIPT-BINDS-"+field+"-"+part, domain.Receipt(mutated) != receipt["receipt_hash"], O{"before": receipt["receipt_hash"], "after": domain.Receipt(mutated)})
		}
	}
	contract := O{"contract_hash": h, "contract_revision": 1, "checks": []any{O{"check_id": "rubric-check", "kind": "MODEL_RUBRIC", "required": true, "expected": "bound rubric", "command_key": nil, "rubric_ref": ref, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": "2026-10-06T00:00:00Z"}
	add("bindings", "RUBRIC-CONTRACT-SHAPE", runtime.Validate("AcceptanceContract", contract) == nil && current.Validate("AcceptanceContract", contract) == nil, contract)
	// Rubric binds through contract_hash, not an invented top-level receipt field.
	before := domain.Hash(contract)
	mutated := clone(contract)
	obj(obj(mutated["checks"].([]any)[0])["rubric_ref"])["revision"] = 2
	after := domain.Hash(mutated)
	r2 := clone(receipt)
	r2["contract_hash"] = after
	r1 := clone(receipt)
	r1["contract_hash"] = before
	add("bindings", "RECEIPT-BINDS-RUBRIC-VIA-CONTRACT", before != after && domain.Receipt(r1) != domain.Receipt(r2), O{"contract_before": before, "contract_after": after})
	r2 = clone(receipt)
	r2["receipt_hash"] = "ignored"
	add("bindings", "RECEIPT-SELF-HASH-EXCLUDED", domain.Receipt(r2) == receipt["receipt_hash"], nil)
	a := O{"id": "artifact", "revision": 1, "content_hash": h}
	r := domain.Ref(a, "Artifact")
	add("bindings", "ARTIFACT-REF-EXACT", same(r, ref), r)
	r = domain.Ref(receipt, "AcceptanceReceipt")
	add("bindings", "ACCEPTANCE-REF-EXACT", r["content_hash"] == receipt["receipt_hash"] && r["revision"] == receipt["revision"], r)
}
func main() {
	gate := flag.String("check", "", "exact gate")
	spec := flag.String("spec", "", "frozen contract directory")
	flag.Parse()
	code := 0
	defer func() {
		if v := recover(); v != nil {
			add("fatal", "PROBE-ERROR", false, fmt.Sprint(v))
			code = 1
		}
		for _, c := range checks {
			if !c.Passed {
				code = 1
			}
		}
		status := "PASS"
		if code != 0 || len(checks) == 0 {
			status = "FAIL"
			code = 1
		}
		json.NewEncoder(os.Stdout).Encode(O{"status": status, "check_id": *gate, "checks": checks, "formal_product_acceptance": "NOT_RUN", "owned_acceptance_ids": []any{}})
		os.Exit(code)
	}()
	switch *gate {
	case "W03-G01":
		schemaProbes(*spec)
		fixtures()
	case "W03-G03":
		scalarProbes(*spec)
	default:
		panic("unsupported exact gate")
	}
}
