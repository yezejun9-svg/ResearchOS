//go:build !windows

package host

import (
	"context"
	"errors"
)

// ErrPipeUnavailable exists so callers compile everywhere while the native transport stays
// Windows-only: there is no supported way to bind an OS-SID-scoped local channel elsewhere, and a
// host that cannot prove that boundary must not accept native frames at all.
var ErrPipeUnavailable = errors.New("NATIVE_TRANSPORT_UNAVAILABLE")

func PipeName(instanceID string) string { return "unsupported-" + instanceID }

func (h *Host) ServeNative(context.Context, string) error { return ErrPipeUnavailable }

func DialNative(string, []byte) ([]byte, error) { return nil, ErrPipeUnavailable }

func errorFrame(err error) []byte {
	return []byte(`{"kind":"NATIVE_ERROR","error":{"code":"HOST_UNAVAILABLE","message":"` + err.Error() + `"}}`)
}
