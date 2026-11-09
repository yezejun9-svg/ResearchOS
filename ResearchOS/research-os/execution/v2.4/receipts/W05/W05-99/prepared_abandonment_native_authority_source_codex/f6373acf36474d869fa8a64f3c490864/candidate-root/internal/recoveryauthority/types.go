// Package recoveryauthority authenticates one local historical-evidence adoption.
// Its exported data types are evidence, never capabilities. Only OS-validated
// native bootstrap can produce a nonzero Token.
package recoveryauthority

import (
    "bytes"
    "crypto/ed25519"
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "errors"
    "fmt"
    "io"
    "sync"
    "time"
)

const Purpose = "RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1"
const Schema = "researchos.historical-evidence-adoption.v1"
// Empty until a NEW independently accepted Source revision pins a freshly
// provisioned purpose-specific issuer. No command, environment or JSON setter.
const enrolledIssuerPublicKeyHex = ""

type RawPin struct {
    Role string `json:"role"`
    Path string `json:"path"`
    SHA256 string `json:"sha256"`
    Bytes int64 `json:"bytes"`
}
type ProcessIdentity struct {
    PID uint32 `json:"pid"`
    Birth100ns string `json:"birth_100ns"`
    Image RawPin `json:"image"`
    SID string `json:"sid"`
}
type Tuple struct {
    ProjectID string `json:"project_id"`
    TaskID string `json:"task_id"`
    RunID string `json:"run_id"`
    RuntimeID string `json:"runtime_id"`
    OwnerRoot string `json:"owner_root"`
    Epoch int64 `json:"epoch"`
    RunRevision int64 `json:"run_revision"`
    TaskRevision int64 `json:"task_revision"`
    DispatchKey string `json:"dispatch_key"`
    ManifestHash string `json:"manifest_hash"`
}
type HistoricalObserver struct {
    OwnerPID uint32 `json:"owner_pid"`
    HostPID uint32 `json:"host_pid"`
    HostBirth100ns string `json:"host_birth_100ns"`
    HostJobID string `json:"host_job_id"`
    RunUUID string `json:"run_uuid"`
    ClosedObservedMonotonic string `json:"closed_observed_monotonic"`
    OriginalRootSignature *string `json:"original_root_signature"`
    ExactJobClosedUTC *string `json:"exact_job_closed_utc"`
}
type Adoption struct {
    Schema string `json:"schema"`
    Kind string `json:"kind"`
    Purpose string `json:"purpose"`
    ReleaseID string `json:"release_id"`
    GrantSHA256 string `json:"grant_sha256"`
    Tuple Tuple `json:"tuple"`
    Root string `json:"root"`
    RootIdentity string `json:"root_identity"`
    Database string `json:"database"`
    DatabaseIdentity string `json:"database_identity"`
    Producer ProcessIdentity `json:"producer"`
    Maintenance ProcessIdentity `json:"maintenance"`
    SignedUTC string `json:"signed_utc"`
    ExpiresUTC string `json:"expires_utc"`
    Nonce string `json:"nonce"`
    Historical HistoricalObserver `json:"historical"`
    RootStartedUTC string `json:"root_started_utc"`
    RootClockExpiredUTC string `json:"root_clock_expired_utc"`
    Pins []RawPin `json:"pins"`
    ProviderRequests *int64 `json:"provider_requests"`
    ActualCost *string `json:"actual_cost"`
    FinancialClosed bool `json:"financial_closed"`
    // This is authorization for exact CAS, not an assertion it already passed.
    StateVerification string `json:"state_verification"`
    Signature string `json:"signature"`
}
type Release struct {
    Schema string `json:"schema"`
    Purpose string `json:"purpose"`
    ID string `json:"id"`
    SID string `json:"sid"`
    RootImage RawPin `json:"root_image"`
    ControlImage RawPin `json:"control_image"`
    SourceRoot string `json:"source_root"`
    SourceFiles []RawPin `json:"source_files"`
    RootSigningPublicKey string `json:"root_signing_public_key"`
    NotBeforeUTC string `json:"not_before_utc"`
    ExpiresUTC string `json:"expires_utc"`
}
type Grant struct {
    Schema string `json:"schema"`
    Purpose string `json:"purpose"`
    ReleaseSHA256 string `json:"release_sha256"`
    Nonce string `json:"nonce"`
    IssuedUTC string `json:"issued_utc"`
    ExpiresUTC string `json:"expires_utc"`
    Root string `json:"root"`
    RootIdentity string `json:"root_identity"`
    Database string `json:"database"`
    DatabaseIdentity string `json:"database_identity"`
    Tuple Tuple `json:"tuple"`
    Pins []RawPin `json:"pins"`
}
type signedDocument struct {
    Payload json.RawMessage `json:"payload"`
    Signature string `json:"signature"`
}
func digest(b []byte) string { h := sha256.Sum256(b); return "sha256:"+hex.EncodeToString(h[:]) }
func hexNonce(s string) ([]byte,error) { return hex.DecodeString(s) }
func encoded(v any) []byte { b, _ := json.Marshal(v); return b }
func strict(raw []byte, v any) error {
    d := json.NewDecoder(bytes.NewReader(raw)); d.DisallowUnknownFields(); d.UseNumber()
    if err := d.Decode(v); err != nil { return err }
    if err := d.Decode(new(any)); err != io.EOF { return errors.New("AUTHORITY_TRAILING_JSON") }
    return nil
}
func publicKey(s string) (ed25519.PublicKey,error) {
    b,e := hex.DecodeString(s); if e != nil || len(b)!=ed25519.PublicKeySize { return nil,errors.New("AUTHORITY_UNENROLLED_KEY") }; return ed25519.PublicKey(b),nil
}
func verifyDocument(raw []byte, purpose string, target any) error {
    key,err := publicKey(enrolledIssuerPublicKeyHex); if err != nil { return err }
    var d signedDocument
    if err = strict(raw,&d); err != nil { return err }
    signature,err := hex.DecodeString(d.Signature)
    if err != nil || !ed25519.Verify(key,append([]byte(purpose+"\x00"),d.Payload...),signature) { return errors.New("AUTHORITY_ISSUER_SIGNATURE") }
    return strict(d.Payload,target)
}
func validInterval(start,end string,now time.Time,max time.Duration) bool {
    a,ae := time.Parse(time.RFC3339Nano,start); b,be := time.Parse(time.RFC3339Nano,end)
    return ae==nil && be==nil && !now.Before(a) && now.Before(b) && b.After(a) && (max==0 || b.Sub(a)<=max)
}
func releaseCoversGrant(r Release,expires string) bool {
    releaseEnd,re:=time.Parse(time.RFC3339Nano,r.ExpiresUTC); grantEnd,ge:=time.Parse(time.RFC3339Nano,expires)
    return re==nil && ge==nil && !grantEnd.After(releaseEnd)
}
func validTuple(t Tuple) bool {
    return t.ProjectID!="" && t.TaskID!="" && t.RunID!="" && t.RuntimeID!="" && t.OwnerRoot!="" && t.DispatchKey!="" && t.Epoch>0 && t.RunRevision>0 && t.TaskRevision>0 && validHash(t.ManifestHash)
}
func validHash(s string) bool { if len(s)!=71 || s[:7]!="sha256:" { return false }; b,e:=hex.DecodeString(s[7:]); return e==nil && len(b)==32 }
func ValidateAdoption(a Adoption) error {
    if a.Schema!=Schema || a.Kind!="HISTORICAL_EVIDENCE_ADOPTION" || a.Purpose!=Purpose || !validTuple(a.Tuple) || a.ReleaseID=="" || !validHash(a.GrantSHA256) || !validInterval(a.SignedUTC,a.ExpiresUTC,time.Now(),5*time.Minute) || len(a.Nonce)!=64 || a.StateVerification!="REQUIRE_CURRENT_OWNER_AND_EXACT_CAS" { return errors.New("AUTHORITY_ADOPTION_BINDING") }
    if a.Historical.OriginalRootSignature!=nil || a.Historical.ExactJobClosedUTC!=nil || a.ProviderRequests!=nil || a.ActualCost!=nil || a.FinancialClosed { return errors.New("AUTHORITY_HISTORICAL_UNKNOWN_MUST_STAY_NULL") }
    if a.Historical.OwnerPID==0 || a.Historical.HostPID==0 || a.Historical.HostBirth100ns=="" || a.Historical.HostJobID=="" || a.Historical.RunUUID=="" || a.Historical.ClosedObservedMonotonic=="" || a.Producer.PID==0 || a.Producer.Birth100ns=="" || a.Maintenance.PID==0 || a.Maintenance.Birth100ns=="" { return errors.New("AUTHORITY_OBSERVER_IDENTITY") }
    started,err:=time.Parse(time.RFC3339Nano,a.RootStartedUTC); end,ee:=time.Parse(time.RFC3339Nano,a.RootClockExpiredUTC)
    if err!=nil || ee!=nil || !end.Equal(started.Add(300*time.Second)) || time.Now().Before(end) { return errors.New("AUTHORITY_ORIGINAL_CLOCK") }
    return nil
}
func verifyAdoption(a Adoption,r Release,g Grant,grantRaw []byte) error {
    if err:=ValidateAdoption(a); err!=nil { return err }
    if a.ReleaseID!=r.ID || a.GrantSHA256!=digest(grantRaw) || !bytes.Equal(encoded(a.Tuple),encoded(g.Tuple)) || a.Nonce!=g.Nonce || a.ExpiresUTC!=g.ExpiresUTC || a.Root!=g.Root || a.Database!=g.Database || a.RootIdentity!=g.RootIdentity || a.DatabaseIdentity!=g.DatabaseIdentity || !bytes.Equal(encoded(a.Pins),encoded(g.Pins)) { return errors.New("AUTHORITY_SIGNED_GRANT_BINDING") }
    key,err:=publicKey(r.RootSigningPublicKey); if err!=nil { return err }
    sig,err:=hex.DecodeString(a.Signature); a.Signature=""
    if err!=nil || !ed25519.Verify(key,append([]byte(Purpose+"/adoption\x00"),encoded(a)...),sig) { return errors.New("AUTHORITY_ADOPTION_SIGNATURE") }
    return nil
}

// Token deliberately has no exported fields, serialization or arbitrary-key
// constructor. Copies share one state. A zero value rejects all operations.
type Token struct { state *tokenState }
type tokenState struct {
    mu sync.Mutex
    adoption Adoption
    native *nativeSession
    proof string
    phase string
}
func (t Token) Adoption() (Adoption,error) {
    if t.state==nil { return Adoption{},errors.New("AUTHORITY_ZERO_TOKEN") }
    t.state.mu.Lock(); defer t.state.mu.Unlock()
    var a Adoption; err:=strict(encoded(t.state.adoption),&a); return a,err
}
func (t Token) Check(root,database,proof string) error {
    if t.state==nil { return errors.New("AUTHORITY_ZERO_TOKEN") }
    s:=t.state; s.mu.Lock(); defer s.mu.Unlock()
    if s.phase=="CLOSED" || s.native==nil || root!=s.adoption.Root || database!=s.adoption.Database || !validHash(proof) || (s.proof!="" && proof!=s.proof) { return errors.New("AUTHORITY_TOKEN_BINDING") }
    if err:=ValidateAdoption(s.adoption); err!=nil { return err }
    return s.native.check()
}
func (t Token) Begin(proof string) error {
    if t.state==nil { return errors.New("AUTHORITY_ZERO_TOKEN") }
    s:=t.state; s.mu.Lock(); defer s.mu.Unlock()
    if s.phase!="READY" || !validHash(proof) || (s.proof!="" && s.proof!=proof) { return errors.New("AUTHORITY_ONE_USE") }
    if err:=s.native.check(); err!=nil { return err }
    s.proof=proof; s.phase="INFLIGHT"; return nil
}
func (t Token) Finish(committed bool) {
    if t.state==nil { return }; s:=t.state; s.mu.Lock(); defer s.mu.Unlock()
    if s.phase=="INFLIGHT" { if committed { s.phase="COMMITTED" } else { s.phase="READY" } }
}
func (t Token) Close() error {
    if t.state==nil { return nil }; s:=t.state; s.mu.Lock(); defer s.mu.Unlock()
    if s.phase=="INFLIGHT" { return fmt.Errorf("AUTHORITY_TRANSACTION_INFLIGHT") }
    if s.phase=="CLOSED" { return nil }; s.phase="CLOSED"; return s.native.close()
}
