package retrieval

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
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
		return nil, err
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
