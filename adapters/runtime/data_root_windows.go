//go:build windows

package runtime

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"sync"
)

// DataRootLease is an opaque, process-local owner of the existing exclusive
// coordinator.lock. The control process acquires it before opening SQLite and
// the in-process coordinator may borrow it without opening a second writer.
type DataRootLease struct {
	mu       sync.Mutex
	root     string
	file     *os.File
	closed   bool
	borrowed bool
}

func AcquireDataRootLease(directory string) (*DataRootLease, error) {
	f, e := LockDataRoot(directory)
	if e != nil {
		return nil, e
	}
	root, e := filepath.Abs(directory)
	if e != nil {
		_ = f.Close()
		return nil, e
	}
	return &DataRootLease{root: filepath.Clean(root), file: f}, nil
}

func (l *DataRootLease) Root() string {
	if l == nil {
		return ""
	}
	return l.root
}

func (l *DataRootLease) Borrow(directory string) error {
	if l == nil {
		return errors.New("control data-root lease required")
	}
	root, e := filepath.Abs(directory)
	if e != nil {
		return e
	}
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.closed || l.file == nil || !strings.EqualFold(filepath.Clean(root), l.root) {
		return errors.New("control data-root lease unavailable or mismatched")
	}
	if l.borrowed {
		return errors.New("control data-root lease already borrowed")
	}
	if _, e = l.file.Stat(); e != nil {
		return e
	}
	l.borrowed = true
	return nil
}

func (l *DataRootLease) ReturnBorrow() error {
	if l == nil {
		return errors.New("control data-root lease required")
	}
	l.mu.Lock()
	defer l.mu.Unlock()
	if !l.borrowed {
		return errors.New("control data-root lease not borrowed")
	}
	l.borrowed = false
	return nil
}

func (l *DataRootLease) Close() error {
	if l == nil {
		return nil
	}
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.closed {
		return nil
	}
	if l.borrowed {
		return errors.New("control data-root lease still borrowed")
	}
	l.closed = true
	return l.file.Close()
}
