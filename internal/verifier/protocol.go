// Package verifier is the fixed-purpose local deterministic verification client.
// It never creates principals, launches workers, calls model endpoints, or
// manufactures an AcceptanceReceipt. Domain remains the acceptance authority.
package verifier

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"os"

	"researchos.local/research-os/internal/domain"
)

const ServiceID = "researchos.runtime-qualification-verifier.v1"
const Protocol = "researchos.runtime-verifier/1"

// The private job includes bounded original SSE and sealed output evidence.
// It is never accepted from the renderer or persisted with its credential.
const MaximumFrameBytes = 8 << 20

type Challenge struct {
	Protocol string `json:"protocol"`
	Nonce    string `json:"nonce"`
}
type Hello struct {
	Protocol  string `json:"protocol"`
	ServiceID string `json:"service_id"`
	Nonce     string `json:"nonce"`
	PID       int    `json:"pid"`
}
type Job struct {
	Protocol                 string        `json:"protocol"`
	Nonce                    string        `json:"nonce"`
	APIURL                   string        `json:"api_url"`
	Token                    string        `json:"token"`
	PrincipalID              string        `json:"principal_id"`
	ServiceRoot              string        `json:"service_root"`
	ProjectID                string        `json:"project_id"`
	RuntimeID                string        `json:"runtime_id"`
	TaskRef                  domain.Object `json:"task_ref"`
	RunRef                   domain.Object `json:"run_ref"`
	ProfileRef               domain.Object `json:"profile_ref"`
	ObservationRef           domain.Object `json:"observation_ref"`
	PlanHash                 string        `json:"plan_hash"`
	ExecutorID               string        `json:"executor_id"`
	Epoch                    int64         `json:"epoch"`
	VerificationSnapshot     domain.Object `json:"verification_snapshot"`
	VerificationSnapshotHash string        `json:"verification_snapshot_hash"`
}
type Result struct {
	Protocol       string        `json:"protocol"`
	Nonce          string        `json:"nonce"`
	Status         string        `json:"status"`
	RuntimeRef     domain.Object `json:"runtime_ref,omitempty"`
	AcceptanceRef  domain.Object `json:"acceptance_ref,omitempty"`
	ObservationRef domain.Object `json:"observation_ref,omitempty"`
	ErrorCode      string        `json:"error_code,omitempty"`
}

// ReadFrame has no unbounded buffered reader that could consume the next secret
// frame. Private inherited pipes carry exactly one newline-delimited JSON frame.
func ReadFrame(r io.Reader, target any) error {
	buf := make([]byte, 0, 1024)
	var b [1]byte
	for len(buf) <= MaximumFrameBytes {
		n, e := r.Read(b[:])
		if e != nil {
			return errors.New("private verifier frame incomplete")
		}
		if n == 0 {
			continue
		}
		if b[0] == '\n' {
			d := json.NewDecoder(bytes.NewReader(buf))
			d.DisallowUnknownFields()
			if e = d.Decode(target); e != nil {
				return errors.New("private verifier frame invalid")
			}
			var extra any
			if d.Decode(&extra) != io.EOF {
				return errors.New("private verifier frame has trailing data")
			}
			return nil
		}
		buf = append(buf, b[0])
	}
	return errors.New("private verifier frame too large")
}
func WriteFrame(w io.Writer, value any) error {
	raw, e := json.Marshal(value)
	if e != nil || len(raw) > MaximumFrameBytes {
		return errors.New("private verifier output invalid")
	}
	_, e = w.Write(append(raw, '\n'))
	return e
}

func Handshake(r io.Reader, w io.Writer) (Challenge, error) {
	var c Challenge
	if e := ReadFrame(r, &c); e != nil {
		return c, e
	}
	if c.Protocol != Protocol || len(c.Nonce) != 64 {
		return c, errors.New("private verifier challenge invalid")
	}
	return c, WriteFrame(w, Hello{Protocol: Protocol, ServiceID: ServiceID, Nonce: c.Nonce, PID: os.Getpid()})
}
