//go:build windows

// This keyless native fixture receives one arithmetic question and host paths
// for negative access probes. It contains no labels, dataset or credentials.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"syscall"
)

type question struct {
	Operands []int `json:"operands"`
}
type probe struct {
	Name string `json:"name"`
	Path string `json:"path"`
}
type request struct {
	Question         question `json:"question"`
	PrivateDirectory string   `json:"private_directory"`
	Probes           []probe  `json:"probes"`
}

func errorCode(err error) uint64 {
	var code syscall.Errno
	if errors.As(err, &code) {
		return uint64(code)
	}
	return 0
}
func main() {
	if len(os.Args) != 3 {
		os.Exit(90)
	}
	raw, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(91)
	}
	var r request
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&r); err != nil || len(r.Question.Operands) != 2 {
		os.Exit(92)
	}
	entries, err := os.ReadDir(filepath.Dir(os.Args[1]))
	if err != nil {
		os.Exit(93)
	}
	inputFiles := []string{}
	for _, entry := range entries {
		inputFiles = append(inputFiles, entry.Name())
	}
	results := []map[string]any{}
	for _, p := range r.Probes {
		body, readErr := os.ReadFile(p.Path)
		f, writeErr := os.OpenFile(p.Path, os.O_WRONLY, 0)
		written := 0
		if writeErr == nil {
			written, writeErr = f.Write([]byte("candidate-modified"))
			f.Close()
		}
		results = append(results, map[string]any{"name": p.Name, "path": p.Path, "read_code": errorCode(readErr), "read_error": fmt.Sprint(readErr), "read_bytes": len(body), "read_body": string(body), "write_code": errorCode(writeErr), "write_error": fmt.Sprint(writeErr), "written_bytes": written})
	}
	privateEntries, listErr := os.ReadDir(r.PrivateDirectory)
	result := map[string]any{"pid": os.Getpid(), "question": r.Question, "input_files": inputFiles, "input_raw": string(raw), "result": r.Question.Operands[0] + r.Question.Operands[1], "probes": results, "list_code": errorCode(listErr), "list_error": fmt.Sprint(listErr), "listed_entries": len(privateEntries)}
	out, err := json.Marshal(result)
	if err != nil {
		os.Exit(94)
	}
	if err = os.WriteFile(os.Args[2], out, 0600); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(95)
	}
	fmt.Println(string(out))
}
