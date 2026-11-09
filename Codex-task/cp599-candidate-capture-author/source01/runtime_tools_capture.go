package domain

import (
 "fmt"
 "strconv"
 "strings"
 "unicode/utf8"
)

const runtimeToolCaptureSchema = "researchos.coding-private-capture-context.v1"

// RuntimeCodingCaptureView is provenance, not authority. Decoding this value
// cannot opt a request in. There is no production producer in this slice.
type RuntimeCodingCaptureView struct {
 Schema string `json:"schema"`
 ProjectID string `json:"project_id"`
 TaskID string `json:"task_id"`
 RunID string `json:"run_id"`
 LeaseEpoch string `json:"lease_epoch"`
 CheckID string `json:"check_id"`
 SuiteRef string `json:"suite_ref"`
 SuiteHash string `json:"suite_hash"`
 BindingHash string `json:"binding_hash"`
 TaskContractHash string `json:"task_contract_hash"`
 GoalContractHash string `json:"goal_contract_hash"`
 PolicyHash string `json:"policy_hash"`
 ToolchainHash string `json:"toolchain_hash"`
 GoModHash string `json:"go_mod_hash"`
 TestHash string `json:"test_hash"`
}

// ValidateShape checks integrity only. Candidate content is deliberately absent:
// the current check's Host staging manifest, after editing, freezes its bytes.
func (v RuntimeCodingCaptureView) ValidateShape() error {
 bad:=func()error{return fmt.Errorf("CODING_CAPTURE_CONTEXT_INVALID")}
 if v.Schema!=runtimeToolCaptureSchema || v.SuiteRef!="coding.pure-scalar-bundle-v1" {return bad()}
 for _,s:=range []string{v.ProjectID,v.TaskID,v.RunID,v.CheckID} {
  if len(s)>256 || !utf8.ValidString(s) || strings.TrimSpace(s)=="" || strings.ContainsRune(s,0) {return bad()}
 }
 n,err:=strconv.ParseInt(v.LeaseEpoch,10,64)
 if err!=nil || n<=0 || strconv.FormatInt(n,10)!=v.LeaseEpoch {return bad()}
 for _,h:=range []string{v.SuiteHash,v.BindingHash,v.TaskContractHash,v.GoalContractHash,v.PolicyHash,v.ToolchainHash,v.GoModHash,v.TestHash} {
  if !codingDeliveryHash(h) {return bad()}
 }
 if v.TaskContractHash==v.GoalContractHash {return bad()}
 return nil
}

// Only a future domain factory, after real binding/authority/origin/plan checks,
// may fill this private concrete carrier. No JSON, policy marker, exported
// setter or context.WithValue bridge mints it.
type runtimeToolCaptureContext struct {view RuntimeCodingCaptureView}

// CodingCapture returns nil only for an ordinary request. Malformed nonnil
// never falls back. Scalar-only views are copied and cannot mutate the carrier.
func (r RuntimeToolRequest) CodingCapture() (*RuntimeCodingCaptureView,error) {
 if r.codingCapture==nil {return nil,nil}
 v:=r.codingCapture.view
 if err:=v.ValidateShape();err!=nil {return nil,err}
 return &v,nil
}

