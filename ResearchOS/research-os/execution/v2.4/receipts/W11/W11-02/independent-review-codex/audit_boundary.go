package main

import (
 "encoding/json"
 "fmt"
 "math"
 "os"
 "slices"
 "researchos.local/research-os/adapters/decision"
)

func base() decision.QualificationAuditInput {
 s := decision.Scope{TaskType:"reuse_selection", Language:"zh", Provider:"typesafe", ModelRevision:"independent-fixture-model", RubricRevision:"independent-fixture-rubric"}
 return decision.QualificationAuditInput{Requested:s, Observed:s, EvidenceMode:"CURRENT_PROTECTED_LIVE", LabelBasis:"OBJECTIVE", IndependentHoldout:true, DisjointSourceFamilies:true, Development:60, Holdout:40, RecordedInvocations:40, Correct:40, NegativeLabels:20, AcceptActions:20, RejectActions:20, LatencyMS:4000, NegativeCoverage:map[string]bool{"license_unknown":true,"platform_mismatch":true,"integration_unavailable":true,"no_benefit":true,"missing_evidence":true,"readme_injection":true,"timeout":true,"abstain":true,"cross_scope_qualification":true}}
}

func main() {
 total, failed := 0, 0
 check := func(id string, ok bool, detail any) {
  total++; status := "PASS"; if !ok {status="FAIL"; failed++}
  raw, _ := json.Marshal(map[string]any{"assertion_id":id,"status":status,"mode":"INDEPENDENT_SYNTHETIC_NUMERICAL_FIXTURE","detail":detail})
  fmt.Println("INDEPENDENT_ASSERTION "+string(raw))
 }
 for _, tc := range []struct{name string; value float64}{{"nan",math.NaN()},{"positive-infinity",math.Inf(1)},{"negative-infinity",math.Inf(-1)}} {
  in:=base(); in.ActualCost=&tc.value; got:=decision.AuditQualification(in); raw, err:=json.Marshal(got)
  check("NONFINITE-JSON-"+tc.name, got.Status=="BLOCKED" && got.ActualCost==nil && err==nil && slices.Contains(got.Reasons,"INVALID_COUNTS_OR_METRICS") && got.AutomaticAuthority=="NONE", map[string]any{"json_encodable":err==nil,"bytes":len(raw),"status":got.Status,"null_cost":got.ActualCost==nil})
 }
 cases:=0; mismatch:=0
 // Independently constructed TP/TN/FP/FN matrices: A08 holdout denominator
 // and this card's disagreement gate must both compare integer counts.
 for fa:=int64(0);fa<=3;fa++ {for fr:=int64(0);fr<=3;fr++ {for abstain:=int64(0);abstain<=3;abstain++ {
  in:=base();in.FalseAccept=fa;in.FalseReject=fr;in.Abstain=abstain
  in.Correct=40-fa-fr-abstain;in.AcceptActions=20-fr+fa-abstain;in.RejectActions=20-fa+fr
  got:=decision.AuditQualification(in);want:="REVIEWABLE";if fa+fr>2 {want="BLOCKED"}
  cases++
  if got.Status!=want || got.AutomaticAuthority!="NONE" || got.MaximumMode!="ADVISORY" || got.DisagreementRate==nil || *got.DisagreementRate!=float64(fa+fr)/40 || got.AbstainRate==nil || *got.AbstainRate!=float64(abstain)/40 {mismatch++}
 }}}
 check("CONFUSION-MATRIX-ORACLE",mismatch==0,map[string]any{"independent_matrices":cases,"mismatches":mismatch})
 for _, tc:=range []struct{name,reason string; change func(*decision.QualificationAuditInput)}{
  {"error-abstain-bound","INVALID_COUNTS_OR_METRICS",func(x *decision.QualificationAuditInput){x.Errors=1}},
  {"negative-count","INVALID_COUNTS_OR_METRICS",func(x *decision.QualificationAuditInput){x.FalseReject=-1}},
  {"counter-cap","INVALID_COUNTS_OR_METRICS",func(x *decision.QualificationAuditInput){x.Development=1000000001}},
  {"negative-latency","INVALID_COUNTS_OR_METRICS",func(x *decision.QualificationAuditInput){x.LatencyMS=-1}},
  {"zero-invocations","INCOMPLETE_REAL_INVOCATIONS",func(x *decision.QualificationAuditInput){x.RecordedInvocations=0}},
  {"one-critical-error","CRITICAL_FALSE_ACCEPT",func(x *decision.QualificationAuditInput){x.Correct=39;x.FalseAccept=1;x.CriticalFalseAccept=1;x.AcceptActions=21;x.RejectActions=19}},
  {"historical-mode","CURRENT_PROTECTED_LIVE_NOT_ESTABLISHED",func(x *decision.QualificationAuditInput){x.EvidenceMode="ARCHIVED_LIVE"}},
  {"traceable-human","",func(x *decision.QualificationAuditInput){x.LabelBasis="HUMAN_TRACEABLE"}},
 } {
  in:=base();tc.change(&in);got:=decision.AuditQualification(in);ok:=got.Status=="BLOCKED" && slices.Contains(got.Reasons,tc.reason);if tc.reason=="" {ok=got.Status=="REVIEWABLE"}
  check("EDGE-"+tc.name,ok && got.AutomaticAuthority=="NONE",got)
 }
 got:=decision.AuditQualification(base());check("UNKNOWN-COST-NO-ZERO",got.ActualCost==nil,got)
 raw,_:=json.Marshal(map[string]any{"assertions":total,"failed":failed,"provider_calls":0,"service_operations":0,"domain_grants":0})
 fmt.Println(string(raw));if failed>0 {os.Exit(1)}
}
