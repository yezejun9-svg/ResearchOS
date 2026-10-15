package runtime

import (
	"encoding/json"
	"errors"

	"researchos.local/research-os/internal/runtimepolicy"
)

// Mu uses a staged, immutable bundle and configuration. Freezing Node alone
// would attest every script which that executable could load.
func validateBridgeProgram(manifest map[string]any, inputs map[string][]byte) error {
	admission, _ := manifest["admission"].(map[string]any)
	profile, _ := admission["profile"].(map[string]any)
	if profile["backend"] == "native-offline" && profile["model"] == "none" {
		if _, exists := manifest[runtimepolicy.ProjectionField]; exists {
			return errors.New("non-Mu dispatch carries model projection")
		}
		return nil
	}
	if profile["backend"] != "mu-sdk-broker-v1" || profile["model"] == "" || profile["model"] == "none" {
		return errors.New("host cannot attest requested backend/model identity")
	}
	bundle := inputs["mu-worker.mjs"]
	if len(bundle) == 0 || Hash(bundle) != profile["bundle_hash"] {
		return errors.New("Mu bundle differs from frozen build")
	}
	var config map[string]any
	if err := json.Unmarshal(inputs["worker.json"], &config); err != nil || config == nil {
		return errors.New("immutable Mu worker configuration required")
	}
	effective, err := runtimepolicy.Effective(manifest, "")
	if err != nil {
		return err
	}
	want, err := json.Marshal(effective)
	if err != nil || Hash(inputs["worker.json"]) != Hash(want) {
		return errors.New("Mu worker configuration differs from immutable projection")
	}
	if config["model"] != profile["model"] || config["api"] != "openai-completions" {
		return errors.New("unsupported Mu model adapter")
	}
	argv, err := json.Marshal(profile["argv"])
	if err != nil || string(argv) != `["--preserve-symlinks-main","--preserve-symlinks","{bundle}","{manifest}"]` {
		return errors.New("Mu requires the frozen sandbox argument vector")
	}
	return nil
}
