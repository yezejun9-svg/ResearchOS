package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

const actualEvidenceDirectory = "D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/root-model-trial-v5-870ecc93e109c85ee985e1566ff/trial-output"

func pinnedTestJSON(t *testing.T, raw []byte) pinnedFile {
	t.Helper()
	p := filepath.Join(t.TempDir(), "evidence.json")
	if err := os.WriteFile(p, raw, 0600); err != nil {
		t.Fatal(err)
	}
	return pinnedFile{Path: p, SHA256: hashBytes(raw), Bytes: int64(len(raw))}
}

func TestActualOwnedJobEvidenceKeepsFILETIME(t *testing.T) {
	for _, name := range []string{"host-job.contract.json", "host-job.probe.json"} {
		t.Run(name, func(t *testing.T) {
			raw, err := os.ReadFile(filepath.Join(actualEvidenceDirectory, name))
			if err != nil {
				t.Fatal(err)
			}
			pin := pinnedTestJSON(t, raw)
			if _, err = readPinnedObject(pin); err == nil || !strings.Contains(err.Error(), "not losslessly representable") {
				t.Fatalf("strict general reader did not reject observed unsafe integer: %v", err)
			}
			object, err := readPinnedOwnedJobObject(pin)
			if err != nil {
				t.Fatal(err)
			}
			identity, ok := object["held_identity"].(map[string]any)
			if !ok {
				t.Fatal("held identity missing")
			}
			if identity["creation_time_100ns"] != "134359521876434319" {
				t.Fatalf("FILETIME changed: %#v", identity["creation_time_100ns"])
			}
			var original map[string]any
			d := json.NewDecoder(bytes.NewReader(raw))
			d.UseNumber()
			if err = d.Decode(&original); err != nil {
				t.Fatal(err)
			}
			for _, key := range []string{"schema", "root_job_id", "host_pid", "root_pid", "deadline_utc", "in_job", "descendant_of_root"} {
				left, _ := json.Marshal(object[key])
				right, _ := json.Marshal(original[key])
				if !bytes.Equal(left, right) {
					t.Errorf("%s changed: %s / %s", key, left, right)
				}
			}
		})
	}
}

func TestOwnedJobReaderRejectsInvalidOrUnrelatedNumbers(t *testing.T) {
	template := `{"schema":"researchos.mu-trial-host-job.v1","host_pid":123,"root_job_id":"owned","held_identity":{"creation_time_100ns":FILETIME}}`
	for _, lexeme := range []string{"0", "-1", "1.5", "1e2", `"134359521876434319"`, "true", "null", "18446744073709551616"} {
		t.Run("invalid_FILETIME_"+lexeme, func(t *testing.T) {
			raw := []byte(strings.Replace(template, "FILETIME", lexeme, 1))
			if _, err := readPinnedOwnedJobObject(pinnedTestJSON(t, raw)); err == nil {
				t.Fatal("invalid FILETIME accepted")
			}
		})
	}
	cases := map[string]string{
		"missing_identity":            `{"schema":"researchos.mu-trial-host-job.v1","host_pid":123}`,
		"wrong_identity_type":         `{"schema":"researchos.mu-trial-host-job.v1","held_identity":true}`,
		"missing_FILETIME":            `{"schema":"researchos.mu-trial-host-job.v1","held_identity":{}}`,
		"unknown_schema":              strings.Replace(strings.Replace(template, "FILETIME", "134359521876434319", 1), "researchos.mu-trial-host-job.v1", "unknown", 1),
		"duplicate_schema":            `{"schema":"researchos.mu-trial-host-job.v1","schema":"researchos.mu-trial-host-job.v1","held_identity":{"creation_time_100ns":134359521876434319}}`,
		"duplicate_FILETIME":          `{"schema":"researchos.mu-trial-host-job.v1","held_identity":{"creation_time_100ns":1,"creation_time_100ns":134359521876434319}}`,
		"lossy_other_identity_number": `{"schema":"researchos.mu-trial-host-job.v1","held_identity":{"creation_time_100ns":134359521876434319,"other":134359521876434319}}`,
		"lossy_host_pid":              `{"schema":"researchos.mu-trial-host-job.v1","host_pid":134359521876434319,"held_identity":{"creation_time_100ns":134359521876434319}}`,
		"trailing_object":             strings.Replace(template, "FILETIME", "134359521876434319", 1) + `{}`,
		"unpaired_surrogate":          `{"schema":"researchos.mu-trial-host-job.v1","text":"\ud800","held_identity":{"creation_time_100ns":134359521876434319}}`,
	}
	for label, raw := range cases {
		t.Run(label, func(t *testing.T) {
			if _, err := readPinnedOwnedJobObject(pinnedTestJSON(t, []byte(raw))); err == nil {
				t.Fatal("invalid evidence accepted")
			}
		})
	}
	for _, lexeme := range []string{"1", "134359521876434319", "18446744073709551615"} {
		t.Run("positive_"+lexeme, func(t *testing.T) {
			object, err := readPinnedOwnedJobObject(pinnedTestJSON(t, []byte(strings.Replace(template, "FILETIME", lexeme, 1))))
			if err != nil {
				t.Fatal(err)
			}
			if object["held_identity"].(map[string]any)["creation_time_100ns"] != lexeme {
				t.Fatal("integer bits changed")
			}
		})
	}
	t.Run("wrong_hash", func(t *testing.T) {
		pin := pinnedTestJSON(t, []byte(strings.Replace(template, "FILETIME", "134359521876434319", 1)))
		pin.SHA256 = strings.Repeat("0", 64)
		if _, err := readPinnedOwnedJobObject(pin); err == nil {
			t.Fatal("wrong hash accepted")
		}
	})
	t.Run("wrong_size", func(t *testing.T) {
		pin := pinnedTestJSON(t, []byte(strings.Replace(template, "FILETIME", "134359521876434319", 1)))
		pin.Bytes++
		if _, err := readPinnedOwnedJobObject(pin); err == nil {
			t.Fatal("wrong size accepted")
		}
	})
}
