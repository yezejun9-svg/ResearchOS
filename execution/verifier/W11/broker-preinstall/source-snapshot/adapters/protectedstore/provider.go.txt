// Package protectedstore keeps private bytes outside the control-plane database.
// This slice ships only a CANARY_ONLY provider. No independent-identity LIVE
// provider is installed or implied by the interface.
package protectedstore

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"mime"
	"regexp"
	"researchos.local/research-os/internal/canonical"
	"strings"
)

const MaxBlobBytes = 8 << 20

var ErrUnavailable = errors.New("PROTECTED_PROVIDER_UNAVAILABLE")
var ErrIsolation = errors.New("INDEPENDENT_IDENTITY_NOT_VERIFIED")
var ErrBoundary = errors.New("PROTECTED_BOUNDARY_INVALID")
var ErrIntegrity = errors.New("PROTECTED_BLOB_INTEGRITY")
var ErrNotFound = errors.New("PROTECTED_BLOB_UNAVAILABLE")

type Boundary struct {
	Mode                        string `json:"mode"`
	OwnerSID                    string `json:"owner_sid"`
	IndependentIdentity         bool   `json:"independent_identity"`
	UnrestrictedSameUserCanRead bool   `json:"unrestricted_same_user_can_read"`
}
type Blob struct {
	Ticket          string `json:"ticket"`
	Project         string `json:"project"`
	Hash            string `json:"hash"`
	Size            int64  `json:"size"`
	MediaType       string `json:"media_type"`
	MeasurementMode string `json:"measurement_mode"`
}

// Provider is a trusted deployment dependency, never constructed from a client
// pathname, submitted readiness Boolean, Agent name, or Artifact field.
// A future LIVE implementation must attest a separately verified OS identity.
type Provider interface {
	Boundary(context.Context) (Boundary, error)
	Ready(context.Context, string) error
	Describe(context.Context, string, string) (Blob, error)
	Read(context.Context, Blob) ([]byte, error)
}

func Digest(raw []byte) string { h := sha256.Sum256(raw); return "sha256:" + hex.EncodeToString(h[:]) }

var ticketPattern = regexp.MustCompile(`^ps1:[a-f0-9]{32}$`)

func ValidTicket(s string) bool { return ticketPattern.MatchString(s) }
func (b Blob) Valid() bool {
	decoded, e := hex.DecodeString(strings.TrimPrefix(b.Hash, "sha256:"))
	_, _, mediaErr := mime.ParseMediaType(b.MediaType)
	return ValidTicket(b.Ticket) && b.Project != "" && strings.HasPrefix(b.Hash, "sha256:") && e == nil && len(decoded) == 32 && mediaErr == nil && b.Size >= 0 && b.Size <= MaxBlobBytes && (b.MeasurementMode == "FIXTURE" || b.MeasurementMode == "LIVE")
}

// SafeSummary has no arbitrary strings, identifiers, per-case fields, reasons,
// input text or lineage refs. It is only a validator; publication/declassification
// still requires the future independent protected service and explicit review.
type SafeSummary struct {
	Schema              string `json:"schema"`
	Status              string `json:"status"`
	Total               int64  `json:"total"`
	Correct             int64  `json:"correct"`
	FalseAccept         int64  `json:"false_accept"`
	FalseReject         int64  `json:"false_reject"`
	Abstain             int64  `json:"abstain"`
	CriticalFalseAccept int64  `json:"critical_false_accept"`
	MaximumMode         string `json:"maximum_mode"`
}

func (s SafeSummary) Validate() error {
	if s.Schema != "researchos.protected-summary.v1" || (s.Status != "BLOCKED" && s.Status != "EXECUTION_REPORTED") || s.MaximumMode != "ADVISORY" || s.Total < 0 || s.Total > 1000000 {
		return ErrIntegrity
	}
	for _, v := range []int64{s.Correct, s.FalseAccept, s.FalseReject, s.Abstain, s.CriticalFalseAccept} {
		if v < 0 || v > s.Total {
			return ErrIntegrity
		}
	}
	if s.Correct+s.FalseAccept+s.FalseReject+s.Abstain != s.Total || s.CriticalFalseAccept > s.FalseAccept {
		return ErrIntegrity
	}
	return nil
}

func ParseSafeSummary(raw []byte) (SafeSummary, error) {
	var summary SafeSummary
	if len(raw) > 4096 {
		return summary, ErrIntegrity
	}
	strict, e := canonical.JSON(raw)
	if e != nil {
		return summary, ErrIntegrity
	}
	decoder := json.NewDecoder(bytes.NewReader(strict))
	decoder.DisallowUnknownFields()
	if decoder.Decode(&summary) != nil {
		return SafeSummary{}, ErrIntegrity
	}
	if e = summary.Validate(); e != nil {
		return SafeSummary{}, e
	}
	return summary, nil
}
