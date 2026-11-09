//go:build windows

package host

import (
	"unsafe"

	"golang.org/x/sys/windows"
)

// protect seals plaintext to the current OS user's DPAPI master key. UI prompts are forbidden
// so a background host can never block on a dialog, and the caps mirror the existing protected
// store limits so a hostile caller cannot make the host encrypt arbitrary data.
func protect(raw []byte) ([]byte, error) {
	in := windows.DataBlob{Size: uint32(len(raw)), Data: &raw[0]}
	var out windows.DataBlob
	if windows.CryptProtectData(&in, nil, nil, 0, nil, windows.CRYPTPROTECT_UI_FORBIDDEN, &out) != nil {
		return nil, ErrCredentialProtected
	}
	defer windows.LocalFree(windows.Handle(unsafe.Pointer(out.Data)))
	return append([]byte(nil), unsafe.Slice(out.Data, out.Size)...), nil
}

func unprotect(cipher []byte) ([]byte, error) {
	if len(cipher) == 0 || len(cipher) > MaxWrappedBytes {
		return nil, ErrCredentialProtected
	}
	in := windows.DataBlob{Size: uint32(len(cipher)), Data: &cipher[0]}
	var out windows.DataBlob
	if windows.CryptUnprotectData(&in, nil, nil, 0, nil, windows.CRYPTPROTECT_UI_FORBIDDEN, &out) != nil {
		return nil, ErrCredentialProtected
	}
	defer windows.LocalFree(windows.Handle(unsafe.Pointer(out.Data)))
	view := unsafe.Slice(out.Data, out.Size)
	defer func() {
		for i := range view {
			view[i] = 0
		}
	}()
	return append([]byte(nil), view...), nil
}

// otherOS reports whether the DPAPI-dependent paths must fail closed on this platform.
func otherOS() bool { return false }
