package qualificationprobe

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"path/filepath"
	"testing"
)

func fixturePlan(t *testing.T) Plan {
	t.Helper()
	root := t.TempDir()
	return Plan{Schema: Schema, Source: filepath.Join(root, "S"), Working: filepath.Join(root, "QW"), Denied: filepath.Join(root, "D"), Nonce: "researchos-readonly-0123456789abcdef0123456789abcdef", Port: 12345, Cases: FixedCases()}
}
func TestFixedPlanRejectsCallerAlternates(t *testing.T) {
	p := fixturePlan(t)
	encoded, err := Encode(p)
	if err != nil {
		t.Fatal(err)
	}
	if got, err := Decode(encoded); err != nil || got.Source != p.Source {
		t.Fatal("canonical fixed plan rejected", err)
	}
	for _, change := range []func(*Plan){func(v *Plan) { v.Source = filepath.Join(t.TempDir(), "user-project") }, func(v *Plan) { v.Working = v.Source }, func(v *Plan) { v.Cases[0] = "generic_command" }, func(v *Plan) { v.Nonce = "fixed" }, func(v *Plan) { v.Port = 0 }} {
		q := p
		q.Cases = FixedCases()
		change(&q)
		if _, err := Encode(q); err == nil {
			t.Fatal("alternate plan accepted", q)
		}
	}
	raw, _ := json.Marshal(p)
	duplicate := bytes.Replace(raw, []byte(`"port":12345`), []byte(`"port":12345,"port":12345`), 1)
	if _, err := Decode(base64.RawURLEncoding.EncodeToString(duplicate)); err == nil {
		t.Fatal("duplicate plan key accepted")
	}
}
func TestTranscriptRequiresOrderedCompleteBitmap(t *testing.T) {
	rows := make([][]byte, 0, 2*len(Cases)+1)
	for _, name := range Cases {
		for _, phase := range []string{"START", "RESULT"} {
			raw, _ := json.Marshal(Event{Schema: EventSchema, Phase: phase, Case: name})
			rows = append(rows, raw)
		}
	}
	complete, _ := json.Marshal(Event{Schema: EventSchema, Phase: "COMPLETE", Bitmap: CompleteBitmap})
	rows = append(rows, complete)
	raw := append(bytes.Join(rows, []byte{'\n'}), '\n')
	if got, err := ParseTranscript(raw); err != nil || len(got) != len(Cases) {
		t.Fatal("complete canonical transcript rejected", err)
	}
	for _, bad := range [][]byte{raw[:len(raw)-1], append([]byte(nil), raw[:len(raw)-len(complete)-1]...), bytes.Replace(raw, []byte(`"bitmap":127`), []byte(`"bitmap":126`), 1), bytes.Replace(raw, []byte(`"phase":"START"`), []byte(`"phase":"RESULT"`), 1), append(raw, []byte("junk\n")...)} {
		if _, err := ParseTranscript(bad); err == nil {
			t.Fatal("incomplete/duplicate transcript accepted")
		}
	}
}
