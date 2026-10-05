package retrieval

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

const MaxSnapshotBytes = 8 << 20

// ReadFile opens a path through the OS root handle. A lexical check alone is
// insufficient: Root.Open also refuses links and Windows junctions that escape.
func ReadFile(rootPath, relative string) ([]byte, error) {
	return readFile(rootPath, "", relative)
}

// Identity is a durable volume/file identity for the opened root directory.
func Identity(rootPath string) (string, error) {
	root, err := os.OpenRoot(rootPath)
	if err != nil {
		return "", err
	}
	defer root.Close()
	return rootIdentity(root)
}

// ReadFileBound verifies the directory identity on the same Root handle used
// to open the child. Replacing the registered path with a junction cannot
// change the authorized root to a different directory.
func ReadFileBound(rootPath, expectedIdentity, relative string) ([]byte, error) {
	if expectedIdentity == "" {
		return nil, fmt.Errorf("registered root identity missing")
	}
	return readFile(rootPath, expectedIdentity, relative)
}

func readFile(rootPath, expectedIdentity, relative string) ([]byte, error) {
	if relative == "" || relative == "." || !filepath.IsLocal(relative) {
		return nil, fmt.Errorf("path is not root-relative")
	}
	root, err := os.OpenRoot(rootPath)
	if err != nil {
		return nil, err
	}
	defer root.Close()
	if expectedIdentity != "" {
		actual, identityErr := rootIdentity(root)
		if identityErr != nil {
			return nil, identityErr
		}
		if actual != expectedIdentity {
			return nil, fmt.Errorf("registered root identity changed")
		}
	}
	file, err := root.Open(relative)
	if err != nil {
		return nil, classifyOpen(root, relative, err)
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > MaxSnapshotBytes {
		return nil, fmt.Errorf("snapshot must be a regular file of at most %d bytes", MaxSnapshotBytes)
	}
	data, err := io.ReadAll(io.LimitReader(file, MaxSnapshotBytes+1))
	if err != nil {
		return nil, err
	}
	if len(data) > MaxSnapshotBytes {
		return nil, fmt.Errorf("snapshot grew beyond the byte limit")
	}
	return data, nil
}

// classifyOpen names which containment guard refused, so an audit can tell a link that
// escapes apart from an absent file. os.Root answers both with the same *PathError, and a
// refusal that only reads "not found" would let an escape look like ordinary absence.
//
// The whole path cannot be inspected at once: when an intermediate component is the link,
// Lstat on the full path fails for the same reason Open did, and the two cases collapse
// back into one message. So each component is inspected in turn and the first one that is
// not a plain directory names the guard. Lstat is used deliberately because Stat would
// follow the very link being reported.
func classifyOpen(root *os.Root, relative string, openErr error) error {
	parts := strings.Split(filepath.ToSlash(relative), "/")
	for i := range parts {
		prefix := strings.Join(parts[:i+1], "/")
		info, err := root.Lstat(prefix)
		if err != nil {
			if i == len(parts)-1 {
				return fmt.Errorf("path is not present inside the registered root: %w", openErr)
			}
			return fmt.Errorf("path component %q could not be inspected inside the registered root: %w", prefix, openErr)
		}
		if info.Mode()&os.ModeSymlink != 0 {
			target, linkErr := root.Readlink(prefix)
			if linkErr != nil {
				target = "unreadable"
			}
			return fmt.Errorf("path component %q is a symbolic link to %q; snapshots must be a regular file inside the registered root", prefix, target)
		}
		if !info.Mode().IsRegular() && !info.Mode().IsDir() {
			return fmt.Errorf("path component %q is a link or reparse point with irregular mode %s; snapshots must be a regular file inside the registered root", prefix, info.Mode())
		}
	}
	return fmt.Errorf("registered root refused the path: %w", openErr)
}
