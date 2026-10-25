package qualificationmaintenancejournal

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"strings"

	"researchos.local/research-os/internal/canonical"
)

const (
	QualificationNamespace = "qualification-failure-maintenance"
	ReplacementNamespace   = "runtime-verifier-replacements"
)

// InspectionPermit is intentionally usable only for discovery of one pending
// transition. It never authorizes a write, a process action, or normal startup.
type InspectionPermit struct {
	root            string
	namespace       string
	operation       string
	planDigest      string
	replacementPlan []byte
}

type HistoryStatus struct {
	Namespace  string
	Operation  string
	PlanDigest string
	State      string
	Terminal   bool
	Applied    bool
}

func digest(raw []byte) string {
	hash := sha256.Sum256(raw)
	return "sha256:" + hex.EncodeToString(hash[:])
}

func validDigest(value string) bool {
	if len(value) != 71 || !strings.HasPrefix(value, "sha256:") {
		return false
	}
	raw, err := hex.DecodeString(value[7:])
	return err == nil && len(raw) == 32 && value == strings.ToLower(value)
}

func validOperation(value string) bool {
	if len(value) != 32 || value != strings.ToLower(value) {
		return false
	}
	raw, err := hex.DecodeString(value)
	return err == nil && len(raw) == 16
}

func strictJSON(raw []byte, out any) error {
	if len(raw) == 0 || len(raw) > 256<<10 {
		return errors.New("maintenance JSON bound")
	}
	normalized, err := canonical.JSON(raw)
	if err != nil {
		return err
	}
	decoder := json.NewDecoder(strings.NewReader(string(normalized)))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(out); err != nil {
		return err
	}
	var trailing any
	if decoder.Decode(&trailing) != io.EOF {
		return errors.New("maintenance JSON trailing data")
	}
	return nil
}

func hash(value any) (string, error) {
	raw, err := json.Marshal(value)
	if err != nil {
		return "", err
	}
	canonicalRaw, err := canonical.JSON(raw)
	if err != nil {
		return "", err
	}
	return digest(canonicalRaw), nil
}
