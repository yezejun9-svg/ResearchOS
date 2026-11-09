package domain

import (
	"encoding/json"
	"strings"
	"testing"
)

func captureTestView() RuntimeCodingCaptureView {
	h := func(s string) string { return Digest([]byte(s)) }
	return RuntimeCodingCaptureView{Schema: runtimeToolCaptureSchema, ProjectID: "fixture-project", TaskID: "fixture-task", RunID: "fixture-run", LeaseEpoch: "9223372036854775807", CheckID: "fixture-check", SuiteRef: "coding.pure-scalar-bundle-v1", SuiteHash: h("suite"), BindingHash: h("binding"), TaskContractHash: h("task"), GoalContractHash: h("goal"), PolicyHash: h("policy"), ToolchainHash: h("toolchain"), GoModHash: h("mod"), TestHash: h("test")}
}
func TestRuntimeToolCaptureJSONCannotOptIn(t *testing.T) {
	for _, key := range []string{"codingCapture", "CodingCapture", "coding_capture", "capture", "context", "runtimeToolCaptureContext"} {
		t.Run(key, func(t *testing.T) {
			raw, _ := json.Marshal(map[string]any{key: captureTestView(), "Name": "run_check", "Arguments": Object{"check_id": "coding.pure-scalar-bundle-v1"}, "Policy": Object{"capture": true}})
			var r RuntimeToolRequest
			if err := json.Unmarshal(raw, &r); err != nil {
				t.Fatal(err)
			}
			if v, err := r.CodingCapture(); v != nil || err != nil {
				t.Fatal("JSON minted private carrier", err)
			}
		})
	}
}
func TestRuntimeToolCapturePrivateView(t *testing.T) {
	if v, e := (RuntimeToolRequest{}).CodingCapture(); v != nil || e != nil {
		t.Fatal("nil compatibility")
	}
	original := captureTestView()
	r := RuntimeToolRequest{codingCapture: &runtimeToolCaptureContext{view: original}}
	first, err := r.CodingCapture()
	if err != nil || *first != original {
		t.Fatal(err)
	}
	first.CheckID = "mutated"
	first.BindingHash = "bad"
	again, err := r.CodingCapture()
	if err != nil || *again != original || again.LeaseEpoch != "9223372036854775807" {
		t.Fatal("view aliases or loses epoch", err)
	}
}
func TestRuntimeToolCaptureInvalidNeverFallsBack(t *testing.T) {
	cases := map[string]func(*RuntimeCodingCaptureView){
		"schema":         func(v *RuntimeCodingCaptureView) { v.Schema = "unknown" },
		"suite":          func(v *RuntimeCodingCaptureView) { v.SuiteRef = "unknown" },
		"project":        func(v *RuntimeCodingCaptureView) { v.ProjectID = "" },
		"task":           func(v *RuntimeCodingCaptureView) { v.TaskID = "" },
		"run":            func(v *RuntimeCodingCaptureView) { v.RunID = "" },
		"check":          func(v *RuntimeCodingCaptureView) { v.CheckID = "" },
		"utf8":           func(v *RuntimeCodingCaptureView) { v.TaskID = string([]byte{255}) },
		"nul":            func(v *RuntimeCodingCaptureView) { v.CheckID = "a\x00b" },
		"size":           func(v *RuntimeCodingCaptureView) { v.RunID = strings.Repeat("x", 257) },
		"zero_epoch":     func(v *RuntimeCodingCaptureView) { v.LeaseEpoch = "0" },
		"negative_epoch": func(v *RuntimeCodingCaptureView) { v.LeaseEpoch = "-1" },
		"alias_epoch":    func(v *RuntimeCodingCaptureView) { v.LeaseEpoch = "01" },
		"overflow_epoch": func(v *RuntimeCodingCaptureView) { v.LeaseEpoch = "9223372036854775808" },
		"suite_hash":     func(v *RuntimeCodingCaptureView) { v.SuiteHash = "bad" },
		"binding":        func(v *RuntimeCodingCaptureView) { v.BindingHash = "" },
		"task_contract":  func(v *RuntimeCodingCaptureView) { v.TaskContractHash = "bad" },
		"goal_contract":  func(v *RuntimeCodingCaptureView) { v.GoalContractHash = "bad" },
		"policy":         func(v *RuntimeCodingCaptureView) { v.PolicyHash = "bad" },
		"toolchain":      func(v *RuntimeCodingCaptureView) { v.ToolchainHash = "bad" },
		"fixed_mod":      func(v *RuntimeCodingCaptureView) { v.GoModHash = "bad" },
		"fixed_test":     func(v *RuntimeCodingCaptureView) { v.TestHash = "bad" },
		"same_contract":  func(v *RuntimeCodingCaptureView) { v.GoalContractHash = v.TaskContractHash },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			v := captureTestView()
			change(&v)
			r := RuntimeToolRequest{codingCapture: &runtimeToolCaptureContext{view: v}}
			if got, err := r.CodingCapture(); err == nil || got != nil {
				t.Fatal("invalid downgraded")
			}
		})
	}
	if _, err := (RuntimeToolRequest{codingCapture: &runtimeToolCaptureContext{}}).CodingCapture(); err == nil {
		t.Fatal("zero carrier")
	}
}

// Independent predicates only: no producer or sandbox call is added.
func TestIndependentCaptureCarrierCanonicalEpochAndNoWireAuthority(t *testing.T) {
    for _, raw := range []string{
        `{"codingCapture":{"view":{"Schema":"researchos.coding-private-capture-context.v1"}},"Name":"run_check"}`,
        `{"coding\u0043apture":{"view":{}},"Policy":{"capture":true},"IntentKey":"coding.pure-scalar-bundle-v1"}`,
        `{"CodingCapture":null,"Arguments":{"check_id":"coding.pure-scalar-bundle-v1"}}`,
    } { t.Run("wire-"+Digest([]byte(raw))[7:15],func(t *testing.T){
        var request RuntimeToolRequest
        if err:=json.Unmarshal([]byte(raw),&request);err!=nil {t.Fatal(err)}
        if view,err:=request.CodingCapture();view!=nil||err!=nil {t.Fatal("wire minted context")}
    }) }
    for _, epoch:=range []string{"+1"," 1","1 ","1.0","1e0"} {t.Run("epoch-"+Digest([]byte(epoch))[7:15],func(t *testing.T){
        view:=captureTestView();view.LeaseEpoch=epoch
        request:=RuntimeToolRequest{codingCapture:&runtimeToolCaptureContext{view:view}}
        if got,err:=request.CodingCapture();got!=nil||err==nil {t.Fatal("noncanonical epoch accepted")}
    })}
    view:=captureTestView();view.LeaseEpoch="9007199254740993"
    request:=RuntimeToolRequest{codingCapture:&runtimeToolCaptureContext{view:view}}
    first,err:=request.CodingCapture();if err!=nil {t.Fatal(err)}
    first.LeaseEpoch="9007199254740992";first.ProjectID="changed";first.GoModHash="changed"
    again,err:=request.CodingCapture();if err!=nil||*again!=view {t.Fatal("copied scalar context changed",err)}
}
