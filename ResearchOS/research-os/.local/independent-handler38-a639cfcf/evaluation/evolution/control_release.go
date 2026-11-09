package evolution

import "fmt"

// Exact reviewed schema20 release. New protocol support needs a new reviewed
// profile; a candidate cannot replace SQL, contracts or replay interpretation.
var controlReleaseHashes = map[string]string{
	"migrations/sqlite/0001_bootstrap.sql":                    "sha256:bb87c889e31fd5412b49743d106679f783b6dd21d874fe29d82d18a729ce3dbc",
	"migrations/sqlite/0002_domain.sql":                       "sha256:90d6c36100cbfaddf85c23f603b686336d161e43eeeed47c034ab85415b25db4",
	"migrations/sqlite/0003_context.sql":                      "sha256:50aa1579e4233cbb64ac30777e27c55cba29bab7ee0cc221a677f9a420a7159a",
	"migrations/sqlite/0004_sources.sql":                      "sha256:d40152642778d8ea4e21148fd6517bdc8bf4c2582a8d6212b8cfdf7a470dea06",
	"migrations/sqlite/0005_runtime.sql":                      "sha256:f3b9cd4c03f101c22c47a4fd7ad72593babe69de9abcd8a1ee3056fa6c23ade5",
	"migrations/sqlite/0006_orchestration.sql":                "sha256:cbc9ede2d2e46e1e68ac7120d2a99b29627f2e13b1fc82937e3ed13ac9b2317b",
	"migrations/sqlite/0007_retrieval.sql":                    "sha256:eaa3963a3acdfcc1791982432c42dea9d4dd8f0baf7de51d278fce70bcd626bb",
	"migrations/sqlite/0008_artifact_uses.sql":                "sha256:adf17ad69203f0e700897a426f2d596496081bd5f3a964cbea8e3db9fc561ee7",
	"migrations/sqlite/0009_retrieval_root_identity.sql":      "sha256:48219da409abc3f9d353e8d91a71a387ea342e5c13aae711a36c28410b22fb4f",
	"migrations/sqlite/0010_experiments.sql":                  "sha256:c197ff792f62a1be5903bb6967175512cb53bdb09ff276e06fa8542822024287",
	"migrations/sqlite/0011_resources.sql":                    "sha256:45c082ae0980af14f5b0be2d5aae02622dcc15c8c566b442077b4c1fb0c9942b",
	"migrations/sqlite/0012_experiment_execution.sql":         "sha256:c81411769ef2bd3ec1d101f311ce37722036485b8e9d99d45ae9c9be48f088c0",
	"migrations/sqlite/0013_research_cycles.sql":              "sha256:188e0d6fbcffd3901d36109dcd421a21f7ef704574f62cd5c0f8af862c191d1e",
	"migrations/sqlite/0014_remote_access.sql":                "sha256:687b01552260301a8f3f39e92422f16d0b2e310b38f77d1b025566f9a9cfa4d7",
	"migrations/sqlite/0015_evolution_fixture.sql":            "sha256:d70dd0580e89e2a7940c90ee771b2bd94551a42d8cda7fadfe83b60509852fe9",
	"migrations/sqlite/0016_runtime_qualification.sql":        "sha256:7fd44c42be4c0753c367fc8361e9990b56e4f9a001a5f443ef62d0d87d05a03f",
	"migrations/sqlite/0017_runtime_dispatch.sql":             "sha256:e5a2671c25725205bb5306c7fcbab254d53e3ef7a0448a163a41c5ac24a7b558",
	"migrations/sqlite/0018_intent_planning.sql":              "sha256:7592b2b47d2e305f9ec26937830b5c0606c7d90622401a0b6b80a8c8a67db4e0",
	"migrations/sqlite/0019_evolution_release_operations.sql": "sha256:54ff6eb7a7ca588df738f5bd68b6f6851d86916cef435abaac15d1f8bd6e131e",
	"migrations/sqlite/0020_research_cycle_work.sql":          "sha256:3f90bdb0e828cec90bc370f34abed0cf0629dc78dcc01dda250c18cda49e528a",
	"spec/v2.0/contracts/domain.schema.json":                  "sha256:b11439c80d15c9481d7940c98eb6517b5156470f871c839e505a8dce40e0b847",
	"spec/v2.0/contracts/openapi.json":                        "sha256:f1edd7955a1d134a675c5558618756db809d82729f8eebe622a9bc2605a58920",
}

func ControlReleaseHashes() map[string]string {
	out := map[string]string{}
	for name, hash := range controlReleaseHashes {
		out[name] = hash
	}
	return out
}
func (b ControlBundle) Validate() error {
	if err := b.Binding.Validate(); err != nil {
		return err
	}
	if len(b.Files) != len(controlReleaseHashes)+1 {
		return fmt.Errorf("CONTROL_RELEASE_FILES")
	}
	if b.Binding.ReleaseHash != Digest(Bytes(controlReleaseHashes)) {
		return fmt.Errorf("CONTROL_RELEASE_HASH")
	}
	for name, hash := range controlReleaseHashes {
		if Digest(b.Files[name]) != hash {
			return fmt.Errorf("CONTROL_RELEASE_FILE: %s", name)
		}
	}
	database := b.Files["snapshot.sqlite"]
	if len(database) < 16 || len(database) > 32*1024*1024 || string(database[:16]) != "SQLite format 3\x00" || Digest(database) != b.Binding.SnapshotHash {
		return fmt.Errorf("CONTROL_SNAPSHOT_BYTES")
	}
	return nil
}
