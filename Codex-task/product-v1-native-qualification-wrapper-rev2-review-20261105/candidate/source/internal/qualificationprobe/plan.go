package qualificationprobe

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"errors"
	"path/filepath"
	"strings"
)

const Schema = "researchos.native-qualification-plan.v1"
const EventSchema = "researchos.native-qualification-event.v1"

var Cases = [...]string{"source_read", "denied_read", "source_write_open", "working_write_open", "source_create", "working_create", "loopback_connect"}

const CompleteBitmap = (1 << len(Cases)) - 1

type Plan struct {
	Schema  string   `json:"schema"`
	Source  string   `json:"source"`
	Working string   `json:"working"`
	Denied  string   `json:"denied"`
	Nonce   string   `json:"nonce"`
	Port    uint16   `json:"port"`
	Cases   []string `json:"cases"`
}
type Event struct {
	Schema string `json:"schema"`
	Phase  string `json:"phase"`
	Case   string `json:"case"`
	Errno  int    `json:"errno"`
	Opened bool   `json:"opened"`
	Digest string `json:"digest"`
	Bytes  int    `json:"bytes"`
	Bitmap uint32 `json:"bitmap"`
}

func FixedCases() []string { return append([]string(nil), Cases[:]...) }
func Validate(p Plan) error {
	if p.Schema != Schema || p.Port == 0 || len(p.Cases) != len(Cases) || !strings.HasPrefix(p.Nonce, "researchos-readonly-") || len(p.Nonce) != len("researchos-readonly-")+32 {
		return errors.New("QUALIFICATION_PLAN_INVALID")
	}
	for i, c := range Cases {
		if p.Cases[i] != c {
			return errors.New("QUALIFICATION_PLAN_CASES_CHANGED")
		}
	}
	for _, c := range p.Nonce[len("researchos-readonly-"):] {
		if !strings.ContainsRune("0123456789abcdef", c) {
			return errors.New("QUALIFICATION_PLAN_NONCE_INVALID")
		}
	}
	paths := []string{p.Source, p.Working, p.Denied}
	for _, path := range paths {
		if !filepath.IsAbs(path) || filepath.Clean(path) != path || strings.ContainsAny(path, "\x00\r\n;") {
			return errors.New("QUALIFICATION_PLAN_PATH_INVALID")
		}
	}
	if filepath.Base(p.Source) != "S" || filepath.Base(p.Working) != "QW" || filepath.Base(p.Denied) != "D" || !strings.EqualFold(filepath.Dir(p.Source), filepath.Dir(p.Working)) || !strings.EqualFold(filepath.Dir(p.Source), filepath.Dir(p.Denied)) {
		return errors.New("QUALIFICATION_PLAN_ROOTS_OVERLAP")
	}
	if strings.EqualFold(paths[0], paths[1]) || strings.EqualFold(paths[0], paths[2]) || strings.EqualFold(paths[1], paths[2]) {
		return errors.New("QUALIFICATION_PLAN_ROOTS_OVERLAP")
	}
	for _, other := range paths[1:] {
		rel, err := filepath.Rel(paths[0], other)
		if err != nil || rel == "." || rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
			return errors.New("QUALIFICATION_PLAN_ROOTS_OVERLAP")
		}
	}
	return nil
}
func Encode(p Plan) (string, error) {
	if err := Validate(p); err != nil {
		return "", err
	}
	raw, err := json.Marshal(p)
	if err != nil {
		return "", err
	}
	if len(raw) > 4096 {
		return "", errors.New("QUALIFICATION_PLAN_TOO_LARGE")
	}
	return base64.RawURLEncoding.EncodeToString(raw), nil
}
func Decode(encoded string) (Plan, error) {
	var p Plan
	if len(encoded) == 0 || len(encoded) > 5500 {
		return p, errors.New("QUALIFICATION_PLAN_TOO_LARGE")
	}
	raw, err := base64.RawURLEncoding.DecodeString(encoded)
	if err != nil || len(raw) > 4096 {
		return p, errors.New("QUALIFICATION_PLAN_INVALID")
	}
	if json.Unmarshal(raw, &p) != nil {
		return p, errors.New("QUALIFICATION_PLAN_INVALID")
	}
	canonical, _ := json.Marshal(p)
	if !bytes.Equal(raw, canonical) || Validate(p) != nil {
		return Plan{}, errors.New("QUALIFICATION_PLAN_NONCANONICAL")
	}
	return p, nil
}
func ParseTranscript(raw []byte) (map[string]Event, error) {
	if len(raw) == 0 || len(raw) > 1<<20 || raw[len(raw)-1] != '\n' {
		return nil, errors.New("QUALIFICATION_TRANSCRIPT_INCOMPLETE")
	}
	lines := bytes.Split(raw[:len(raw)-1], []byte{'\n'})
	if len(lines) != 2*len(Cases)+1 {
		return nil, errors.New("QUALIFICATION_TRANSCRIPT_CASE_COUNT")
	}
	results := make(map[string]Event, len(Cases))
	for i, name := range Cases {
		for j, phase := range []string{"START", "RESULT"} {
			var e Event
			line := lines[2*i+j]
			if len(line) > 4096 || json.Unmarshal(line, &e) != nil {
				return nil, errors.New("QUALIFICATION_TRANSCRIPT_INVALID")
			}
			canonical, _ := json.Marshal(e)
			if !bytes.Equal(line, canonical) || e.Schema != EventSchema || e.Phase != phase || e.Case != name || e.Bitmap != 0 {
				return nil, errors.New("QUALIFICATION_TRANSCRIPT_INVALID")
			}
			if j == 0 && (e.Errno != 0 || e.Opened || e.Digest != "" || e.Bytes != 0) {
				return nil, errors.New("QUALIFICATION_TRANSCRIPT_INVALID")
			}
			if j == 1 {
				results[name] = e
			}
		}
	}
	var final Event
	if json.Unmarshal(lines[len(lines)-1], &final) != nil {
		return nil, errors.New("QUALIFICATION_TRANSCRIPT_INCOMPLETE")
	}
	canonical, _ := json.Marshal(final)
	if !bytes.Equal(lines[len(lines)-1], canonical) || final.Schema != EventSchema || final.Phase != "COMPLETE" || final.Case != "" || final.Bitmap != CompleteBitmap || final.Errno != 0 || final.Opened || final.Digest != "" || final.Bytes != 0 {
		return nil, errors.New("QUALIFICATION_TRANSCRIPT_INCOMPLETE")
	}
	return results, nil
}
