//go:build windows

package protectedstore

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"golang.org/x/sys/windows"
	"io"
	"mime"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/canonical"
	"strings"
	"sync"
	"unsafe"
)

type CanaryStore struct {
	mu      sync.Mutex
	root    string
	sid     string
	handles []windows.Handle
	sd      *windows.SECURITY_DESCRIPTOR
	closed  bool
}

// NewCanary creates a new private directory. It never takes over an existing
// directory or changes ACLs on user-created data. The current-user SID is not an
// independent verifier identity; LIVE operations always remain unavailable.
func NewCanary(root string) (*CanaryStore, error) {
	return openCanary(root, true)
}

// OpenCanary reopens only an existing directory with the exact current-identity
// boundary. It does not repair permissions or take ownership of existing data.
func OpenCanary(root string) (*CanaryStore, error) {
	return openCanary(root, false)
}

func openCanary(root string, create bool) (*CanaryStore, error) {
	if !filepath.IsAbs(root) || strings.HasPrefix(root, `\\`) || filepath.Clean(root) != root {
		return nil, ErrBoundary
	}
	tokenUser, e := windows.GetCurrentProcessToken().GetTokenUser()
	if e != nil {
		return nil, ErrBoundary
	}
	sid := tokenUser.User.Sid.String()
	sd, e := windows.SecurityDescriptorFromString("O:" + sid + "D:P(A;OICI;FA;;;" + sid + ")")
	if e != nil {
		return nil, ErrBoundary
	}
	store := &CanaryStore{root: root, sid: sid, sd: sd}
	ok := false
	defer func() {
		if !ok {
			store.Close()
		}
	}()
	// Hold every ancestor without FILE_SHARE_DELETE. Reparse-point handles are
	// opened as the reparse object and then rejected, never traversed blindly.
	parent := filepath.Dir(root)
	volume := filepath.VolumeName(parent)
	current := volume + `\`
	parts := strings.Split(strings.TrimPrefix(parent, current), `\`)
	paths := []string{current}
	for _, part := range parts {
		if part != "" {
			current = filepath.Join(current, part)
			paths = append(paths, current)
		}
	}
	for _, path := range paths {
		h, e := openDirectory(path)
		if e != nil {
			return nil, ErrBoundary
		}
		store.handles = append(store.handles, h)
	}
	sa := windows.SecurityAttributes{Length: uint32(unsafe.Sizeof(windows.SecurityAttributes{})), SecurityDescriptor: sd}
	name, e := windows.UTF16PtrFromString(root)
	if e != nil {
		return nil, ErrBoundary
	}
	if create {
		if e = windows.CreateDirectory(name, &sa); e != nil {
			return nil, ErrBoundary
		}
	}
	h, e := openDirectory(root)
	if e != nil {
		return nil, ErrBoundary
	}
	store.handles = append(store.handles, h)
	if e = store.checkRoot(); e != nil {
		return nil, e
	}
	ok = true
	return store, nil
}
func openDirectory(path string) (windows.Handle, error) {
	name, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return 0, e
	}
	h, e := windows.CreateFile(name, windows.FILE_READ_ATTRIBUTES|windows.READ_CONTROL, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_BACKUP_SEMANTICS|windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if e != nil {
		return 0, e
	}
	var info windows.ByHandleFileInformation
	if e = windows.GetFileInformationByHandle(h, &info); e != nil || info.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 || info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY == 0 {
		windows.CloseHandle(h)
		return 0, ErrBoundary
	}
	return h, nil
}
func (s *CanaryStore) Close() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.closed {
		return nil
	}
	s.closed = true
	for i := len(s.handles) - 1; i >= 0; i-- {
		windows.CloseHandle(s.handles[i])
	}
	s.handles = nil
	return nil
}
func (s *CanaryStore) checkRoot() error {
	if s.closed || len(s.handles) == 0 {
		return ErrUnavailable
	}
	h := s.handles[len(s.handles)-1]
	// Modern Windows POSIX rename may bypass ordinary share-delete protection.
	// Revalidate the actual open handle's name instead of assuming rename failed.
	buffer := make([]uint16, 32768)
	n, e := windows.GetFinalPathNameByHandle(h, &buffer[0], uint32(len(buffer)), 0)
	if e != nil || n == 0 || n >= uint32(len(buffer)) {
		return ErrBoundary
	}
	actual := strings.TrimPrefix(windows.UTF16ToString(buffer[:n]), `\\?\`)
	if !strings.EqualFold(filepath.Clean(actual), s.root) {
		return ErrBoundary
	}
	return s.checkACL(h, true)
}
func (s *CanaryStore) checkACL(h windows.Handle, directory bool) error {
	sd, e := windows.GetSecurityInfo(h, windows.SE_FILE_OBJECT, windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
	if e != nil || !sd.IsValid() {
		return ErrBoundary
	}
	control, _, e := sd.Control()
	if e != nil || control&windows.SE_DACL_PROTECTED == 0 {
		return ErrBoundary
	}
	owner, _, e := sd.Owner()
	if e != nil || owner == nil || owner.String() != s.sid {
		return ErrBoundary
	}
	acl, _, e := sd.DACL()
	if e != nil || acl == nil || acl.AceCount != 1 {
		return ErrBoundary
	}
	var ace *windows.ACCESS_ALLOWED_ACE
	if e = windows.GetAce(acl, 0, &ace); e != nil || ace.Header.AceType != windows.ACCESS_ALLOWED_ACE_TYPE || uint32(ace.Mask) != 0x1f01ff {
		return ErrBoundary
	}
	trustee := (*windows.SID)(unsafe.Pointer(&ace.SidStart))
	if !trustee.IsValid() || trustee.String() != s.sid {
		return ErrBoundary
	}
	flags := uint8(0)
	if directory {
		flags = 3
	}
	if ace.Header.AceFlags != flags {
		return ErrBoundary
	}
	return nil
}
func (s *CanaryStore) Boundary(ctx context.Context) (Boundary, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if ctx.Err() != nil {
		return Boundary{}, ctx.Err()
	}
	if e := s.checkRoot(); e != nil {
		return Boundary{}, e
	}
	return Boundary{Mode: "CANARY_ONLY", OwnerSID: s.sid, IndependentIdentity: false, UnrestrictedSameUserCanRead: true}, nil
}
func (s *CanaryStore) Ready(ctx context.Context, mode string) error {
	if mode != "FIXTURE" {
		return ErrIsolation
	}
	_, e := s.Boundary(ctx)
	return e
}
func (s *CanaryStore) createFile(name string, raw []byte) error {
	sd, e := windows.SecurityDescriptorFromString("O:" + s.sid + "D:P(A;;FA;;;" + s.sid + ")")
	if e != nil {
		return ErrBoundary
	}
	sa := windows.SecurityAttributes{Length: uint32(unsafe.Sizeof(windows.SecurityAttributes{})), SecurityDescriptor: sd}
	path, _ := windows.UTF16PtrFromString(filepath.Join(s.root, name))
	h, e := windows.CreateFile(path, windows.GENERIC_WRITE|windows.READ_CONTROL, 0, &sa, windows.CREATE_NEW, windows.FILE_ATTRIBUTE_NORMAL|windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if e != nil {
		return ErrBoundary
	}
	f := os.NewFile(uintptr(h), "protected-canary")
	defer f.Close()
	if e = s.checkACL(h, false); e != nil {
		return e
	}
	if _, e = f.Write(raw); e != nil {
		return ErrIntegrity
	}
	if e = f.Sync(); e != nil {
		return ErrIntegrity
	}
	return nil
}

// CreateCanary is a trusted fixture-only writer, deliberately absent from the
// control-plane Provider interface. It stores no formal data or credentials.
func (s *CanaryStore) CreateCanary(ctx context.Context, project, media string, raw []byte) (Blob, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if ctx.Err() != nil {
		return Blob{}, ctx.Err()
	}
	if e := s.checkRoot(); e != nil {
		return Blob{}, e
	}
	if project == "" || len(raw) > MaxBlobBytes {
		return Blob{}, ErrIntegrity
	}
	if _, _, e := mime.ParseMediaType(media); e != nil {
		return Blob{}, ErrIntegrity
	}
	var id [16]byte
	if _, e := rand.Read(id[:]); e != nil {
		return Blob{}, ErrUnavailable
	}
	key := hex.EncodeToString(id[:])
	blob := Blob{Ticket: "ps1:" + key, Project: project, Hash: Digest(raw), Size: int64(len(raw)), MediaType: media, MeasurementMode: "FIXTURE"}
	if e := s.createFile(key+".bin", raw); e != nil {
		return Blob{}, e
	}
	metadata, _ := json.Marshal(blob)
	if e := s.createFile(key+".json", metadata); e != nil {
		return Blob{}, e
	}
	if e := s.checkRoot(); e != nil {
		return Blob{}, e
	}
	return blob, nil
}
func (s *CanaryStore) readFile(name string, limit int64) ([]byte, error) {
	path, _ := windows.UTF16PtrFromString(filepath.Join(s.root, name))
	h, e := windows.CreateFile(path, windows.GENERIC_READ|windows.READ_CONTROL, windows.FILE_SHARE_READ, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if e != nil {
		return nil, ErrNotFound
	}
	f := os.NewFile(uintptr(h), "protected-canary")
	defer f.Close()
	var info windows.ByHandleFileInformation
	if e = windows.GetFileInformationByHandle(h, &info); e != nil || info.FileAttributes&(windows.FILE_ATTRIBUTE_REPARSE_POINT|windows.FILE_ATTRIBUTE_DIRECTORY) != 0 || info.NumberOfLinks != 1 {
		return nil, ErrBoundary
	}
	if e = s.checkACL(h, false); e != nil {
		return nil, e
	}
	size := int64(info.FileSizeHigh)<<32 | int64(info.FileSizeLow)
	if size < 0 || size > limit {
		return nil, ErrIntegrity
	}
	raw, e := io.ReadAll(io.LimitReader(f, limit+1))
	if e != nil || int64(len(raw)) != size {
		return nil, ErrIntegrity
	}
	if e = s.checkRoot(); e != nil {
		return nil, e
	}
	return raw, nil
}
func (s *CanaryStore) describe(project, ticket string) (Blob, error) {
	if !ValidTicket(ticket) {
		return Blob{}, ErrNotFound
	}
	raw, e := s.readFile(strings.TrimPrefix(ticket, "ps1:")+".json", 4096)
	if e != nil {
		return Blob{}, e
	}
	canonicalRaw, e := canonical.JSON(raw)
	if e != nil {
		return Blob{}, ErrIntegrity
	}
	var b Blob
	if json.Unmarshal(canonicalRaw, &b) != nil || !b.Valid() || b.Ticket != ticket || b.Project != project || b.MeasurementMode != "FIXTURE" {
		return Blob{}, ErrNotFound
	}
	return b, nil
}
func (s *CanaryStore) Describe(ctx context.Context, project, ticket string) (Blob, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if ctx.Err() != nil {
		return Blob{}, ctx.Err()
	}
	if e := s.checkRoot(); e != nil {
		return Blob{}, e
	}
	return s.describe(project, ticket)
}
func (s *CanaryStore) Read(ctx context.Context, expected Blob) ([]byte, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	if e := s.checkRoot(); e != nil {
		return nil, e
	}
	if expected.MeasurementMode != "FIXTURE" {
		return nil, ErrIsolation
	}
	b, e := s.describe(expected.Project, expected.Ticket)
	if e != nil {
		return nil, e
	}
	if b != expected {
		return nil, ErrIntegrity
	}
	raw, e := s.readFile(strings.TrimPrefix(b.Ticket, "ps1:")+".bin", MaxBlobBytes)
	if e != nil {
		return nil, e
	}
	if int64(len(raw)) != b.Size || Digest(raw) != b.Hash {
		return nil, ErrIntegrity
	}
	if e = s.checkRoot(); e != nil {
		return nil, e
	}
	return raw, nil
}
