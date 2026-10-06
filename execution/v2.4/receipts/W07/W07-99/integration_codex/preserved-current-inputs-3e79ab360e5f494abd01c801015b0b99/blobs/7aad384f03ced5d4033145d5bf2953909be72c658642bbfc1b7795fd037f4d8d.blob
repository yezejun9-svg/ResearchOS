package canonical

import (
	"encoding/json"
	"encoding/json/jsontext"
)

// JSON applies RFC 8785 to strict JSON input. Go 1.27 rejects duplicate names
// and invalid Unicode before canonicalization.
func JSON(input []byte) ([]byte, error) {
	v := jsontext.Value(input).Clone()
	// JCS uses finite IEEE-754 numbers. jsontext validates syntax and Unicode;
	// encoding/json additionally rejects exponents outside float64 range.
	var check any
	if err := json.Unmarshal(v, &check); err != nil {
		return nil, err
	}
	if err := v.Canonicalize(); err != nil {
		return nil, err
	}
	return []byte(v), nil
}
