package host

import (
	"bytes"
	"fmt"
	"time"
)

func bytesReader(b []byte) *bytes.Reader { return bytes.NewReader(b) }

// nanos is the single clock source for generated local references.
func nanos() int64 { return time.Now().UTC().UnixNano() }

func hostRef(kind string, n int) string { return fmt.Sprintf("%s-%d-%d", kind, n+1, nanos()) }
