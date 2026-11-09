package api

// POST /v2/command — the single typed command service for CLI and Desktop (W03-02).
//
// Identity comes only from a host-issued credential (never from a field the client can
// claim), the envelope is decoded by the typed protocol core, and the command runs in one
// transaction that writes business state and its session events together. The pinned
// contract documents are embedded so the route cannot start against a schema that differs
// from the published hashes; a mismatch or load failure disables v2 and answers
// HOST_UNAVAILABLE instead of falling back to an older protocol.

import (
	"context"
	"crypto/sha256"
	"database/sql"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"runtime/debug"
	"strconv"
	"time"

	"researchos.local/research-os/internal/domain"
)

//go:embed contracts/client.protocol.schema.json
var protocolSchemaJSON []byte

//go:embed contracts/domain.schema.json
var domainSchemaJSON []byte

const (
	protocolSchemaSHA256 = "8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b"
	domainSchemaSHA256   = "b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54"
	// maxCommandBytes bounds one command envelope; the contract's largest payload is far below it.
	maxCommandBytes = 1 << 20
)

// v2Service carries the typed service plus the host facts it is allowed to report.
type v2Service struct {
	svc     *domain.ClientService
	db      *sql.DB
	loadErr error
}

// ClientProtocolDocument exposes the same pinned schema used by the HTTP
// boundary, so host runtime projections validate typed events identically.
func ClientProtocolDocument() (*domain.SchemaDoc, error) {
	if got := sha256.Sum256(protocolSchemaJSON); hex.EncodeToString(got[:]) != protocolSchemaSHA256 {
		return nil, ErrContractDigest
	}
	if got := sha256.Sum256(domainSchemaJSON); hex.EncodeToString(got[:]) != domainSchemaSHA256 {
		return nil, ErrContractDigest
	}
	return domain.LoadSchemaWithExternals(protocolSchemaJSON, map[string][]byte{
		"domain.schema.json": domainSchemaJSON,
	})
}

func newV2Service(db *sql.DB) *v2Service {
	doc, err := ClientProtocolDocument()
	if err != nil {
		return &v2Service{db: db, loadErr: err}
	}
	buildID, mode := coreBuildID()
	ttl, err := leaseTTL()
	if err != nil {
		return &v2Service{db: db, loadErr: err}
	}
	return &v2Service{db: db, svc: &domain.ClientService{Doc: doc, Host: domain.ClientHostInfo{
		InstanceID:     "host-" + strconv.Itoa(os.Getpid()),
		CoreBuildID:    buildID,
		OperatingMode:  mode,
		ConfigRevision: 0, // configuration revisions belong to a later card; 0 means "none recorded"
		LeaseTTL:       ttl,
	}}}
}

var ErrContractDigest = &digestError{}

type digestError struct{}

func (*digestError) Error() string { return "PINNED_CONTRACT_DIGEST_MISMATCH" }

// coreBuildID reports the real build identity of this binary; when VCS stamping is absent it
// says so instead of inventing a revision.
func coreBuildID() (string, string) {
	info, ok := debug.ReadBuildInfo()
	if !ok {
		return "core-unstamped", operatingMode()
	}
	revision, modified := "", ""
	for _, s := range info.Settings {
		switch s.Key {
		case "vcs.revision":
			revision = s.Value
		case "vcs.modified":
			modified = s.Value
		}
	}
	if revision == "" {
		return "core-unstamped", operatingMode()
	}
	if modified == "true" {
		revision += "-dirty"
	}
	return "core-" + revision[:min(12, len(revision))], operatingMode()
}

func operatingMode() string { return "LOCAL_USER_HOST" }

// leaseTTL is host configuration, not a client parameter; unset uses the local
// host's 90-second writer lease.
func leaseTTL() (time.Duration, error) {
	raw := os.Getenv("RESEARCHOS_WRITER_LEASE_TTL")
	if raw == "" {
		return 90 * time.Second, nil
	}
	d, err := time.ParseDuration(raw)
	if err != nil || d <= 0 || d > 15*time.Minute {
		return 0, &leaseError{}
	}
	return d, nil
}

type leaseError struct{}

func (*leaseError) Error() string { return "WRITER_LEASE_POLICY_INVALID" }

func (v *v2Service) serve(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	if v.loadErr != nil || v.svc == nil {
		// No downgrade path: an unverifiable contract or lease policy closes v2 completely.
		writeTypedError(w, http.StatusServiceUnavailable, nil, "HOST_UNAVAILABLE", v.loadErr.Error())
		return
	}
	body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, maxCommandBytes))
	if err != nil {
		writeTypedError(w, http.StatusRequestEntityTooLarge, nil, "INVALID_REQUEST", "command body unreadable or too large")
		return
	}
	// The protocol version is settled before anything else: a client speaking another
	// protocol must learn UNSUPPORTED_PROTOCOL rather than a credential error, and no state
	// is touched by this peek.
	if code, bad := peekProtocol(body); bad != "" {
		writeTypedError(w, http.StatusBadRequest, nil, code, bad)
		return
	}
	env, decErr := domain.DecodeEnvelope(body)
	principal, authErr := domain.AuthenticateToken(r.Context(), v.db, bearerToken(r))
	if authErr != nil {
		if env != nil {
			// The envelope is well formed, so the client gets the typed rejection it asked for.
			resp := domain.NewTypedRejection(env, "UNAUTHENTICATED", "host credential required")
			writeJSON(w, http.StatusUnauthorized, resp)
			return
		}
		writeTypedError(w, http.StatusUnauthorized, nil, "UNAUTHENTICATED", "host credential required")
		return
	}
	if decErr != nil {
		code := "INVALID_REQUEST"
		status := http.StatusBadRequest
		switch decErr {
		case domain.ErrProtocolVersion:
			code, status = "UNSUPPORTED_PROTOCOL", http.StatusBadRequest
		case domain.ErrUnknownMethod:
			code, status = "UNSUPPORTED_METHOD", http.StatusBadRequest
		}
		writeTypedError(w, status, nil, code, decErr.Error())
		return
	}
	tx, err := v.db.BeginTx(r.Context(), nil)
	if err != nil {
		writeTypedError(w, http.StatusInternalServerError, env, "INTERNAL_ERROR", "host transaction unavailable")
		return
	}
	defer tx.Rollback()
	// Grants are the existing per-principal project authorisations; a null project command
	// (host.status) still requires an authenticated principal but no project grant.
	if env.ProjectID != nil && *env.ProjectID != "" && !principal.Allowed(*env.ProjectID, "", "", false) {
		resp := domain.NewTypedRejection(env, "FORBIDDEN", "principal has no grant for this project")
		writeJSON(w, http.StatusForbidden, resp)
		return
	}
	resp, replayed, err := v.svc.Execute(r.Context(), tx, env, principal.ID)
	if err != nil {
		if err == domain.ErrIdemConflict {
			writeTypedError(w, http.StatusConflict, env, "COMMAND_ID_CONFLICT", "command_id reused with a different request")
			return
		}
		log.Printf("v2 command failed: %v", err)
		writeTypedError(w, http.StatusInternalServerError, env, "INTERNAL_ERROR", "command could not be completed")
		return
	}
	if err := tx.Commit(); err != nil {
		writeTypedError(w, http.StatusInternalServerError, env, "INTERNAL_ERROR", "command transaction could not be committed")
		return
	}
	_ = replayed
	writeJSON(w, http.StatusOK, resp)
}

// peekProtocol does the minimum structural check that decides which error a client sees
// first: is this JSON at all, and does it claim researchos-client/2?
func peekProtocol(body []byte) (string, string) {
	var frame map[string]any
	if err := json.Unmarshal(body, &frame); err != nil {
		return "INVALID_REQUEST", "command envelope is not a JSON object"
	}
	v, ok := frame["protocol_version"]
	if !ok {
		return "UNSUPPORTED_PROTOCOL", "protocol_version is required"
	}
	if s, isString := v.(string); !isString || s != domain.ProtocolV2 {
		return "UNSUPPORTED_PROTOCOL", "only researchos-client/2 is served"
	}
	return "", ""
}

func bearerToken(r *http.Request) string {
	h := r.Header.Get("Authorization")
	const prefix = "Bearer "
	if len(h) > len(prefix) && h[:len(prefix)] == prefix {
		return h[len(prefix):]
	}
	return ""
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

// writeTypedError answers before an envelope can be decoded at all, so no CommandResponse
// fields are fabricated: the shape is the published ProtocolError plus its HTTP status.
func writeTypedError(w http.ResponseWriter, status int, env *domain.Envelope, code, message string) {
	writeJSON(w, status, map[string]any{"error": map[string]any{
		"code": code, "message": message, "retryable": status >= 500,
		"correlation_id": envCommandID(env),
	}})
}

func envCommandID(env *domain.Envelope) string {
	if env == nil || env.CommandID == nil {
		return "unparsed-command"
	}
	return *env.CommandID
}

var _ = context.Background
