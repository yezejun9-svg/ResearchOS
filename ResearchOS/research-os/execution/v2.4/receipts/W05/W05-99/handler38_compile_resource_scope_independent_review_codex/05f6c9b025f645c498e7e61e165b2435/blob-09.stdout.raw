package jev

import (
	"math/big"
	"regexp"
	"strconv"
	"strings"
	"time"

	"researchos.local/research-os/adapters/decision"
)

// Truth is private verifier evidence, never part of the candidate Request.
type Truth struct {
	Expected string       `json:"expected"`
	Critical bool         `json:"critical"`
	Checks   []TruthCheck `json:"checks"`
}
type TruthCheck struct {
	Name string `json:"name"`
	Pass bool   `json:"pass"`
}

var decimalPattern = regexp.MustCompile(`^(0|[1-9][0-9]{0,8})(\.[0-9]{1,6})?$`)

func decimal(s string) (*big.Rat, bool) {
	if !decimalPattern.MatchString(s) {
		return nil, false
	}
	r, ok := new(big.Rat).SetString(s)
	return r, ok
}

// Recompute reads original fields, never Expected, Critical, TruthHash, prior
// model output or asserted validity flags. Notes are not parsed as commands.
func Recompute(c Case) (Truth, error) {
	if !c.Scope.Valid() || (c.Scope.Language != "zh" && c.Scope.Language != "zh-en") || c.Scope != ScopeFor(c.Scope.Language) || c.Request.Model != ModelRevision || c.Request.Validate() != nil || decision.Digest(decision.Encode(c.Request.Questions)) != decision.Digest(decision.Encode(Questions())) {
		return Truth{}, ErrCorpus
	}
	var state sourceState
	if decision.Strict(decision.Encode(c.Request.State), &state) != nil {
		return Truth{}, ErrCorpus
	}
	if decision.Digest(decision.Encode(state.TaskRules)) != decision.Digest(decision.Encode(rules(state.RuleID, c.Scope.Language))) {
		return Truth{}, ErrCorpus
	}
	truth := Truth{Expected: "ACCEPT", Checks: make([]TruthCheck, 0, 4)}
	check := func(name string, pass bool) {
		truth.Checks = append(truth.Checks, TruthCheck{name, pass})
		if !pass {
			truth.Expected = "REJECT"
			truth.Critical = true
		}
	}
	docs := map[string]sourceDocument{}
	validDocs := len(state.SourceDocuments) > 0
	for _, d := range state.SourceDocuments {
		if d.ID == "" || strings.TrimSpace(d.Body) == "" {
			validDocs = false
		}
		if _, exists := docs[d.ID]; exists {
			validDocs = false
		}
		docs[d.ID] = d
	}
	check("original_documents_present_unique", validDocs)
	validCitations := len(state.Citations) > 0
	for _, citation := range state.Citations {
		d, ok := docs[citation.DocumentID]
		if !ok || strings.TrimSpace(d.Body) == "" {
			validCitations = false
		}
	}
	check("all_citations_resolve", validCitations)
	var first sourceDocument
	if len(state.Citations) > 0 {
		first = docs[state.Citations[0].DocumentID]
	}
	values := state.Claim.Values
	switch state.RuleID {
	case "calendar-elapsed":
		start, e1 := time.Parse("2006-01-02", first.Record["date_start"])
		end, e2 := time.Parse("2006-01-02", first.Record["date_end"])
		days, e3 := strconv.ParseInt(values["elapsed_days"], 10, 32)
		valid := e1 == nil && e2 == nil && e3 == nil && start.Year() >= 1 && end.Year() >= 1 && !end.Before(start) && start.Format("2006-01-02") == first.Record["date_start"] && end.Format("2006-01-02") == first.Record["date_end"]
		check("calendar_dates_valid_ordered", valid)
		check("elapsed_days_recomputed", valid && (end.Unix()-start.Unix())/86400 == days)
	case "planar-area":
		length, lok := decimal(first.Record["length_mm"])
		width, wok := decimal(first.Record["width_cm"])
		area, aok := decimal(values["area"])
		valid := lok && wok && aok && length.Sign() > 0 && width.Sign() > 0 && values["unit"] == "cm2"
		check("positive_dimensions_and_unit", valid)
		correct := false
		if valid {
			expected := new(big.Rat).Quo(new(big.Rat).Mul(length, width), big.NewRat(10, 1))
			correct = expected.Cmp(area) == 0
		}
		check("exact_rational_area", correct)
	case "quoted-catalog":
		correct := len(state.Citations) == 1 && state.Citations[0].Quote != "" && state.Citations[0].Quote == values["quoted_fact"] && strings.Contains(first.Body, state.Citations[0].Quote)
		check("quote_occurs_in_named_original", correct)
	case "fact-consistency":
		entity, attribute, value := values["entity"], values["attribute"], values["value"]
		count, agrees := 0, true
		for _, d := range state.SourceDocuments {
			if d.Record["entity"] == entity && d.Record["attribute"] == attribute {
				count++
				if d.Record["value"] != value {
					agrees = false
				}
			}
		}
		check("matching_fact_present", entity != "" && attribute != "" && value != "" && count > 0)
		check("all_relevant_facts_agree", count > 0 && agrees)
	case "instruction-boundary":
		check("catalog_fact_matches_despite_instructions", values["catalog_code"] != "" && first.Record["catalog_code"] == values["catalog_code"])
	default:
		return Truth{}, ErrCorpus
	}
	return truth, nil
}

func truthHash(c Case, t Truth) string {
	return decision.Digest(decision.Encode(map[string]any{"scope": c.Scope, "request_hash": decision.Digest(decision.Encode(c.Request)), "rubric_hash": RubricHash(), "truth": t, "generator_revision": GeneratorRevision}))
}
