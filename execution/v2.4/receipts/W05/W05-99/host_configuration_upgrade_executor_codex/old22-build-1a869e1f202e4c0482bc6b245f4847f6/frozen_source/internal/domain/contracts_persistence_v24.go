package domain

import (
	_ "embed"
	"fmt"
	"strings"

	"github.com/santhosh-tekuri/jsonschema/v6"
)

// The root-owned projection is the unchanged frozen five-root definition
// closure. It adds validation choices, not entities or a new lifecycle.
//
//go:embed contracts/persistence-v24.schema.json
var persistenceV24Schema []byte

const persistenceV24Location = "https://researchos.invalid/persistence-v24.schema.json"

func persistenceSchemaName(name string, value any) (string, error) {
	switch name {
	case "ProjectBinding", "ProjectState", "Goal", "Task", "EvaluationSummary":
	default:
		return name, nil
	}
	o, ok := value.(map[string]any)
	if !ok {
		return "", fmt.Errorf("%s must be an object", name)
	}
	if name == "EvaluationSummary" {
		switch o["schema_version"] {
		case "2.0.0":
			return name, nil
		case "2.4.0":
			return name + "V24", nil
		default:
			return "", fmt.Errorf("unsupported EvaluationSummary schema_version")
		}
	}
	binding := o
	if name != "ProjectBinding" {
		binding, ok = o["binding"].(map[string]any)
		if !ok {
			return "", fmt.Errorf("%s binding must be an object", name)
		}
	}
	switch binding["route"] {
	case "PAPERCLIP", "THIN_CORE":
		return name, nil
	case "MU_FORK", "PI_COMPOSE", "GAP_ONLY_COMPOSE":
		return name + "V24", nil
	default:
		return "", fmt.Errorf("%s binding route is missing or unsupported", name)
	}
}

func (c *Contracts) bindPersistenceV24(compiler *jsonschema.Compiler, domainDoc, apiDoc Object) error {
	current, err := Decode(persistenceV24Schema)
	if err != nil {
		return err
	}
	if err = compiler.AddResource(persistenceV24Location, current); err != nil {
		return err
	}
	for _, name := range []string{"ProjectBinding", "ProjectState", "Goal", "Task", "EvaluationSummary"} {
		schema, err := compiler.Compile(persistenceV24Location + "#/$defs/" + name)
		if err != nil {
			return err
		}
		c.Schemas[name+"V24"] = schema
	}
	// A caller loading the actual current frozen document already has strict
	// current pages. Do not make identical oneOf alternatives reject that input.
	if Hash(domainDoc["$defs"].(map[string]any)["ProjectBinding"]) == Hash(current["$defs"].(map[string]any)["ProjectBinding"]) {
		return nil
	}
	// Preserve the entire original outer schema. Only the complete nested
	// aggregate becomes a strict legacy/current oneOf; malformed items never
	// fall through to a relaxed object or an unchecked array.
	components := apiDoc["components"].(map[string]any)["schemas"].(map[string]any)
	for _, kind := range []string{"Goal", "Task"} {
		name := kind + "Page"
		page, err := Decode(Bytes(components[name]))
		if err != nil {
			return err
		}
		absolutizeContractRefs(page, "https://researchos.invalid/openapi.json")
		items := page["properties"].(map[string]any)["items"].(map[string]any)
		items["items"] = Object{"oneOf": []any{items["items"], Object{"$ref": persistenceV24Location + "#/$defs/" + kind}}}
		if err = c.compilePersistenceEnvelope(compiler, name, page); err != nil {
			return err
		}
	}
	claim, err := Decode(Bytes(domainDoc["$defs"].(map[string]any)["TaskClaimResponse"]))
	if err != nil {
		return err
	}
	absolutizeContractRefs(claim, "https://researchos.invalid/domain.schema.json")
	properties := claim["properties"].(map[string]any)
	properties["task"] = Object{"oneOf": []any{properties["task"], Object{"$ref": persistenceV24Location + "#/$defs/Task"}}}
	return c.compilePersistenceEnvelope(compiler, "TaskClaimResponse", claim)
}

func (c *Contracts) compilePersistenceEnvelope(compiler *jsonschema.Compiler, name string, doc Object) error {
	location := "https://researchos.invalid/persistence-compat-" + name + ".schema.json"
	if err := compiler.AddResource(location, doc); err != nil {
		return err
	}
	schema, err := compiler.Compile(location)
	if err != nil {
		return err
	}
	c.Schemas[name] = schema
	return nil
}

// Isolated copies of the original envelopes keep their original reference base.
func absolutizeContractRefs(value any, origin string) {
	switch v := value.(type) {
	case map[string]any:
		if ref, ok := v["$ref"].(string); ok && strings.HasPrefix(ref, "#") {
			v["$ref"] = origin + ref
		}
		for _, child := range v {
			absolutizeContractRefs(child, origin)
		}
	case []any:
		for _, child := range v {
			absolutizeContractRefs(child, origin)
		}
	}
}
