//go:build windows

package recoveryauthority

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"os"
	"path/filepath"
	"unsafe"

	"golang.org/x/sys/windows"
)

func wipe(b []byte) {
	for i := range b {
		b[i] = 0
	}
}
func purposeCrypt(raw []byte, role string, protect bool) ([]byte, error) {
	if (role != "issuer" && role != "root-adoption") || len(raw) == 0 || len(raw) > 16384 {
		return nil, errors.New("AUTHORITY_KEY_ROLE_OR_SIZE")
	}
	entropy := []byte(Purpose + "/DPAPI/" + role)
	in := windows.DataBlob{Size: uint32(len(raw)), Data: &raw[0]}
	optional := windows.DataBlob{Size: uint32(len(entropy)), Data: &entropy[0]}
	var out windows.DataBlob
	var e error
	if protect {
		e = windows.CryptProtectData(&in, nil, &optional, 0, nil, windows.CRYPTPROTECT_UI_FORBIDDEN, &out)
	} else {
		e = windows.CryptUnprotectData(&in, nil, &optional, 0, nil, windows.CRYPTPROTECT_UI_FORBIDDEN, &out)
	}
	if e != nil {
		return nil, errors.New("AUTHORITY_DPAPI_UNAVAILABLE")
	}
	defer windows.LocalFree(windows.Handle(unsafe.Pointer(out.Data)))
	view := unsafe.Slice(out.Data, out.Size)
	defer wipe(view)
	if len(view) == 0 || len(view) > 16384 {
		return nil, errors.New("AUTHORITY_DPAPI_SIZE")
	}
	return append([]byte(nil), view...), nil
}
func readPurposeKey(path, role string) ([]byte, error) {
	f, e := hold(path, false, false)
	if e != nil {
		return nil, e
	}
	defer f.file.Close()
	st, e := f.file.Stat()
	if e != nil || st.Size() < 1 || st.Size() > 16384 {
		return nil, errors.New("AUTHORITY_PRIVATE_KEY_SIZE")
	}
	cipher := make([]byte, st.Size())
	if _, e = f.file.ReadAt(cipher, 0); e != nil {
		return nil, e
	}
	defer wipe(cipher)
	key, e := purposeCrypt(cipher, role, false)
	if e != nil {
		return nil, e
	}
	if len(key) != ed25519.PrivateKeySize {
		wipe(key)
		return nil, errors.New("AUTHORITY_PRIVATE_KEY_FORMAT")
	}
	return key, nil
}

// ProvisionEnrollmentKey is used by the separate OFFLINE enrollment executable,
// never apps/control. It creates only a DPAPI-protected private resource and
// returns public bytes. It does not update compiled trust or create any Token.
func ProvisionEnrollmentKey(path, role string) (string, error) {
	if role != "issuer" && role != "root-adoption" {
		return "", errors.New("AUTHORITY_KEY_ROLE")
	}
	if e := plainPath(filepath.Dir(path)); e != nil {
		return "", e
	}
	pub, key, e := ed25519.GenerateKey(rand.Reader)
	if e != nil {
		return "", e
	}
	defer wipe(key)
	cipher, e := purposeCrypt(key, role, true)
	if e != nil {
		return "", e
	}
	defer wipe(cipher)
	ptr, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return "", e
	}
	sa, e := privateSecurity()
	if e != nil {
		return "", e
	}
	h, e := windows.CreateFile(ptr, windows.GENERIC_WRITE, 0, sa, windows.CREATE_NEW, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if e != nil {
		return "", e
	}
	f := os.NewFile(uintptr(h), path)
	defer f.Close()
	if _, e = f.Write(cipher); e != nil {
		return "", e
	}
	if e = f.Sync(); e != nil {
		return "", e
	}
	return hex.EncodeToString(pub), nil
}

// SignEnrollmentDocument is an offline key-owner operation. There is no
// production RPC/CLI that calls this function. Key possession is insufficient
// to substitute an anchor: the key must equal the newly source-pinned issuer.
func SignEnrollmentDocument(keyPath, kind string, payload []byte) ([]byte, error) {
	key, e := readPurposeKey(keyPath, "issuer")
	if e != nil {
		return nil, e
	}
	defer wipe(key)
	pub, e := publicKey(enrolledIssuerPublicKeyHex)
	if e != nil {
		return nil, e
	}
	if !ed25519.PrivateKey(key).Public().(ed25519.PublicKey).Equal(pub) {
		return nil, errors.New("AUTHORITY_OFFLINE_ISSUER_MISMATCH")
	}
	var purpose string
	switch kind {
	case "release":
		var value Release
		if e = strict(payload, &value); e != nil {
			return nil, e
		}
		if value.Purpose != Purpose || value.Schema != "researchos.recovery-release.v1" {
			return nil, errors.New("AUTHORITY_RELEASE_SCHEMA")
		}
		if !bytes.Equal(payload, encoded(value)) {
			return nil, errors.New("AUTHORITY_CANONICAL_TYPED_PAYLOAD_REQUIRED")
		}
		purpose = Purpose + "/release"
	case "grant":
		var value Grant
		if e = strict(payload, &value); e != nil {
			return nil, e
		}
		if value.Purpose != Purpose || value.Schema != "researchos.recovery-grant.v1" {
			return nil, errors.New("AUTHORITY_GRANT_SCHEMA")
		}
		if !bytes.Equal(payload, encoded(value)) {
			return nil, errors.New("AUTHORITY_CANONICAL_TYPED_PAYLOAD_REQUIRED")
		}
		purpose = Purpose + "/grant"
	case "migration-grant":
		var value MigrationGrant
		if e = strict(payload, &value); e != nil {
			return nil, e
		}
		if value.Purpose != MigrationPurpose || value.Schema != "researchos.recovery-migration-grant.v1" {
			return nil, errors.New("AUTHORITY_MIGRATION_SCHEMA")
		}
		if !bytes.Equal(payload, encoded(value)) {
			return nil, errors.New("AUTHORITY_CANONICAL_TYPED_PAYLOAD_REQUIRED")
		}
		purpose = MigrationPurpose + "/grant"
	default:
		return nil, errors.New("AUTHORITY_OFFLINE_PURPOSE")
	}
	signature := ed25519.Sign(ed25519.PrivateKey(key), append([]byte(purpose+"\x00"), payload...))
	return encoded(signedDocument{Payload: payload, Signature: hex.EncodeToString(signature)}), nil
}
