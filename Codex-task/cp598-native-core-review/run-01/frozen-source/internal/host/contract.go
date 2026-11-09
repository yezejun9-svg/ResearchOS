package host

// Pinned contract grading for native frames. The bridge is not allowed its own dialect: the same
// published definitions the protocol qualification uses decide whether a request payload or a
// reply is acceptable, and replies are graded in READ direction so a credential field cannot
// physically leave the host even if a handler were changed to add one.

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// loadSchema pins client.protocol.schema.json plus the cross-file schema it references.
func loadSchema(dir string) (schemaDocument, error) {
	proto, err := os.ReadFile(filepath.Join(dir, "client.protocol.schema.json"))
	if err != nil {
		return nil, fmt.Errorf("host contract unavailable: %w", err)
	}
	ext, err := os.ReadFile(filepath.Join(dir, "domain.schema.json"))
	if err != nil {
		return nil, fmt.Errorf("host contract dependency unavailable: %w", err)
	}
	doc, err := newSchemaDocument(proto, ext)
	if err != nil {
		return nil, err
	}
	return doc, nil
}

// The published def set has no bootstrap request shape because the call takes no parameters, so
// its payload is graded as EmptyPayload rather than an invented definition.
var nativeRequestDefs = map[string]string{
	KindUserBootstrapRequest:    "EmptyPayload",
	KindCredentialImportRequest: "NativeCredentialImportRequest",
	KindWorkspaceChooseRequest:  "NativeWorkspaceChooseRequest",
}

var nativeResultDefs = map[string]string{
	KindUserBootstrapResult:    "NativeUserBootstrapResult",
	KindCredentialImportResult: "NativeCredentialImportResult",
	KindWorkspaceChooseResult:  "NativeWorkspaceChooseResult",
}

// validateNativeRequest checks one request payload against its published definition, in write
// direction: only here may credential material appear at all.
func (h *Host) validateNativeRequest(kind string, payload []byte) error {
	def, ok := nativeRequestDefs[kind]
	if !ok {
		return fmt.Errorf("%w: native kind %s has no published definition", ErrFrameShape, kind)
	}
	if h.doc == nil {
		return fmt.Errorf("%w: host contract not loaded", ErrBadState)
	}
	var v any
	if err := json.Unmarshal(payload, &v); err != nil {
		return fmt.Errorf("%w: %v", ErrFrameShape, err)
	}
	if err := h.doc.ValidateDefInput(def, v); err != nil {
		return fmt.Errorf("%w: %v", ErrFrameShape, err)
	}
	return nil
}

// validateNativeReply grades a reply in read direction and refuses to return it otherwise, so
// the credential boundary is enforced by the contract rather than by handler discipline.
func (h *Host) validateNativeReply(reply []byte) error {
	var frame struct {
		Kind    string          `json:"kind"`
		Payload json.RawMessage `json:"payload"`
	}
	if err := json.Unmarshal(reply, &frame); err != nil {
		return fmt.Errorf("%w: %v", ErrFrameShape, err)
	}
	if frame.Kind == KindNativeClientAttestResult {
		return validateNativeCreateResult(reply)
	}
	def, ok := nativeResultDefs[frame.Kind]
	if !ok {
		return fmt.Errorf("%w: native result %s has no published definition", ErrFrameShape, frame.Kind)
	}
	if h.doc == nil {
		return fmt.Errorf("%w: host contract not loaded", ErrBadState)
	}
	var v any
	if err := json.Unmarshal(frame.Payload, &v); err != nil {
		return err
	}
	if err := h.doc.ValidateDef(def, v); err != nil {
		return fmt.Errorf("%w: reply violates %s: %v", ErrFrameShape, def, err)
	}
	return nil
}
