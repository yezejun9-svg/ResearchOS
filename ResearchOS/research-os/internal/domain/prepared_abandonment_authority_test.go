package domain

import (
    "context"
    "encoding/json"
    "testing"

    "researchos.local/research-os/internal/recoveryauthority"
)

func TestPreparedNativeAuthorityJSONAndZeroTokenCannotInstall(t *testing.T) {
    var token recoveryauthority.Token
    if err:=json.Unmarshal([]byte(`{"approved":true,"state":{"phase":"READY"}}`),&token); err!=nil { t.Fatal(err) }
    if _,_,err:=newNativePreparedAbandonmentService(context.Background(),nil,"unused",token); err==nil { t.Fatal("JSON or zero value installed a production verifier") }
    service:=&Service{}
    if _,err:=service.AbandonPreparedQualification(context.Background(),"caller token",PreparedRunAbandonmentEvidence{HistoricalAdoption:&recoveryauthority.Adoption{Kind:"HISTORICAL_EVIDENCE_ADOPTION"}}); err==nil { t.Fatal("normal Service accepted self-asserted adoption") }
    if service.preparedAbandonmentAuthority!=nil { t.Fatal("failed call installed authority") }
}
func TestPreparedHistoricalSchemaCannotEraseContemporaneousV1Requirements(t *testing.T) {
    if validatePreparedAbandonmentEvidence(PreparedRunAbandonmentEvidence{Schema:"researchos.prepared-run-abandonment.v1",Outcome:preparedAbandonmentOutcome})==nil { t.Fatal("old v1 accepted missing signature/time") }
    if validatePreparedAbandonmentEvidence(PreparedRunAbandonmentEvidence{Schema:historicalPreparedAbandonmentSchema,HistoricalAdoption:&recoveryauthority.Adoption{},RootWitnessSignature:"pretend-old-root-signed",ParentJobClosedUTC:"2026-10-08T17:01:27Z"})==nil { t.Fatal("historical schema fabricated old facts") }
}
