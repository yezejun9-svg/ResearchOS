// Package decision implements the documented Typesafe System One wire contract.
// A signal is evidence, never an acceptance or automatic-action grant.
package decision

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"net/http"
	"net/url"
	"researchos.local/research-os/internal/canonical"
	"sort"
	"strconv"
	"strings"
	"time"
)

const Endpoint = "https://api.typesafe.ai/v1/systemone"
const Adapter = "typesafe-systemone-v1"
const MaxResponseBytes = 2 << 20

type Scope struct {
	TaskType       string `json:"task_type"`
	Language       string `json:"language"`
	Provider       string `json:"provider"`
	ModelRevision  string `json:"model_revision"`
	RubricRevision string `json:"rubric_revision"`
}
type Question struct {
	Type         string `json:"type"`
	Instructions string `json:"instructions"`
	Criteria     any    `json:"criteria,omitempty"`
}
type Request struct {
	Model     string              `json:"model"`
	State     any                 `json:"state"`
	Questions map[string]Question `json:"questions"`
}
type Binding struct {
	ProjectID  string `json:"project_id"`
	InputHash  string `json:"input_hash"`
	RubricHash string `json:"rubric_hash"`
	Scope      Scope  `json:"scope"`
}

// Envelope retains invalid upstream bytes as base64; even malformed JSON remains evidence.
type Envelope struct {
	Version         int     `json:"version"`
	Binding         Binding `json:"binding"`
	Request         Request `json:"request"`
	RequestHash     string  `json:"request_hash"`
	Response        []byte  `json:"response"`
	ResponseHash    string  `json:"response_hash"`
	HTTPStatus      int     `json:"http_status"`
	TransportError  string  `json:"transport_error"`
	JevCalled       bool    `json:"jev_called"`
	MeasurementMode string  `json:"measurement_mode"`
	LatencyMS       int64   `json:"latency_ms"`
}
type Answer struct {
	Type          string             `json:"type"`
	Choice        *string            `json:"choice,omitempty"`
	Score         *float64           `json:"score,omitempty"`
	Noul          *float64           `json:"noul,omitempty"`
	Confidence    *float64           `json:"confidence,omitempty"`
	Probabilities map[string]float64 `json:"probabilities,omitempty"`
	Legend        map[string]string  `json:"legend,omitempty"`
}
type Usage struct {
	InputTokens  *int64 `json:"input_tokens"`
	OutputTokens *int64 `json:"output_tokens"`
}
type Response struct {
	Model   string            `json:"model"`
	Answers map[string]Answer `json:"answers"`
	Usage   Usage             `json:"usage"`
}
type Signal struct {
	Question    string
	Operation   string
	Value       *string
	Probability *float64
	Abstained   bool
	Reason      string
}
type Result struct {
	Signals       []Signal
	Selected      string
	Abstained     bool
	Reasons       []string
	ModelRevision string
	Usage         *Usage
}
type Client struct {
	HTTP    *http.Client
	Token   string
	URL     string
	Fixture bool
	Timeout time.Duration
}

func Digest(b []byte) string { h := sha256.Sum256(b); return "sha256:" + hex.EncodeToString(h[:]) }
func Encode(v any) []byte {
	b, e := json.Marshal(v)
	if e != nil {
		panic(e)
	}
	canonicalBytes, e := canonical.JSON(b)
	if e != nil {
		panic(e)
	}
	return canonicalBytes
}
func Strict(raw []byte, dest any) error {
	b, e := canonical.JSON(raw)
	if e != nil {
		return e
	}
	d := json.NewDecoder(bytes.NewReader(b))
	d.DisallowUnknownFields()
	return d.Decode(dest)
}
func (s Scope) Valid() bool {
	return s.TaskType != "" && (s.Language == "zh" || s.Language == "zh-en" || s.Language == "en") && s.Provider == "typesafe" && s.ModelRevision != "" && s.RubricRevision != ""
}
func (r Request) Validate() error {
	if r.Model == "" || r.State == nil || len(r.Questions) == 0 {
		return errors.New("model, state and questions required")
	}
	for id, q := range r.Questions {
		if id == "" || strings.TrimSpace(q.Instructions) == "" {
			return errors.New("question identity and instructions required")
		}
		switch q.Type {
		case "choice":
			var c map[string]string
			if Strict(Encode(q.Criteria), &c) != nil || len(c) < 2 || len(c) > 255 {
				return errors.New("choice requires 2..255 named options")
			}
			for k := range c {
				if k == "" {
					return errors.New("empty choice")
				}
			}
		case "score":
			var c []string
			if Strict(Encode(q.Criteria), &c) != nil || len(c) < 2 || len(c) > 10 {
				return errors.New("score requires 2..10 ordered criteria")
			}
		case "noul":
			if q.Criteria != nil {
				var c map[string]string
				if Strict(Encode(q.Criteria), &c) != nil || len(c) != 2 || c["true"] == "" || c["false"] == "" {
					return errors.New("noul criteria must name true and false")
				}
			}
		default:
			return errors.New("unknown question type")
		}
	}
	return nil
}
func (c Client) Call(ctx context.Context, b Binding, r Request) (Envelope, error) {
	if e := r.Validate(); e != nil {
		return Envelope{}, e
	}
	if !b.Scope.Valid() || b.ProjectID == "" || b.InputHash == "" || b.RubricHash == "" || r.Model != b.Scope.ModelRevision {
		return Envelope{}, errors.New("exact invocation binding required")
	}
	endpoint := c.URL
	if endpoint == "" {
		endpoint = Endpoint
	}
	u, e := url.Parse(endpoint)
	if e != nil {
		return Envelope{}, e
	}
	if !c.Fixture && endpoint != Endpoint {
		return Envelope{}, errors.New("live endpoint must be official fixed HTTPS endpoint")
	}
	if c.Fixture && !(u.Scheme == "http" && (u.Hostname() == "127.0.0.1" || u.Hostname() == "localhost" || u.Hostname() == "::1")) {
		return Envelope{}, errors.New("fixture endpoint must be loopback HTTP")
	}
	if !c.Fixture && c.Token == "" {
		return Envelope{}, errors.New("live credential required")
	}
	mode := "LIVE"
	if c.Fixture {
		mode = "FIXTURE"
	}
	env := Envelope{Version: 1, Binding: b, Request: r, RequestHash: Digest(Encode(r)), MeasurementMode: mode, Response: []byte{}}
	timeout := c.Timeout
	if timeout <= 0 || timeout > 60*time.Second {
		timeout = 30 * time.Second
	}
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	req, e := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(Encode(r)))
	if e != nil {
		return env, e
	}
	req.Header.Set("Content-Type", "application/json")
	if !c.Fixture {
		req.Header.Set("Authorization", "Bearer "+c.Token)
	}
	client := http.Client{}
	if c.HTTP != nil {
		client = *c.HTTP
	}
	client.CheckRedirect = func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }
	start := time.Now()
	env.JevCalled = !c.Fixture
	resp, e := client.Do(req)
	if e != nil {
		env.TransportError = "TRANSPORT_ERROR"
		if ctx.Err() != nil {
			env.TransportError = "TIMEOUT_OR_CANCELLED"
		}
	} else {
		env.HTTPStatus = resp.StatusCode
		env.Response, e = io.ReadAll(io.LimitReader(resp.Body, MaxResponseBytes+1))
		resp.Body.Close()
		if e != nil {
			env.TransportError = "BODY_READ_ERROR"
		}
		if len(env.Response) > MaxResponseBytes {
			env.TransportError = "RESPONSE_TOO_LARGE"
		}
	}
	env.LatencyMS = time.Since(start).Milliseconds()
	env.ResponseHash = Digest(env.Response)
	return env, nil
}
func invalid(reason string) Result {
	return Result{Abstained: true, Reasons: []string{reason}, Signals: []Signal{}}
}
func probability(p *float64) bool {
	return p != nil && !math.IsNaN(*p) && !math.IsInf(*p, 0) && *p >= 0 && *p <= 1
}
func Evaluate(e Envelope, threshold float64) Result {
	if threshold < 0.5 || threshold > 1 || math.IsNaN(threshold) {
		return invalid("INVALID_THRESHOLD")
	}
	if e.Version != 1 || !e.Binding.Scope.Valid() || e.Request.Model != e.Binding.Scope.ModelRevision || e.Request.Validate() != nil || e.RequestHash != Digest(Encode(e.Request)) || e.ResponseHash != Digest(e.Response) || e.LatencyMS < 0 {
		return invalid("ENVELOPE_BINDING_INVALID")
	}
	if e.MeasurementMode != "LIVE" && e.MeasurementMode != "FIXTURE" || e.MeasurementMode == "FIXTURE" && e.JevCalled || e.MeasurementMode == "LIVE" && !e.JevCalled {
		return invalid("INVOCATION_PROVENANCE_INVALID")
	}
	if e.TransportError != "" {
		return invalid(e.TransportError)
	}
	if e.HTTPStatus != 200 {
		return invalid("UPSTREAM_HTTP_ERROR")
	}
	var response Response
	if len(e.Response) > MaxResponseBytes || Strict(e.Response, &response) != nil {
		return invalid("INVALID_RESPONSE_JSON")
	}
	if response.Model != e.Binding.Scope.ModelRevision {
		return invalid("MODEL_REVISION_CHANGED")
	}
	if response.Usage.InputTokens == nil || response.Usage.OutputTokens == nil || *response.Usage.InputTokens < 0 || *response.Usage.OutputTokens < 0 {
		return invalid("INVALID_USAGE")
	}
	if len(response.Answers) != len(e.Request.Questions) {
		return invalid("ANSWER_SET_MISMATCH")
	}
	out := Result{ModelRevision: response.Model, Usage: &response.Usage, Reasons: []string{}, Signals: []Signal{}}
	keys := []string{}
	for k := range e.Request.Questions {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, id := range keys {
		q := e.Request.Questions[id]
		a, ok := response.Answers[id]
		if !ok || a.Type != q.Type {
			return invalid("ANSWER_TYPE_MISMATCH")
		}
		signal := Signal{Question: id, Operation: strings.ToUpper(q.Type)}
		reason := ""
		switch q.Type {
		case "noul":
			if !probability(a.Noul) || a.Choice != nil || a.Score != nil || a.Confidence != nil || len(a.Probabilities) != 0 || len(a.Legend) != 0 {
				return invalid("INVALID_NOUL")
			}
			v := strconv.FormatFloat(*a.Noul, 'g', -1, 64)
			signal.Value = &v
			signal.Probability = a.Noul
			if *a.Noul < threshold {
				reason = "NOUL_INSUFFICIENT_EVIDENCE"
			}
		case "choice", "score":
			if !probability(a.Confidence) || len(a.Probabilities) == 0 || a.Noul != nil {
				return invalid("INVALID_PROBABILITY")
			}
			sum := 0.0
			for _, p := range a.Probabilities {
				if !probability(&p) {
					return invalid("INVALID_PROBABILITY")
				}
				sum += p
			}
			if math.Abs(sum-1) > 1e-5 {
				return invalid("INVALID_PROBABILITY_SUM")
			}
			signal.Probability = a.Confidence
			if q.Type == "choice" {
				var c map[string]string
				_ = Strict(Encode(q.Criteria), &c)
				if a.Choice == nil || a.Score != nil || len(a.Legend) != 0 || len(c) != len(a.Probabilities) {
					return invalid("INVALID_CHOICE")
				}
				for k := range c {
					if _, ok := a.Probabilities[k]; !ok {
						return invalid("UNKNOWN_ACTION")
					}
				}
				p, ok := a.Probabilities[*a.Choice]
				if !ok {
					return invalid("UNKNOWN_ACTION")
				}
				for _, alternative := range a.Probabilities {
					if alternative > p+1e-5 {
						return invalid("CHOICE_NOT_MAXIMUM")
					}
				}
				signal.Value = a.Choice
				if id == "action" {
					out.Selected = *a.Choice
				}
			} else {
				var c []string
				_ = Strict(Encode(q.Criteria), &c)
				if a.Score == nil || a.Choice != nil || len(a.Probabilities) != len(c) || len(a.Legend) != len(c) {
					return invalid("INVALID_SCORE")
				}
				mean := 0.0
				for i, s := range c {
					k := strconv.Itoa(i)
					p, ok := a.Probabilities[k]
					if !ok || a.Legend[k] != s {
						return invalid("SCORE_CRITERIA_CHANGED")
					}
					mean += float64(i) * p
				}
				if math.IsNaN(*a.Score) || math.Abs(mean-*a.Score) > 1e-5 {
					return invalid("SCORE_MEAN_MISMATCH")
				}
				v := strconv.FormatFloat(*a.Score, 'g', -1, 64)
				signal.Value = &v
				if *a.Score/float64(len(c)-1) < threshold {
					reason = "LOW_SCORE"
				}
			}
			if *a.Confidence < threshold {
				reason = "LOW_CONFIDENCE"
			}
		}
		signal.Abstained = reason != ""
		signal.Reason = reason
		out.Signals = append(out.Signals, signal)
		if reason != "" {
			out.Abstained = true
			out.Reasons = append(out.Reasons, fmt.Sprintf("%s:%s", id, reason))
		}
	}
	if out.Selected == "" {
		out.Abstained = true
		out.Reasons = append(out.Reasons, "ACTION_NOT_MEASURED")
	}
	return out
}
