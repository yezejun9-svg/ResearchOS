package host

import (
	"context"
	"crypto/rand"
	"database/sql"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/santhosh-tekuri/jsonschema/v6"

	"researchos.local/research-os/internal/canonical"
	"researchos.local/research-os/internal/domain"
)

const KindNativeClientAttestRequest = "NATIVE_CLIENT_ATTEST_REQUEST"
const KindNativeClientAttestResult = "NATIVE_CLIENT_ATTEST_RESULT"
const nativeCreateWitnessTTL = 60 * time.Second
const nativeCreateWitnessLimit = 256

//go:embed contracts/native.client-attestation.v1.schema.json
var nativeCreateProfile []byte

const nativeCreateProfileDigest = "sha256:1ea23c47c4521b7da82796be432e09f4bb9c1d6e5d0d545692e3579d86256ce5"

type nativeProfileLocalLoader struct{}

func (nativeProfileLocalLoader) Load(string) (any, error) {
	return nil, fmt.Errorf("NATIVE_CREATE_EXTERNAL_SCHEMA_FORBIDDEN")
}

type nativeCreateProfileDocument struct{ schemas map[string]*jsonschema.Schema }

func (d *nativeCreateProfileDocument) ValidateDefInput(name string, value any) error {
	if name != "NativeClientAttestRequestFrame" {
		return fmt.Errorf("NATIVE_CREATE_PROFILE_DIRECTION")
	}
	return d.schemas[name].Validate(value)
}
func (d *nativeCreateProfileDocument) ValidateDef(name string, value any) error {
	if name != "NativeClientAttestResultFrame" {
		return fmt.Errorf("NATIVE_CREATE_PROFILE_DIRECTION")
	}
	return d.schemas[name].Validate(value)
}

var nativeCreateDocument = sync.OnceValues(func() (schemaDocument, error) {
	if domain.Digest(nativeCreateProfile) != nativeCreateProfileDigest {
		return nil, fmt.Errorf("NATIVE_CREATE_PROFILE_DIGEST")
	}
	var value map[string]any
	if json.Unmarshal(nativeCreateProfile, &value) != nil {
		return nil, fmt.Errorf("NATIVE_CREATE_PROFILE_JSON")
	}
	location, ok := value["$id"].(string)
	if !ok {
		return nil, fmt.Errorf("NATIVE_CREATE_PROFILE_ID")
	}
	compiler := jsonschema.NewCompiler()
	compiler.UseLoader(nativeProfileLocalLoader{})
	compiler.AssertFormat()
	compiler.DefaultDraft(jsonschema.Draft2020)
	if err := compiler.AddResource(location, value); err != nil {
		return nil, err
	}
	doc := &nativeCreateProfileDocument{schemas: map[string]*jsonschema.Schema{}}
	for _, name := range []string{"NativeClientAttestRequestFrame", "NativeClientAttestResultFrame"} {
		s, err := compiler.Compile(location + "#/$defs/" + name)
		if err != nil {
			return nil, err
		}
		doc.schemas[name] = s
	}
	return doc, nil
})

type nativeCreateRequest struct {
	SchemaVersion    int64   `json:"schema_version"`
	Credential       string  `json:"credential_value"`
	CommandID        string  `json:"command_id"`
	Method           string  `json:"method"`
	ProjectID        string  `json:"project_id"`
	RawHash          string  `json:"request_raw_sha256"`
	SessionID        *string `json:"session_id"`
	ExpectedRevision *int64  `json:"expected_revision"`
	WriterEpoch      *int64  `json:"writer_epoch"`
}
type nativeCreateWitness struct {
	origin  domain.VerifiedNativeCreateOrigin
	service *domain.ClientService
	store   *sql.DB
}
type nativeCreateState struct {
	mu        sync.Mutex
	service   *domain.ClientService
	witnesses map[string]nativeCreateWitness
}
type nativeCreateVerifier struct {
	host    *Host
	service *domain.ClientService
}

func (h *Host) BindNativeCreateAuthority(service *domain.ClientService) (domain.NativeCreateAuthority, error) {
	if h == nil || h.nativeCreate == nil || service == nil || service.Domain == nil || service.Domain.DB != h.db || h.bootGeneration == ([32]byte{}) {
		return nil, fmt.Errorf("NATIVE_CREATE_COMPOSITION")
	}
	h.nativeCreate.mu.Lock()
	defer h.nativeCreate.mu.Unlock()
	if h.nativeCreate.service != service {
		h.nativeCreate.service = service
		h.nativeCreate.witnesses = map[string]nativeCreateWitness{}
	}
	return &nativeCreateVerifier{h, service}, nil
}

func (h *Host) validateNativeCreateFrame(raw []byte) error {
	strict, err := canonical.JSON(raw)
	if err != nil {
		return ErrFrameShape
	}
	var value any
	if json.Unmarshal(strict, &value) != nil {
		return ErrFrameShape
	}
	doc, err := nativeCreateDocument()
	if err != nil {
		return err
	}
	if doc.ValidateDefInput("NativeClientAttestRequestFrame", value) != nil {
		return ErrFrameShape
	}
	return nil
}
func validateNativeCreateResult(raw []byte) error {
	var value any
	if json.Unmarshal(raw, &value) != nil {
		return ErrFrameShape
	}
	doc, err := nativeCreateDocument()
	if err != nil {
		return err
	}
	if doc.ValidateDef("NativeClientAttestResultFrame", value) != nil {
		return ErrFrameShape
	}
	return nil
}

// A witness is populated only at this typed OS transport seam. No ordinary DB
// row, legacy boolean or caller-supplied client label can construct one.
func (h *Host) nativeClientAttest(ctx context.Context, call nativeInvocation) ([]byte, func(), error) {
	if call.peer == nil || !call.peer.validFor(h) || h.nativeCreate == nil {
		return nil, nil, ErrFrameUntrusted
	}
	if _, err := h.reverify(); err != nil {
		return nil, nil, ErrFrameUntrusted
	}
	encoded, err := json.Marshal(call.frame)
	if err != nil || h.validateNativeCreateFrame(encoded) != nil {
		return nil, nil, ErrFrameShape
	}
	var req nativeCreateRequest
	if json.Unmarshal(call.frame.Payload, &req) != nil {
		return nil, nil, ErrFrameShape
	}
	h.nativeCreate.mu.Lock()
	service := h.nativeCreate.service
	h.nativeCreate.mu.Unlock()
	if service == nil || service.Domain == nil || service.Domain.DB != h.db {
		return nil, nil, fmt.Errorf("NATIVE_CREATE_COMPOSITION")
	}
	limited, cancel := context.WithTimeout(ctx, 3*time.Second)
	defer cancel()
	tx, err := h.db.BeginTx(limited, nil)
	if err != nil {
		return nil, nil, fmt.Errorf("NATIVE_CREATE_STORAGE")
	}
	defer tx.Rollback()
	present, err := domain.NativeCreatePreparedSchemaAvailable(limited, tx)
	if err != nil {
		return nil, nil, fmt.Errorf("NATIVE_CREATE_STORAGE_INTEGRITY")
	}
	if !present {
		return nil, nil, fmt.Errorf("NATIVE_CREATE_UNSUPPORTED")
	}
	credential, err := h.domain.ResolveNativeCreateCredential(limited, tx, req.Credential, req.ProjectID)
	req.Credential = ""
	if err != nil || credential.Principal != h.boundPrincipal() {
		return nil, nil, ErrFrameUntrusted
	}
	if err = tx.Commit(); err != nil {
		return nil, nil, fmt.Errorf("NATIVE_CREATE_STORAGE")
	}
	now := h.nowUTC()
	expires := now.Add(nativeCreateWitnessTTL)
	if credential.ExpiresAt.Before(expires) {
		expires = credential.ExpiresAt
	}
	if !now.Before(expires) {
		return nil, nil, ErrFrameUntrusted
	}
	var random [48]byte
	if _, err = rand.Read(random[:]); err != nil {
		return nil, nil, fmt.Errorf("NATIVE_CREATE_ENTROPY")
	}
	ref := "natt-" + hex.EncodeToString(random[:32])
	instance := "nci-" + hex.EncodeToString(random[32:])
	v := domain.VerifiedNativeCreateOrigin{WitnessRef: ref, ClientInstanceRef: instance, HostInstanceID: h.InstanceID(), HostGenerationRef: domain.Digest(h.bootGeneration[:]), OSSubjectRef: call.peer.identity.Ref,
		Principal: credential.Principal, AuthorityRoot: credential.AuthorityRoot, CredentialHash: credential.CredentialHash, CommandID: req.CommandID, ClientID: call.frame.ClientID, ProjectID: req.ProjectID, Method: req.Method, ActualRawSHA256: req.RawHash, IssuedAt: now, ExpiresAt: expires}
	v.WitnessSHA256 = domain.Hash(v)
	h.nativeCreate.mu.Lock()
	for key, w := range h.nativeCreate.witnesses {
		if !now.Before(w.origin.ExpiresAt) {
			delete(h.nativeCreate.witnesses, key)
		}
	}
	if h.nativeCreate.service != service || len(h.nativeCreate.witnesses) >= nativeCreateWitnessLimit {
		h.nativeCreate.mu.Unlock()
		return nil, nil, fmt.Errorf("NATIVE_CREATE_WITNESS_LIMIT_OR_COMPOSITION")
	}
	if _, exists := h.nativeCreate.witnesses[ref]; exists {
		h.nativeCreate.mu.Unlock()
		return nil, nil, fmt.Errorf("NATIVE_CREATE_ENTROPY_COLLISION")
	}
	h.nativeCreate.witnesses[ref] = nativeCreateWitness{v, service, h.db}
	h.nativeCreate.mu.Unlock()
	undo := func() { h.nativeCreate.mu.Lock(); delete(h.nativeCreate.witnesses, ref); h.nativeCreate.mu.Unlock() }
	reply, err := json.Marshal(map[string]any{"kind": KindNativeClientAttestResult, "payload": map[string]any{"schema_version": 1, "attestation_ref": ref, "client_instance_ref": instance, "host_instance_id": h.InstanceID(), "expires_at": expires.Format(time.RFC3339Nano)}})
	if err != nil {
		undo()
		return nil, nil, err
	}
	return reply, undo, nil
}

func (v *nativeCreateVerifier) VerifyNativeCreate(ctx context.Context, tx *sql.Tx, q domain.NativeCreateProofQuery) (domain.VerifiedNativeCreateOrigin, error) {
	zero := domain.VerifiedNativeCreateOrigin{}
	h := v.host
	if ctx.Err() != nil {
		return zero, ctx.Err()
	}
	if tx == nil || h == nil || h.nativeCreate == nil || q.Service != v.service || q.Store != h.db || v.service == nil || v.service.Domain == nil || v.service.Domain.DB != h.db || q.Method != "session.create" || q.SessionID != nil || q.ExpectedRevision != nil || q.WriterEpoch != nil {
		return zero, ErrFrameUntrusted
	}
	h.nativeCreate.mu.Lock()
	w, ok := h.nativeCreate.witnesses[q.AttestationRef]
	current := h.nativeCreate.service
	h.nativeCreate.mu.Unlock()
	p := w.origin
	if !ok || current != v.service || w.service != v.service || w.store != h.db || p.HostGenerationRef != domain.Digest(h.bootGeneration[:]) || p.HostInstanceID != h.InstanceID() || p.OSSubjectRef != h.identity.Ref || p.Principal != q.Principal || p.AuthorityRoot != q.AuthorityRoot || p.CredentialHash != q.CredentialHash || p.CommandID != q.CommandID || p.ClientID != q.ClientID || p.ProjectID != q.ProjectID || p.Method != q.Method || p.ActualRawSHA256 != q.ActualRawSHA256 || !h.nowUTC().Before(p.ExpiresAt) || p.ExpiresAt.After(q.CredentialExpiresAt) {
		return zero, ErrFrameUntrusted
	}
	return p, nil
}
