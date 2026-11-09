//go:build windows

package recoveryauthority

import (
	"bytes"
	"context"
	"debug/buildinfo"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"golang.org/x/sys/windows"
	rt "researchos.local/research-os/adapters/runtime"
)

const bootstrapEnv = "RESEARCHOS_PRIVATE_ADOPTION_BOOTSTRAP_HANDLE"
const MaintenanceArgument = "--private-prepared-abandonment"
const maxFrame = 4 * 1024 * 1024

type heldFile struct {
	file *os.File
	id   string
	path string
}
type nativeSession struct {
	lease        *rt.DataRootLease
	root, db     *heldFile
	guards       []*heldFile
	peer         windows.Handle
	peerIdentity ProcessIdentity
	self         ProcessIdentity
	expires      time.Time
	channel      *os.File
}

func fileID(h windows.Handle) (string, error) {
	var i windows.ByHandleFileInformation
	if e := windows.GetFileInformationByHandle(h, &i); e != nil {
		return "", e
	}
	if i.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 {
		return "", errors.New("AUTHORITY_REPARSE")
	}
	return fmt.Sprintf("%08x:%08x:%08x", i.VolumeSerialNumber, i.FileIndexHigh, i.FileIndexLow), nil
}
func plainPath(path string) error {
	a, e := filepath.Abs(path)
	if e != nil || a != filepath.Clean(path) || strings.HasPrefix(path, `\\`) {
		return errors.New("AUTHORITY_ABSOLUTE_LOCAL_PATH")
	}
	real, e := filepath.EvalSymlinks(path)
	if e != nil || !strings.EqualFold(real, path) {
		return errors.New("AUTHORITY_REPARSE_PATH")
	}
	return nil
}
func hold(path string, directory, mutable bool) (*heldFile, error) {
	if e := plainPath(path); e != nil {
		return nil, e
	}
	ptr, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return nil, e
	}
	access := uint32(windows.GENERIC_READ)
	flags := uint32(windows.FILE_FLAG_OPEN_REPARSE_POINT)
	if directory {
		access = windows.FILE_READ_ATTRIBUTES
		flags |= windows.FILE_FLAG_BACKUP_SEMANTICS
	}
	share := uint32(windows.FILE_SHARE_READ)
	if mutable {
		share |= windows.FILE_SHARE_WRITE
	}
	h, e := windows.CreateFile(ptr, access, share, nil, windows.OPEN_EXISTING, flags, 0)
	if e != nil {
		return nil, e
	}
	id, e := fileID(h)
	if e != nil {
		windows.CloseHandle(h)
		return nil, e
	}
	var info windows.ByHandleFileInformation
	if e = windows.GetFileInformationByHandle(h, &info); e != nil || (info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != directory {
		windows.CloseHandle(h)
		return nil, errors.New("AUTHORITY_FILE_KIND")
	}
	return &heldFile{file: os.NewFile(uintptr(h), path), id: id, path: path}, nil
}
func (f *heldFile) check() error {
	if f == nil || f.file == nil {
		return errors.New("AUTHORITY_FILE_CLOSED")
	}
	id, e := fileID(windows.Handle(f.file.Fd()))
	if e != nil || id != f.id {
		return errors.New("AUTHORITY_FILE_ID_CHANGED")
	}
	other, e := hold(f.path, false, true)
	// Directory paths require a directory handle.
	if e != nil {
		other, e = hold(f.path, true, true)
	}
	if e != nil {
		return e
	}
	defer other.file.Close()
	if other.id != id {
		return errors.New("AUTHORITY_PATH_ID_CHANGED")
	}
	return nil
}
func pinHeld(p RawPin) (*heldFile, []byte, error) {
	if p.Bytes < 0 || p.Bytes > 256*1024*1024 || !validHash(p.SHA256) {
		return nil, nil, errors.New("AUTHORITY_PIN_SIZE")
	}
	f, e := hold(p.Path, false, false)
	if e != nil {
		return nil, nil, e
	}
	b, e := io.ReadAll(io.LimitReader(f.file, p.Bytes+1))
	if e != nil || int64(len(b)) != p.Bytes || digest(b) != p.SHA256 {
		f.file.Close()
		return nil, nil, errors.New("AUTHORITY_RAW_PIN_MISMATCH")
	}
	return f, b, nil
}
func process(h windows.Handle) (ProcessIdentity, error) {
	var p ProcessIdentity
	pid, e := windows.GetProcessId(h)
	if e != nil {
		return p, e
	}
	p.PID = pid
	var created, exited, kernel, user windows.Filetime
	if e = windows.GetProcessTimes(h, &created, &exited, &kernel, &user); e != nil {
		return p, e
	}
	p.Birth100ns = strconv.FormatUint(uint64(created.HighDateTime)<<32|uint64(created.LowDateTime), 10)
	var exit uint32
	if e = windows.GetExitCodeProcess(h, &exit); e != nil || exit != 259 {
		return p, errors.New("AUTHORITY_PEER_NOT_LIVE")
	}
	buf := make([]uint16, 32768)
	size := uint32(len(buf))
	if e = windows.QueryFullProcessImageName(h, 0, &buf[0], &size); e != nil {
		return p, e
	}
	path := windows.UTF16ToString(buf[:size])
	f, e := hold(path, false, false)
	if e != nil {
		return p, e
	}
	defer f.file.Close()
	raw, e := io.ReadAll(io.LimitReader(f.file, 256*1024*1024))
	if e != nil {
		return p, e
	}
	p.Image = RawPin{Role: "observed-image", Path: path, SHA256: digest(raw), Bytes: int64(len(raw))}
	var token windows.Token
	if e = windows.OpenProcessToken(h, windows.TOKEN_QUERY, &token); e != nil {
		return p, e
	}
	defer token.Close()
	u, e := token.GetTokenUser()
	if e != nil {
		return p, e
	}
	p.SID = u.User.Sid.String()
	return p, nil
}
func sameProcess(a, b ProcessIdentity) bool {
	return a.PID == b.PID && a.Birth100ns == b.Birth100ns && a.SID == b.SID && strings.EqualFold(a.Image.Path, b.Image.Path) && a.Image.SHA256 == b.Image.SHA256 && a.Image.Bytes == b.Image.Bytes
}
func liveProcessBinding(h windows.Handle, expected ProcessIdentity) error {
	pid, e := windows.GetProcessId(h)
	if e != nil || pid != expected.PID {
		return errors.New("AUTHORITY_LIVE_PID")
	}
	var created, exited, kernel, user windows.Filetime
	if e = windows.GetProcessTimes(h, &created, &exited, &kernel, &user); e != nil {
		return e
	}
	birth := strconv.FormatUint(uint64(created.HighDateTime)<<32|uint64(created.LowDateTime), 10)
	if birth != expected.Birth100ns || exited.HighDateTime != 0 || exited.LowDateTime != 0 {
		return errors.New("AUTHORITY_LIVE_BIRTH_OR_EXIT")
	}
	status, e := windows.WaitForSingleObject(h, 0)
	if e != nil || status != uint32(windows.WAIT_TIMEOUT) {
		return errors.New("AUTHORITY_PROCESS_NOT_LIVE")
	}
	return nil
}
func acceptedImage(p ProcessIdentity, pin RawPin, sid, application string) error {
	if p.SID != sid || !strings.EqualFold(p.Image.Path, pin.Path) || p.Image.SHA256 != pin.SHA256 || p.Image.Bytes != pin.Bytes {
		return errors.New("AUTHORITY_UNACCEPTED_IMAGE")
	}
	f, raw, e := pinHeld(pin)
	if e != nil {
		return e
	}
	defer f.file.Close()
	info, e := buildinfo.Read(bytes.NewReader(raw))
	if e != nil || info.Path != application {
		return errors.New("AUTHORITY_BUILD_APPLICATION")
	}
	settings := map[string]string{}
	for _, s := range info.Settings {
		settings[s.Key] = s.Value
	}
	if settings["GOOS"] != "windows" || settings["GOARCH"] != "amd64" || settings["CGO_ENABLED"] != "0" || settings["-trimpath"] != "true" {
		return errors.New("AUTHORITY_BUILD_PLATFORM")
	}
	return nil
}
func (n *nativeSession) check() error {
	if n == nil || n.lease == nil || !n.lease.Held() || n.peer == 0 || time.Now().After(n.expires) {
		return errors.New("AUTHORITY_NATIVE_LIFETIME")
	}
	// Image/source/signature loading happened before the transaction and its
	// deny-write guards remain held. CAS rechecks only live handles and IDs.
	if e := liveProcessBinding(n.peer, n.peerIdentity); e != nil {
		return e
	}
	if e := liveProcessBinding(windows.CurrentProcess(), n.self); e != nil {
		return e
	}
	var e error
	if e = n.root.check(); e != nil {
		return e
	}
	if e = n.db.check(); e != nil {
		return e
	}
	// Guard handles deny write/delete sharing for the whole operation.
	for _, g := range n.guards {
		if _, e = g.file.Stat(); e != nil {
			return e
		}
	}
	return nil
}
func (n *nativeSession) close() error {
	if n == nil {
		return nil
	}
	var errs []error
	if n.channel != nil {
		errs = append(errs, n.channel.Close())
		n.channel = nil
	}
	if n.peer != 0 {
		errs = append(errs, windows.CloseHandle(n.peer))
		n.peer = 0
	}
	for _, g := range n.guards {
		errs = append(errs, g.file.Close())
	}
	n.guards = nil
	if n.db != nil {
		errs = append(errs, n.db.file.Close())
		n.db = nil
	}
	if n.root != nil {
		errs = append(errs, n.root.file.Close())
		n.root = nil
	}
	if n.lease != nil {
		errs = append(errs, n.lease.ReturnBorrow())
		errs = append(errs, n.lease.Close())
		n.lease = nil
	}
	return errors.Join(errs...)
}
func loadRelease(path string) (Release, []byte, error) {
	var r Release
	f, e := hold(path, false, false)
	if e != nil {
		return r, nil, e
	}
	defer f.file.Close()
	raw, e := io.ReadAll(io.LimitReader(f.file, maxFrame+1))
	if e != nil || len(raw) > maxFrame {
		return r, nil, errors.New("AUTHORITY_RELEASE_SIZE")
	}
	if e = verifyDocument(raw, Purpose+"/release", &r); e != nil {
		return r, nil, e
	}
	if r.Schema != "researchos.recovery-release.v1" || r.Purpose != Purpose || r.ID == "" || r.SID == "" || !validInterval(r.NotBeforeUTC, r.ExpiresUTC, time.Now(), 0) || len(r.SourceFiles) == 0 {
		return r, nil, errors.New("AUTHORITY_RELEASE_BINDING")
	}
	if _, e = publicKey(r.RootSigningPublicKey); e != nil {
		return r, nil, e
	}
	return r, raw, nil
}
func verifyGrant(raw, releaseRaw []byte) (Grant, error) {
	var g Grant
	if e := verifyDocument(raw, Purpose+"/grant", &g); e != nil {
		return g, e
	}
	nonce, e := hexNonce(g.Nonce)
	if e != nil || len(nonce) != 32 || g.Schema != "researchos.recovery-grant.v1" || g.Purpose != Purpose || g.ReleaseSHA256 != digest(releaseRaw) || !validTuple(g.Tuple) || !validInterval(g.IssuedUTC, g.ExpiresUTC, time.Now(), 5*time.Minute) || g.RootIdentity == "" || g.DatabaseIdentity == "" || !strings.EqualFold(filepath.Dir(g.Database), g.Root) {
		return g, errors.New("AUTHORITY_GRANT_BINDING")
	}
	return g, validatePinRoles(g.Pins)
}
func sourceGuards(r Release) ([]*heldFile, error) {
	expected := map[string]RawPin{}
	var guards []*heldFile
	fail := func(e error) ([]*heldFile, error) {
		for _, f := range guards {
			f.file.Close()
		}
		return nil, e
	}
	for _, p := range r.SourceFiles {
		rel, e := filepath.Rel(r.SourceRoot, p.Path)
		if e != nil || !filepath.IsLocal(rel) {
			return fail(errors.New("AUTHORITY_SOURCE_SCOPE"))
		}
		key := strings.ToLower(filepath.ToSlash(rel))
		if _, ok := expected[key]; ok {
			return fail(errors.New("AUTHORITY_SOURCE_DUPLICATE"))
		}
		expected[key] = p
		f, _, e := pinHeld(p)
		if e != nil {
			return fail(e)
		}
		guards = append(guards, f)
	}
	// Conservative repository-local coverage: every regular file under these
	// fixed product trees is required, regardless of suffix, dot/underscore
	// name, test status or go:embed directory/glob selection. Go embeds cannot
	// escape their package tree. Do not confuse this with a compiler-derived
	// closure of external modules: Root must separately verify go list -deps
	// EmbedFiles/compiled inputs against its accepted, pinned build inventory.
	dirs := []string{"apps/control", "internal", "adapters", "evaluation", "ops", "migrations/sqlite", "spec/v2.0/contracts"}
	if _, e := os.Lstat(filepath.Join(r.SourceRoot, "vendor")); e == nil {
		dirs = append(dirs, "vendor")
	} else if !errors.Is(e, os.ErrNotExist) {
		return fail(e)
	}
	for _, dir := range dirs {
		e := filepath.WalkDir(filepath.Join(r.SourceRoot, filepath.FromSlash(dir)), func(path string, d os.DirEntry, e error) error {
			if e != nil {
				return e
			}
			if d.Type()&os.ModeSymlink != 0 {
				return errors.New("AUTHORITY_SOURCE_LINK")
			}
			if d.IsDir() {
				return plainPath(path)
			}
			if !d.Type().IsRegular() {
				return errors.New("AUTHORITY_SOURCE_NONREGULAR")
			}
			rel, e := filepath.Rel(r.SourceRoot, path)
			if e != nil {
				return e
			}
			if _, ok := expected[strings.ToLower(filepath.ToSlash(rel))]; !ok {
				return fmt.Errorf("AUTHORITY_SOURCE_OMITTED:%s", filepath.ToSlash(rel))
			}
			return nil
		})
		if e != nil {
			return fail(e)
		}
	}
	for _, rel := range []string{"go.mod", "go.sum", "execution/toolchains/locked.json"} {
		if _, ok := expected[rel]; !ok {
			return fail(errors.New("AUTHORITY_REQUIRED_BUILD_PIN"))
		}
	}
	// The accepted build still uses GOWORK=off; pin any present workspace files
	// conservatively so an unexpected local build selector cannot be omitted.
	for _, rel := range []string{"go.work", "go.work.sum"} {
		if _, e := os.Lstat(filepath.Join(r.SourceRoot, rel)); e == nil {
			if _, ok := expected[rel]; !ok {
				return fail(fmt.Errorf("AUTHORITY_REQUIRED_BUILD_PIN:%s", rel))
			}
		} else if !errors.Is(e, os.ErrNotExist) {
			return fail(e)
		}
	}
	return guards, nil
}

// ReceiveInherited is the sole production token constructor. Bootstrap handle
// is only transport. Both its peer and this executable are measured against the
// issuer-signed release selected beside this executable, never request anchors.
func ReceiveInherited(ctx context.Context) (Token, string, error) {
	var zero Token
	b, e := readBootstrap()
	if e != nil {
		return zero, "", e
	}
	if b.Purpose != Purpose {
		return zero, "", errors.New("AUTHORITY_BOOTSTRAP_PURPOSE")
	}
	self, e := process(windows.CurrentProcess())
	if e != nil {
		return zero, "", e
	}
	release, releaseRaw, e := loadRelease(filepath.Join(filepath.Dir(self.Image.Path), "recovery-release.json"))
	if e != nil {
		return zero, "", e
	}
	if e = acceptedImage(self, release.ControlImage, release.SID, "researchos.local/research-os/apps/control"); e != nil {
		return zero, "", e
	}
	peer, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE, false, b.Peer.PID)
	if e != nil {
		return zero, "", e
	}
	n := &nativeSession{peer: peer, self: self, peerIdentity: b.Peer}
	ok := false
	defer func() {
		if !ok {
			_ = n.close()
		}
	}()
	observed, e := process(peer)
	if e != nil || !sameProcess(observed, b.Peer) {
		return zero, "", errors.New("AUTHORITY_BOOTSTRAP_PEER")
	}
	if e = acceptedImage(observed, release.RootImage, release.SID, "researchos.local/research-os/ops/supervisor/recovery_root"); e != nil {
		return zero, "", e
	}
	conn, e := dialPrivate(ctx, b.Pipe, b.Peer)
	if e != nil {
		return zero, "", e
	}
	n.channel = conn
	var frame bootstrapFrame
	if e = readFrame(conn, b.Key, Purpose, &frame); e != nil {
		return zero, "", e
	}
	g, e := verifyGrant(frame.Grant, releaseRaw)
	if e != nil {
		return zero, "", e
	}
	if !releaseCoversGrant(release, g.ExpiresUTC) {
		return zero, "", errors.New("AUTHORITY_RELEASE_EXPIRES_BEFORE_GRANT")
	}
	if e = verifyAdoption(frame.Adoption, release, g, frame.Grant); e != nil || !sameProcess(frame.Adoption.Producer, observed) || !sameProcess(frame.Adoption.Maintenance, self) {
		return zero, "", errors.New("AUTHORITY_CURRENT_SIGNED_PRODUCER")
	}
	n.expires, _ = time.Parse(time.RFC3339Nano, g.ExpiresUTC)
	if n.guards, e = sourceGuards(release); e != nil {
		return zero, "", e
	}
	for _, pin := range []RawPin{release.RootImage, release.ControlImage} {
		f, _, err := pinHeld(pin)
		if err != nil {
			return zero, "", err
		}
		n.guards = append(n.guards, f)
	}
	raw := map[string][]byte{}
	for _, p := range g.Pins {
		f, data, err := pinHeld(p)
		if err != nil {
			return zero, "", err
		}
		n.guards = append(n.guards, f)
		raw[p.Role] = data
	}
	historical, started, expired, e := readHistorical(raw, g.Tuple, g.Pins)
	if e != nil || !bytes.Equal(encoded(historical), encoded(frame.Adoption.Historical)) || started != frame.Adoption.RootStartedUTC || expired != frame.Adoption.RootClockExpiredUTC {
		return zero, "", errors.New("AUTHORITY_HISTORY_ADOPTION_DIFFERS")
	}
	// Inspect original files before acquiring a new lease. Never create a root
	// or database as a side effect of an unvalidated bootstrap.
	if n.root, e = hold(g.Root, true, true); e != nil {
		return zero, "", e
	}
	if n.root.id != g.RootIdentity {
		return zero, "", errors.New("AUTHORITY_ROOT_ID")
	}
	if n.db, e = hold(g.Database, false, true); e != nil {
		return zero, "", e
	}
	if n.db.id != g.DatabaseIdentity {
		return zero, "", errors.New("AUTHORITY_DB_ID")
	}
	if n.lease, e = rt.AcquireDataRootLease(g.Root); e != nil {
		return zero, "", e
	}
	if e = n.lease.Borrow(g.Root); e != nil {
		_ = n.lease.Close()
		n.lease = nil
		return zero, "", e
	}
	if e = n.check(); e != nil {
		return zero, "", e
	}
	if frame.OwnerToken == "" {
		return zero, "", errors.New("AUTHORITY_CURRENT_OWNER_CREDENTIAL_REQUIRED")
	}
	ok = true
	return Token{state: &tokenState{adoption: frame.Adoption, native: n, phase: "READY"}}, frame.OwnerToken, nil
}
