package domain

import (
	_ "embed"

	"github.com/santhosh-tekuri/jsonschema/v6"
)

// evaluationV24Schema is the exact transitive definition closure from the frozen
// v2.4 EvaluationReport. Its source hash is carried in x-source. Embedding keeps
// installed hosts independent of the construction checkout's spec directory.
//
//go:embed contracts/evaluation-v24.schema.json
var evaluationV24Schema []byte

func (c *Contracts) bindEvaluationV24() error {
	doc, err := Decode(evaluationV24Schema)
	if err != nil {
		return err
	}
	compiler := jsonschema.NewCompiler()
	compiler.UseLoader(localOnly{})
	compiler.AssertFormat()
	compiler.DefaultDraft(jsonschema.Draft2020)
	const location = "https://researchos.invalid/evaluation-v24.schema.json"
	if err = compiler.AddResource(location, doc); err != nil {
		return err
	}
	schema, err := compiler.Compile(location)
	if err != nil {
		return err
	}
	c.Schemas["EvaluationReportV24"] = schema
	return nil
}
