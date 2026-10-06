package domain

import (
	"bytes"
	"database/sql"
	_ "embed"
)

const projectRulesPath = "15_NEW_PROJECT_WORKFLOW.md"
const projectRulesHash = "sha256:b81a28161c9115f3290a9e61e0460d22a516e168071965efd9692a0d45dc2497"
const projectRulesMetadataHash = "sha256:55d7a4d89db2c91970d5b5312ff6516d494bc8f940eb3a7217078f4943aca3bd"

// These bytes are the root-owned frozen package projection. No request or
// environment value selects either the rules or the policy that installs them.
//
//go:embed contracts/new-project-rules-v24.md
var projectRulesBytes []byte

//go:embed contracts/new-project-rules-v24.json
var projectRulesMetadata []byte

func validateProjectRules(raw, metadata []byte) error {
	if len(raw) != 12952 || Digest(raw) != projectRulesHash || Digest(metadata) != projectRulesMetadataHash {
		return Fail(422, "CONTENT_HASH_MISMATCH", "fixed project rules bytes or provenance changed")
	}
	m, err := Decode(metadata)
	if err != nil {
		return err
	}
	if len(m) != 7 || Str(m, "schema") != "researchos.embedded-project-rules-source.v1" ||
		Str(m, "source_path") != projectRulesPath || Str(m, "rules_version") != "1.1" ||
		Str(m, "package_version") != "2.4.0" || Str(m, "package_manifest_sha256") != "4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964" ||
		"sha256:"+Str(m, "sha256") != projectRulesHash {
		return Fail(422, "CONTENT_HASH_MISMATCH", "fixed project rules provenance differs")
	}
	size, err := Num(m, "size_bytes")
	if err != nil || size != int64(len(raw)) {
		return Fail(422, "CONTENT_HASH_MISMATCH", "fixed project rules size differs")
	}
	return nil
}

func (s *Service) installCurrentProjectRules(tx *sql.Tx, p Principal, profile, state Object) error {
	if s.projectBindingRoute != "MU_FORK" {
		return nil
	}
	if err := validateProjectRules(projectRulesBytes, projectRulesMetadata); err != nil {
		return err
	}
	project := Str(profile, "id")
	artifact, err := s.serverArtifactMode(tx, project, p.ID, "SOURCE_SNAPSHOT", "FIXTURE", projectRulesBytes, Empty())
	if err != nil {
		return err
	}
	profile["source_document_refs"] = append(Arr(profile, "source_document_refs"), Ref(artifact, "Artifact"))
	if err = bump(profile); err != nil {
		return err
	}
	if err = s.put(tx, "ProjectProfile", profile); err != nil {
		return err
	}
	state["profile_revision"] = profile["revision"]
	if err = bump(state); err != nil {
		return err
	}
	return s.put(tx, "ProjectState", state)
}

// Only the exact installed document may reuse its existing project-owned
// sealed artifact. A different caller-pinned document remains imported source.
func (s *Service) importedProjectRules(tx *sql.Tx, project string, profile Object, file importFile) (Object, error) {
	if s.projectBindingRoute != "MU_FORK" || file.path != projectRulesPath || !bytes.Equal(file.raw, projectRulesBytes) {
		return nil, nil
	}
	for _, rawRef := range Arr(profile, "source_document_refs") {
		ref, ok := rawRef.(map[string]any)
		if !ok || Str(ref, "entity_type") != "Artifact" || Str(ref, "content_hash") != projectRulesHash {
			continue
		}
		artifact, err := version(tx, project, ref)
		if err != nil {
			return nil, err
		}
		size, err := Num(artifact, "byte_size")
		if err != nil || size != int64(len(file.raw)) || Str(artifact, "project_id") != project ||
			Str(artifact, "kind") != "SOURCE_SNAPSHOT" || Str(artifact, "access_class") != "PROJECT" ||
			Str(artifact, "content_hash") != projectRulesHash || Str(artifact, "sealed_at") == "" {
			return nil, Fail(422, "CONTENT_HASH_MISMATCH", "installed project rule artifact differs")
		}
		var stored []byte
		if err = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, artifact["storage_key"]).Scan(&stored); err != nil {
			return nil, err
		}
		if !bytes.Equal(stored, file.raw) || Digest(stored) != projectRulesHash {
			return nil, Fail(422, "CONTENT_HASH_MISMATCH", "installed project rule original differs")
		}
		return artifact, nil
	}
	return nil, Fail(422, "GATE_FAILED", "current project rule reference missing during import")
}
