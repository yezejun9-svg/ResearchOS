package host

// Single-use workspace selection references (22 §workspace choose): the host resolves the real
// path, links and access scope itself, then hands the client a reference that is valid for five
// minutes, bound to this principal and this client, and consumable once.

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"sync"
	"time"
)

var (
	ErrSelectionUnknown = errors.New("SELECTION_UNKNOWN")
	ErrSelectionExpired = errors.New("SELECTION_EXPIRED")
	ErrSelectionUsed    = errors.New("SELECTION_ALREADY_USED")
	ErrSelectionForeign = errors.New("FORBIDDEN")
)

type SelectionRecord struct {
	Ref          string `json:"ref"`
	PrincipalRef string `json:"principal_ref"`
	ClientID     string `json:"client_id"`
	RealPath     string `json:"real_path"`
	DisplayPath  string `json:"display_path"`
	Access       string `json:"access"`
	IssuedAt     string `json:"issued_at"`
	ExpiresAt    string `json:"expires_at"`
	Used         bool   `json:"used"`
}

type selectionIndex struct {
	Version   int                `json:"version"`
	Selection []*SelectionRecord `json:"selections"`
}

type SelectionStore struct {
	dir      string
	mu       sync.Mutex
	items    map[string]*SelectionRecord
	MaxItems int
}

func openSelectionStore(dir string) (*SelectionStore, error) {
	d := filepath.Join(dir, "selections")
	if err := os.MkdirAll(d, 0o700); err != nil {
		return nil, err
	}
	if err := privateDir(d); err != nil {
		return nil, err
	}
	s := &SelectionStore{dir: d, items: map[string]*SelectionRecord{}, MaxItems: MaxSelectionRecords}
	var idx selectionIndex
	if err := readPrivate(d, "selections.json", &idx); err != nil {
		return nil, err
	}
	for _, r := range idx.Selection {
		if r != nil && r.Ref != "" {
			s.items[r.Ref] = r
		}
	}
	return s, nil
}

func (s *SelectionStore) save() error {
	idx := selectionIndex{Version: 1}
	for _, ref := range sortedSelectionRefs(s.items) {
		idx.Selection = append(idx.Selection, s.items[ref])
	}
	if idx.Selection == nil {
		idx.Selection = []*SelectionRecord{}
	}
	return writePrivate(s.dir, "selections.json", &idx)
}

func sortedSelectionRefs(m map[string]*SelectionRecord) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

// Issue returns a fresh reference bound to the caller's identity, plus its expiry.
func (s *SelectionStore) Issue(principalRef, clientID, realPath, displayPath, access string, now time.Time) (*SelectionRecord, error) {
	if principalRef == "" || clientID == "" {
		return nil, fmt.Errorf("%w: selection needs a principal and client", ErrBadState)
	}
	var buf [12]byte
	if _, err := rand.Read(buf[:]); err != nil {
		return nil, err
	}
	rec := &SelectionRecord{Ref: "sel-" + hex.EncodeToString(buf[:]), PrincipalRef: principalRef,
		ClientID: clientID, RealPath: realPath, DisplayPath: displayPath, Access: access,
		IssuedAt:  now.UTC().Format(time.RFC3339Nano),
		ExpiresAt: now.Add(SelectionTTL).UTC().Format(time.RFC3339Nano)}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.pruneLocked(now)
	if len(s.items) >= s.MaxItems {
		return nil, fmt.Errorf("%w: too many outstanding selections", ErrBadState)
	}
	s.items[rec.Ref] = rec
	if err := s.save(); err != nil {
		delete(s.items, rec.Ref)
		return nil, err
	}
	return rec, nil
}

// Consume validates ownership, expiry and single use, and marks the reference spent even when
// the caller later fails: a reference that was revealed to a client cannot be reused after a
// crash, because a second use would be indistinguishable from a replay.
func (s *SelectionStore) Consume(ref, principalRef, clientID string, now time.Time) (*SelectionRecord, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	rec, ok := s.items[ref]
	if !ok || rec == nil {
		return nil, ErrSelectionUnknown
	}
	if rec.PrincipalRef != principalRef || rec.ClientID != clientID {
		return nil, ErrSelectionForeign
	}
	exp, err := time.Parse(time.RFC3339Nano, rec.ExpiresAt)
	if err != nil {
		return nil, fmt.Errorf("%w: unreadable selection expiry", ErrBadState)
	}
	if !now.UTC().Before(exp.UTC()) {
		delete(s.items, ref)
		_ = s.save()
		return nil, ErrSelectionExpired
	}
	if rec.Used {
		return nil, ErrSelectionUsed
	}
	rec.Used = true
	if err := s.save(); err != nil {
		rec.Used = false
		return nil, err
	}
	out := *rec
	return &out, nil
}

// Withdraw removes a reference that was issued during a call the host then refused. A client
// that never received the reference cannot redeem it, and leaving it live would let a later
// frame spend state the host already told the caller did not happen.
func (s *SelectionStore) Withdraw(ref string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.items, ref)
	_ = s.save()
}

func (s *SelectionStore) Outstanding() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.items)
}

func (s *SelectionStore) pruneLocked(now time.Time) {
	for ref, rec := range s.items {
		exp, err := time.Parse(time.RFC3339Nano, rec.ExpiresAt)
		if err != nil || !now.UTC().Before(exp.UTC()) {
			delete(s.items, ref)
		}
	}
}
