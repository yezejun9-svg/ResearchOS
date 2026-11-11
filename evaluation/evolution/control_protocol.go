package evolution

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"regexp"
	"sort"
	"strings"

	"researchos.local/research-os/internal/canonical"
)

const ControlProfile = "control-business-fixture-v1"
const ControlProtocol = "researchos-control-replay-v1"
const ControlPublicRevision = "control-public-research-gates-v1"
const ControlPrivateRevision = "control-private-research-gates-v1"
const ControlProjection = "control-manual-research-projection-v1"
const ControlPrincipal = "fixture-control-replay-owner"
const ControlCredential = "fixture-control-replay-only-not-an-authority-credential-v1"

// Binding is supplied by the trusted host. Neither a candidate nor a request
// may substitute a different source generation, projection or evaluator.
type ControlBinding struct {
	Protocol            string `json:"protocol"`
	AuthorityGeneration string `json:"authority_generation"`
	SourceSnapshotHash  string `json:"source_snapshot_hash"`
	SnapshotHash        string `json:"snapshot_hash"`
	ProjectionHash      string `json:"projection_hash"`
	ProjectionPolicy    string `json:"projection_policy"`
	ReleaseHash         string `json:"release_hash"`
	ProjectID           string `json:"project_id"`
	CycleID             string `json:"cycle_id"`
}

type ControlBundle struct {
	Binding ControlBinding    `json:"binding"`
	Files   map[string][]byte `json:"files"`
}

// Inputs contain one case per child and no labels, rubric, private store or
// release credential. The only credential is a public projection-only fixture.
type ControlStep struct {
	Method         string          `json:"method"`
	Path           string          `json:"path"`
	Authenticated  bool            `json:"authenticated"`
	Body           json.RawMessage `json:"body,omitempty"`
	ETag           string          `json:"etag"`
	IdempotencyKey string          `json:"idempotency_key"`
}
type ControlCase struct {
	ID    string        `json:"id"`
	Steps []ControlStep `json:"steps"`
}
type ControlInputs struct {
	Revision string         `json:"revision"`
	Binding  ControlBinding `json:"binding"`
	Cases    []ControlCase  `json:"cases"`
}
type ControlRequest struct {
	Binding ControlBinding `json:"binding"`
	Case    ControlCase    `json:"case"`
}
type ControlHTTPResult struct {
	Status  int               `json:"status"`
	Headers map[string]string `json:"headers"`
	Body    json.RawMessage   `json:"body"`
}
type ControlReplayResult struct {
	Binding ControlBinding      `json:"binding"`
	CaseID  string              `json:"case_id"`
	Results []ControlHTTPResult `json:"results"`
}
type ControlLabel struct {
	ID        string              `json:"id"`
	Results   []ControlHTTPResult `json:"results"`
	Unchanged bool                `json:"database_unchanged"`
	Required  bool                `json:"required"`
}
type ControlLabels struct {
	Revision string         `json:"revision"`
	Binding  ControlBinding `json:"binding"`
	Labels   []ControlLabel `json:"labels"`
}
type ControlSuite struct {
	Inputs ControlInputs `json:"inputs"`
	Labels ControlLabels `json:"labels"`
}

var controlID = regexp.MustCompile(`^[A-Za-z0-9_-]{1,100}$`)
var controlDigest = regexp.MustCompile(`^sha256:[0-9a-f]{64}$`)

func (b ControlBinding) Validate() error {
	if b.Protocol != ControlProtocol || b.ProjectionPolicy != ControlProjection || !controlID.MatchString(b.ProjectID) || !controlID.MatchString(b.CycleID) {
		return fmt.Errorf("CONTROL_PROTOCOL_OR_PROJECTION")
	}
	for _, hash := range []string{b.AuthorityGeneration, b.SourceSnapshotHash, b.SnapshotHash, b.ProjectionHash, b.ReleaseHash} {
		if !controlDigest.MatchString(hash) {
			return fmt.Errorf("CONTROL_BINDING_DIGEST")
		}
	}
	return nil
}

func StrictControlJSON(raw []byte, target any) error {
	if len(raw) == 0 || len(raw) > 64*1024*1024 {
		return fmt.Errorf("CONTROL_JSON_BOUND")
	}
	canon, err := canonical.JSON(raw)
	if err != nil {
		return err
	}
	d := json.NewDecoder(bytes.NewReader(canon))
	d.DisallowUnknownFields()
	return d.Decode(target)
}

func ValidateControlCase(c ControlCase, binding ControlBinding) error {
	if err := binding.Validate(); err != nil {
		return err
	}
	if !controlID.MatchString(c.ID) || len(c.Steps) < 1 || len(c.Steps) > 3 {
		return fmt.Errorf("CONTROL_SINGLE_CASE_BOUND")
	}
	prefix := "/v1/projects/" + binding.ProjectID + "/research-cycles/"
	for _, step := range c.Steps {
		if !strings.HasPrefix(step.Path, prefix) || len(step.Body) > 4096 {
			return fmt.Errorf("CONTROL_API_SCOPE")
		}
		id := strings.TrimPrefix(step.Path, prefix)
		if step.Method == "POST" {
			id = strings.TrimSuffix(id, "/close")
			if step.Path != prefix+id+"/close" || !controlID.MatchString(step.IdempotencyKey) {
				return fmt.Errorf("CONTROL_CLOSE_SCOPE")
			}
		} else if step.Method != "GET" || step.ETag != "" || step.IdempotencyKey != "" || len(step.Body) != 0 {
			return fmt.Errorf("CONTROL_READ_SCOPE")
		}
		if id != binding.CycleID {
			return fmt.Errorf("CONTROL_OBJECT_ID")
		}
		if step.Method == "POST" {
			var body struct {
				RequestedStatus string `json:"requested_status"`
				OutcomeSummary  string `json:"outcome_summary"`
			}
			if err := StrictControlJSON(step.Body, &body); err != nil || body.RequestedStatus != "COMPLETE" || body.OutcomeSummary == "" {
				return fmt.Errorf("CONTROL_CLOSE_INPUT")
			}
			if !regexp.MustCompile(`^"r[1-9][0-9]*"$`).MatchString(step.ETag) {
				return fmt.Errorf("CONTROL_ETAG")
			}
		}
	}
	return nil
}

// The first profile measures unchanged real read/rejection behavior. It cannot
// certify successful closure, monitor completion, live providers or throughput.
func ValidateControlDataset(inputs ControlInputs, labels ControlLabels) error {
	if (inputs.Revision != ControlPublicRevision && inputs.Revision != ControlPrivateRevision) || labels.Revision != inputs.Revision || labels.Binding != inputs.Binding || len(inputs.Cases) < 2 || len(inputs.Cases) > 8 || len(inputs.Cases) != len(labels.Labels) {
		return fmt.Errorf("CONTROL_DATASET_BINDING")
	}
	seen := map[string]bool{}
	for i, c := range inputs.Cases {
		if err := ValidateControlCase(c, inputs.Binding); err != nil {
			return err
		}
		label := labels.Labels[i]
		if seen[c.ID] || label.ID != c.ID || !label.Unchanged || !label.Required || len(label.Results) != len(c.Steps) {
			return fmt.Errorf("CONTROL_LABEL_BINDING")
		}
		if inputs.Revision == ControlPublicRevision && !strings.HasPrefix(c.ID, "public-control-") || inputs.Revision == ControlPrivateRevision && !strings.HasPrefix(c.ID, "private-control-") {
			return fmt.Errorf("CONTROL_DATASET_ID_SCOPE")
		}
		seen[c.ID] = true
		for j, r := range label.Results {
			if r.Status != 200 && r.Status != 401 && r.Status != 412 && r.Status != 422 {
				return fmt.Errorf("CONTROL_LABEL_STATUS")
			}
			if c.Steps[j].Method == "POST" && r.Status == 200 {
				return fmt.Errorf("CONTROL_UNCHANGED_LABEL_REQUIRED")
			}
			if _, err := ControlSemantic(r); err != nil {
				return err
			}
		}
	}
	return nil
}

// Raw bodies and all process streams are retained in the private proof. Only a
// root error correlation_id is normalized; status, errors, object identity,
// revision, permissions, coverage, costs and every other body field remain.
func ControlSemantic(r ControlHTTPResult) ([]byte, error) {
	if len(r.Body) == 0 || len(r.Body) > 1024*1024 {
		return nil, fmt.Errorf("CONTROL_RESPONSE_BODY")
	}
	canon, err := canonical.JSON(r.Body)
	if err != nil {
		return nil, err
	}
	var body map[string]any
	if err = json.Unmarshal(canon, &body); err != nil {
		return nil, err
	}
	if r.Status >= 400 {
		delete(body, "correlation_id")
	}
	for name := range r.Headers {
		if name != "Content-Type" && name != "Cache-Control" && name != "ETag" && name != "X-ResearchOS-Principal-ID" {
			return nil, fmt.Errorf("CONTROL_RESPONSE_HEADER")
		}
	}
	return canonical.JSON(Bytes(map[string]any{"status": r.Status, "headers": r.Headers, "body": body}))
}

func ControlPolicy(binding ControlBinding, suiteHash string) map[string]any {
	return map[string]any{"scope": Scope, "profile": ControlProfile, "protocol": ControlProtocol, "projection": ControlProjection, "binding": binding, "suite_hash": suiteHash, "min_additional_correct": 1, "mandatory_regressions_allowed": 0, "normalization": "root-error-correlation-id-only", "database_changes_allowed": 0, "timeout_ms": 10000, "promotion_live_qualified": false}
}

// Host and replay use the same canonical inventory encoding; the host reads the
// returned DB itself and does not accept a candidate-reported state hash.
func ControlDatabaseHash(db interface {
	Query(string, ...any) (*sql.Rows, error)
}) (string, error) {
	rows, err := db.Query("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name")
	if err != nil {
		return "", err
	}
	schema := []any{}
	tables := []string{}
	for rows.Next() {
		var kind, name, table, ddl string
		if err = rows.Scan(&kind, &name, &table, &ddl); err != nil {
			rows.Close()
			return "", err
		}
		schema = append(schema, []string{kind, name, table, ddl})
		if kind == "table" {
			tables = append(tables, name)
		}
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return "", err
	}
	data := map[string]any{"schema": schema}
	for _, table := range tables {
		r, err := db.Query(`SELECT * FROM "` + strings.ReplaceAll(table, `"`, `""`) + `"`)
		if err != nil {
			return "", err
		}
		cols, err := r.Columns()
		if err != nil {
			r.Close()
			return "", err
		}
		entries := []string{}
		for r.Next() {
			values := make([]any, len(cols))
			pointers := make([]any, len(cols))
			for i := range values {
				pointers[i] = &values[i]
			}
			if err = r.Scan(pointers...); err != nil {
				r.Close()
				return "", err
			}
			entries = append(entries, string(Bytes(values)))
		}
		err = r.Err()
		r.Close()
		if err != nil {
			return "", err
		}
		sort.Strings(entries)
		data[table] = map[string]any{"columns": cols, "rows": entries}
	}
	return Digest(Bytes(data)), nil
}
