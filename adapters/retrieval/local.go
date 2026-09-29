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
	if relative == "" || relative == "." || !filepath.IsLocal(relative) {
		return nil, fmt.Errorf("path is not root-relative")
	}
	root, err := os.OpenRoot(rootPath)
	if err != nil {
		return nil, err
	}
	defer root.Close()
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
