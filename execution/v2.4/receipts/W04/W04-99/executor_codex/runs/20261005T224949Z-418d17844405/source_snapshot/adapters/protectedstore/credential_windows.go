//go:build windows

package protectedstore

import (
	"golang.org/x/sys/windows"
	"unsafe"
)

const serviceCredentialFile = "typesafe.service.dpapi"
const maxCredentialBytes = 4096

func validCredential(raw []byte) bool {
	if len(raw) == 0 || len(raw) > maxCredentialBytes {
		return false
	}
	for _, b := range raw {
		if b < 33 || b > 126 {
			return false
		}
	}
	return true
}
func wipe(raw []byte) {
	for i := range raw {
		raw[i] = 0
	}
}

func protectCredential(raw []byte) ([]byte, error) {
	if !validCredential(raw) {
		return nil, ErrIntegrity
	}
	in := windows.DataBlob{Size: uint32(len(raw)), Data: &raw[0]}
	var out windows.DataBlob
	if windows.CryptProtectData(&in, nil, nil, 0, nil, windows.CRYPTPROTECT_UI_FORBIDDEN, &out) != nil {
		return nil, ErrUnavailable
	}
	defer windows.LocalFree(windows.Handle(unsafe.Pointer(out.Data)))
	if out.Size == 0 || out.Size > 16384 {
		return nil, ErrIntegrity
	}
	return append([]byte(nil), unsafe.Slice(out.Data, out.Size)...), nil
}
func unprotectCredential(cipher []byte) ([]byte, error) {
	if len(cipher) == 0 || len(cipher) > 16384 {
		return nil, ErrIntegrity
	}
	in := windows.DataBlob{Size: uint32(len(cipher)), Data: &cipher[0]}
	var out windows.DataBlob
	if windows.CryptUnprotectData(&in, nil, nil, 0, nil, windows.CRYPTPROTECT_UI_FORBIDDEN, &out) != nil {
		return nil, ErrUnavailable
	}
	defer windows.LocalFree(windows.Handle(unsafe.Pointer(out.Data)))
	if out.Size == 0 || out.Size > maxCredentialBytes {
		return nil, ErrIntegrity
	}
	view := unsafe.Slice(out.Data, out.Size)
	defer wipe(view)
	if !validCredential(view) {
		return nil, ErrIntegrity
	}
	return append([]byte(nil), view...), nil
}
func (s *CanaryStore) saveServiceCredential(raw []byte) error {
	if e := s.checkRoot(); e != nil {
		return e
	}
	cipher, e := protectCredential(raw)
	if e != nil {
		return e
	}
	// CREATE_NEW and a private service identity DACL make delivery write-once.
	return s.createFile(serviceCredentialFile, cipher)
}
func (s *CanaryStore) loadServiceCredential() ([]byte, error) {
	cipher, e := s.readFile(serviceCredentialFile, 16384)
	if e != nil {
		return nil, e
	}
	return unprotectCredential(cipher)
}
