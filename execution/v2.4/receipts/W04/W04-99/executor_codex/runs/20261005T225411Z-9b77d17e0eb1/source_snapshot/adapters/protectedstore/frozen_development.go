package protectedstore

import (
	_ "embed"
	"encoding/json"
	"researchos.local/research-os/adapters/decision"
	holdout "researchos.local/research-os/evaluation/holdout/jev"
)

const frozenDevelopmentHash = "sha256:da21a2d4b62a73cf18ef8fd17df84c9059f66da1b3ed88bf0c05b476dde4979a"

//go:embed frozen_development.json
var frozenDevelopmentRaw []byte

type FrozenDevelopmentCounts struct {
	Count               int64            `json:"development_count"`
	Correct             int64            `json:"correct_count"`
	FalseAccept         int64            `json:"false_accept_count"`
	FalseReject         int64            `json:"false_reject_count"`
	Abstain             int64            `json:"abstain_count"`
	CriticalFalseAccept int64            `json:"critical_false_accept_count"`
	AcceptCoverage      int64            `json:"nonabstained_accept_count"`
	RawChoices          map[string]int64 `json:"raw_choice_counts"`
}

func frozenDevelopment(language string) (FrozenDevelopmentCounts, error) {
	var doc struct {
		Rubric    string  `json:"rubric_sha256"`
		Threshold float64 `json:"threshold"`
		Keys      []struct {
			Scope   decision.Scope          `json:"qualification_key"`
			Metrics FrozenDevelopmentCounts `json:"metrics"`
		} `json:"keys"`
	}
	if decision.Digest(frozenDevelopmentRaw) != frozenDevelopmentHash || json.Unmarshal(frozenDevelopmentRaw, &doc) != nil || doc.Rubric != holdout.RubricHash() || doc.Threshold != holdout.Threshold || len(doc.Keys) != 2 {
		return FrozenDevelopmentCounts{}, ErrIntegrity
	}
	for _, key := range doc.Keys {
		if key.Scope == holdout.ScopeFor(language) {
			return key.Metrics, nil
		}
	}
	return FrozenDevelopmentCounts{}, ErrIntegrity
}
