package runtimepolicy

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"

	"researchos.local/research-os/internal/canonical"
)

const ProjectionField = "model_execution_projection"
const ProjectionSchema = "researchos.qualification-model-projection.v1"

var markerFields = []string{"schema", "project_id", "task_id", "run_id", "epoch", "runtime_id", "dispatch_key", "task_type", "profile_ref", "profile_hash", "source_profile_body_hash", "source_model_config_hash", "qualification_plan_hash", "permission_hash", "effective_model_config_hash", "policy"}

// Hash uses the same RFC 8785 bytes and sha256 prefix as dispatch manifests.
func Hash(value any) (string, error) {
	raw, err := json.Marshal(value)
	if err != nil {
		return "", err
	}
	canonicalRaw, err := canonical.JSON(raw)
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256(canonicalRaw)
	return "sha256:" + hex.EncodeToString(sum[:]), nil
}

func ownedMap(value map[string]any) (map[string]any, error) {
	raw, err := json.Marshal(value)
	if err != nil {
		return nil, err
	}
	if _, err = canonical.JSON(raw); err != nil {
		return nil, err
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	var copy map[string]any
	if err = decoder.Decode(&copy); err != nil {
		return nil, err
	}
	if copy == nil {
		return nil, errors.New("object required")
	}
	return copy, nil
}

func exactNumber(value any, expected int64) bool {
	switch n := value.(type) {
	case json.Number:
		i, err := n.Int64()
		return err == nil && i == expected
	case int:
		return int64(n) == expected
	case int64:
		return n == expected
	default:
		return false
	}
}

func projectionInput(manifest map[string]any) (map[string]any, map[string]any, map[string]any, map[string]any, error) {
	admission, ok := manifest["admission"].(map[string]any)
	if !ok {
		return nil, nil, nil, nil, errors.New("projection admission missing")
	}
	profile, ok := admission["profile"].(map[string]any)
	if !ok {
		return nil, nil, nil, nil, errors.New("projection profile missing")
	}
	config, ok := profile["model_config"].(map[string]any)
	if !ok {
		return nil, nil, nil, nil, errors.New("projection source config missing")
	}
	permission, ok := admission["permission"].(map[string]any)
	if !ok {
		return nil, nil, nil, nil, errors.New("projection permission missing")
	}
	return admission, profile, config, permission, nil
}

func eligible(manifest map[string]any, taskType string) (map[string]any, error) {
	admission, profile, config, permission, err := projectionInput(manifest)
	if err != nil {
		return nil, err
	}
	if taskType != "runtime_qualification" || admission["qualification_bootstrap"] != true || profile["backend"] != "mu-sdk-broker-v1" || permission["purpose"] != "runtime_qualification" {
		return nil, errors.New("qualification projection authority incomplete")
	}
	if plan, ok := permission["plan_hash"].(string); !ok || plan == "" {
		return nil, errors.New("qualification plan hash missing")
	}
	ref, ok := admission["profile_ref"].(map[string]any)
	if !ok || len(ref) == 0 {
		return nil, errors.New("immutable profile ref missing")
	}
	refHash, err := Hash(ref)
	if err != nil || admission["profile_hash"] != refHash {
		return nil, errors.New("immutable profile ref hash mismatch")
	}
	configHash, err := Hash(config)
	if err != nil {
		return nil, err
	}
	q, ok := profile["model_qualification"].(map[string]any)
	if !ok || len(q) != 3 || q["route"] != config["route"] || q["model_config_hash"] != configHash || !exactNumber(q["max_calls"], 1) {
		return nil, errors.New("qualification must bind original route and one call")
	}
	for _, field := range []string{"project_id", "task_id", "run_id", "runtime_id", "dispatch_key"} {
		if value, ok := manifest[field].(string); !ok || value == "" {
			return nil, fmt.Errorf("projection %s missing", field)
		}
	}
	if !positiveInteger(manifest["epoch"]) {
		return nil, errors.New("projection epoch invalid")
	}
	if _, ok := config["tools"].([]any); !ok || !positiveInteger(config["max_calls"]) {
		return nil, errors.New("source model bounds invalid")
	}
	return config, nil
}

func positiveInteger(v any) bool {
	switch n := v.(type) {
	case json.Number:
		i, e := n.Int64()
		return e == nil && i > 0
	case int:
		return n > 0
	case int64:
		return n > 0
	default:
		return false
	}
}

func projected(config map[string]any) (map[string]any, error) {
	copy, err := ownedMap(config)
	if err != nil {
		return nil, err
	}
	copy["max_calls"] = 1
	copy["tools"] = []any{}
	return copy, nil
}

// Prepare inserts the private marker before the caller hashes or persists the manifest.
// taskType must come from the loaded Task, never from the worker or manifest.
func Prepare(manifest map[string]any, taskType string) error {
	if _, exists := manifest[ProjectionField]; exists {
		return errors.New("projection marker already present")
	}
	admission, profile, config, permission, err := projectionInput(manifest)
	if err != nil {
		partialAdmission, _ := manifest["admission"].(map[string]any)
		partialProfile, _ := partialAdmission["profile"].(map[string]any)
		if taskType == "runtime_qualification" || partialAdmission["qualification_bootstrap"] == true || partialProfile["backend"] == "mu-sdk-broker-v1" {
			return err
		}
		return nil
	}
	wants := taskType == "runtime_qualification" || admission["qualification_bootstrap"] == true || permission["purpose"] == "runtime_qualification"
	if !wants {
		return nil
	}
	if _, err = eligible(manifest, taskType); err != nil {
		return err
	}
	effective, err := projected(config)
	if err != nil {
		return err
	}
	profileHash, err := Hash(profile)
	if err != nil {
		return err
	}
	configHash, err := Hash(config)
	if err != nil {
		return err
	}
	permissionHash, err := Hash(permission)
	if err != nil {
		return err
	}
	effectiveHash, err := Hash(effective)
	if err != nil {
		return err
	}
	ref, err := ownedMap(admission["profile_ref"].(map[string]any))
	if err != nil {
		return err
	}
	manifest[ProjectionField] = map[string]any{"schema": ProjectionSchema, "project_id": manifest["project_id"], "task_id": manifest["task_id"], "run_id": manifest["run_id"], "epoch": manifest["epoch"], "runtime_id": manifest["runtime_id"], "dispatch_key": manifest["dispatch_key"], "task_type": taskType, "profile_ref": ref, "profile_hash": admission["profile_hash"], "source_profile_body_hash": profileHash, "source_model_config_hash": configHash, "qualification_plan_hash": permission["plan_hash"], "permission_hash": permissionHash, "effective_model_config_hash": effectiveHash, "policy": map[string]any{"max_model_calls": 1, "max_tool_calls": 0}}
	return nil
}

// Effective returns an owned configuration. Absence is the explicit legacy path;
// a present but invalid marker can never silently use the original configuration.
func Effective(manifest map[string]any, actualTaskType string) (map[string]any, error) {
	markerValue, exists := manifest[ProjectionField]
	if !exists {
		admission, ok := manifest["admission"].(map[string]any)
		if !ok {
			return nil, errors.New("legacy admission missing")
		}
		profile, ok := admission["profile"].(map[string]any)
		if !ok {
			return nil, errors.New("legacy profile missing")
		}
		config, ok := profile["model_config"].(map[string]any)
		if !ok {
			return nil, errors.New("legacy model config missing")
		}
		return ownedMap(config)
	}
	admission, profile, config, permission, err := projectionInput(manifest)
	if err != nil {
		return nil, err
	}
	marker, ok := markerValue.(map[string]any)
	if !ok || len(marker) != len(markerFields) {
		return nil, errors.New("projection marker field set invalid")
	}
	for _, key := range markerFields {
		if _, ok = marker[key]; !ok {
			return nil, fmt.Errorf("projection marker missing %s", key)
		}
	}
	if marker["schema"] != ProjectionSchema || marker["task_type"] != "runtime_qualification" || (actualTaskType != "" && actualTaskType != "runtime_qualification") {
		return nil, errors.New("projection schema or Task type invalid")
	}
	if _, err = eligible(manifest, "runtime_qualification"); err != nil {
		return nil, err
	}
	for _, key := range []string{"project_id", "task_id", "run_id", "runtime_id", "dispatch_key", "epoch"} {
		h1, e1 := Hash(marker[key])
		h2, e2 := Hash(manifest[key])
		if e1 != nil || e2 != nil || h1 != h2 {
			return nil, fmt.Errorf("projection %s binding mismatch", key)
		}
	}
	refHash, err := Hash(admission["profile_ref"])
	if err != nil {
		return nil, err
	}
	profileHash, err := Hash(profile)
	if err != nil {
		return nil, err
	}
	configHash, err := Hash(config)
	if err != nil {
		return nil, err
	}
	permissionHash, err := Hash(permission)
	if err != nil {
		return nil, err
	}
	refMarkerHash, err := Hash(marker["profile_ref"])
	if err != nil {
		return nil, err
	}
	if refMarkerHash != refHash || marker["profile_hash"] != admission["profile_hash"] || marker["source_profile_body_hash"] != profileHash || marker["source_model_config_hash"] != configHash || marker["qualification_plan_hash"] != permission["plan_hash"] || marker["permission_hash"] != permissionHash {
		return nil, errors.New("projection immutable source binding mismatch")
	}
	policy, ok := marker["policy"].(map[string]any)
	if !ok || len(policy) != 2 || !exactNumber(policy["max_model_calls"], 1) || !exactNumber(policy["max_tool_calls"], 0) {
		return nil, errors.New("projection policy invalid")
	}
	effective, err := projected(config)
	if err != nil {
		return nil, err
	}
	effectiveHash, err := Hash(effective)
	if err != nil {
		return nil, err
	}
	if marker["effective_model_config_hash"] != effectiveHash {
		return nil, errors.New("projection effective config hash mismatch")
	}
	return effective, nil
}
