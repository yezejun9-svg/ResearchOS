package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"unsafe"

	"golang.org/x/sys/windows"

	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

// Called before ordinary control initialization. It neither starts a listener
// nor loads real credentials, a provider, coordinator or service capability.
func runFixtureControlReplay(args []string) (bool, error) {
	if len(args) == 0 || args[0] != "--fixture-control-replay" {
		return false, nil
	}
	if len(args) != 2 {
		return true, fmt.Errorf("one fixture replay request required")
	}
	return true, fixtureControlReplay(args[1])
}

func replayPlain(path string) error {
	if !filepath.IsAbs(path) {
		return fmt.Errorf("absolute replay path required")
	}
	name, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return err
	}
	h, err := windows.CreateFile(name, windows.FILE_READ_ATTRIBUTES, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_BACKUP_SEMANTICS|windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return err
	}
	defer windows.CloseHandle(h)
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(h, &info); err != nil {
		return err
	}
	if info.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 {
		return fmt.Errorf("replay reparse leaf refused")
	}
	// The host has copied every ancestor into a fresh tree while rejecting
	// reparses. AppContainer intentionally cannot query C:\Users metadata, so
	// do not demand ancestor enumeration or grant it broader filesystem access.
	return nil
}

func replayRead(path string, limit int64) ([]byte, error) {
	if err := replayPlain(path); err != nil {
		return nil, err
	}
	info, err := os.Stat(path)
	if err != nil || !info.Mode().IsRegular() || info.Size() > limit {
		return nil, fmt.Errorf("bounded regular replay file required")
	}
	return os.ReadFile(path)
}

// The replay output is a freshly created AppContainer-only clone. Keep the
// same native share-mode-zero coordinator lock without enumerating ancestors
// outside the sandbox. Ordinary control still uses its canonical root lease.
func replayOutputLease(data string) (*os.File, error) {
	if err := replayPlain(data); err != nil {
		return nil, err
	}
	path := filepath.Join(data, "coordinator.lock")
	name, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return nil, err
	}
	h, err := windows.CreateFile(name, windows.GENERIC_READ|windows.GENERIC_WRITE, 0, nil, windows.CREATE_NEW, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if err != nil {
		return nil, err
	}
	return os.NewFile(uintptr(h), path), nil
}

func fixtureControlReplay(requestPath string) error {
	token, err := windows.OpenCurrentProcessToken()
	if err != nil {
		return err
	}
	var appContainer, size uint32
	const tokenIsAppContainer = 29 // TOKEN_INFORMATION_CLASS from Windows SDK winnt.h.
	err = windows.GetTokenInformation(token, tokenIsAppContainer, (*byte)(unsafe.Pointer(&appContainer)), uint32(unsafe.Sizeof(appContainer)), &size)
	token.Close()
	if err != nil || appContainer != 1 {
		return fmt.Errorf("fixture control replay requires AppContainer")
	}
	if err := replayPlain(requestPath); err != nil {
		return err
	}
	input := filepath.Dir(requestPath)
	output, err := os.Getwd()
	if err != nil {
		return err
	}
	if err = replayPlain(output); err != nil {
		return err
	}
	if filepath.Base(requestPath) != "current-case.json" || filepath.Base(input) != "input" || filepath.Base(output) != "output" || !strings.EqualFold(filepath.Dir(input), filepath.Dir(output)) {
		return fmt.Errorf("replay requires isolated sibling input/output roots")
	}
	entries, err := os.ReadDir(output)
	if err != nil || len(entries) != 0 {
		return fmt.Errorf("empty replay output required")
	}
	raw, err := replayRead(requestPath, 64*1024)
	if err != nil {
		return err
	}
	var request evolution.ControlRequest
	if err = evolution.StrictControlJSON(raw, &request); err != nil {
		return err
	}
	if err = evolution.ValidateControlCase(request.Case, request.Binding); err != nil {
		return err
	}
	bundle := evolution.ControlBundle{Binding: request.Binding, Files: map[string][]byte{}}
	for name := range evolution.ControlReleaseHashes() {
		b, e := replayRead(filepath.Join(input, filepath.FromSlash(name)), 2*1024*1024)
		if e != nil {
			return e
		}
		bundle.Files[name] = b
	}
	bundle.Files["snapshot.sqlite"], err = replayRead(filepath.Join(input, "snapshot.sqlite"), 32*1024*1024)
	if err != nil {
		return err
	}
	if err = bundle.Validate(); err != nil {
		return err
	}
	data := filepath.Join(output, "replay-data")
	if err = os.Mkdir(data, 0700); err != nil {
		return err
	}
	path := filepath.Join(data, "researchos.sqlite")
	if err = os.WriteFile(path, bundle.Files["snapshot.sqlite"], 0600); err != nil {
		return err
	}
	lease, err := replayOutputLease(data)
	if err != nil {
		return err
	}
	defer lease.Close()
	db, err := store.Open(path)
	if err != nil {
		return err
	}
	defer db.Close()
	state, err := evolution.ControlDatabaseHash(db)
	if err != nil || state != request.Binding.ProjectionHash {
		return fmt.Errorf("replay projection differs from frozen host binding")
	}
	service, err := domain.New(db, filepath.Join(input, "spec/v2.0/contracts"), filepath.Join(input, "migrations/sqlite/0002_domain.sql"))
	if err != nil {
		return err
	}
	result := evolution.ControlReplayResult{Binding: request.Binding, CaseID: request.Case.ID, Results: []evolution.ControlHTTPResult{}}
	handler := service.Handler()
	for _, step := range request.Case.Steps {
		r := httptest.NewRequest(step.Method, "http://fixture.invalid"+step.Path, bytes.NewReader(step.Body))
		if step.Authenticated {
			r.Header.Set("Authorization", "Bearer "+evolution.ControlCredential)
		}
		if len(step.Body) > 0 {
			r.Header.Set("Content-Type", "application/json")
		}
		if step.ETag != "" {
			r.Header.Set("If-Match", step.ETag)
		}
		if step.IdempotencyKey != "" {
			r.Header.Set("Idempotency-Key", step.IdempotencyKey)
		}
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, r)
		if w.Body.Len() > 1024*1024 {
			return fmt.Errorf("bounded replay response required")
		}
		headers := map[string]string{}
		for _, name := range []string{"Content-Type", "Cache-Control", "ETag", "X-ResearchOS-Principal-ID"} {
			if value := w.Header().Get(name); value != "" {
				headers[name] = value
			}
		}
		result.Results = append(result.Results, evolution.ControlHTTPResult{Status: w.Code, Headers: headers, Body: append(json.RawMessage(nil), w.Body.Bytes()...)})
	}
	if _, err = db.Exec("PRAGMA wal_checkpoint(TRUNCATE)"); err != nil {
		return err
	}
	if err = db.Close(); err != nil {
		return err
	}
	if err = lease.Close(); err != nil {
		return err
	}
	return json.NewEncoder(os.Stdout).Encode(result)
}
