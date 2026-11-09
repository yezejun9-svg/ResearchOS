package host

import "researchos.local/research-os/internal/domain"

// schemaDocument is the pinned contract view the host needs; it is the same loaded document the
// protocol qualification grades, so the bridge and the protocol cannot drift apart.
type schemaDocument interface {
	ValidateDef(name string, value any) error
	ValidateDefInput(name string, value any) error
}

func newSchemaDocument(protocol, external []byte) (schemaDocument, error) {
	return domain.LoadSchemaWithExternals(protocol, map[string][]byte{"domain.schema.json": external})
}
