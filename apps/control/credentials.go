package main

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/domain"
	"time"
)

// Local OS administration only: no HTTP route, automatic role expansion or
// replacement of existing principals. The output file is private before writing.
func adminCredential(s *domain.Service, definition, id, output string) error {
	if output == "" || (definition == "") == (id == "") {
		return errors.New("one principal source and a new credential-file required")
	}
	var p domain.Principal
	if definition != "" {
		input, e := os.Open(definition)
		if e != nil {
			return e
		}
		defer input.Close()
		decoder := json.NewDecoder(io.LimitReader(input, 65537))
		decoder.DisallowUnknownFields()
		if e = decoder.Decode(&p); e != nil {
			return errors.New("invalid principal definition")
		}
		var extra any
		if decoder.Decode(&extra) != io.EOF {
			return errors.New("one principal definition required")
		}
		id = p.ID
	}
	if e := os.MkdirAll(filepath.Dir(output), 0700); e != nil {
		return e
	}
	f, e := os.OpenFile(output, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		return e
	}
	complete := false
	defer func() {
		f.Close()
		if !complete {
			os.Remove(output)
		}
	}()
	if e = privateFile(output); e != nil {
		return e
	}
	if definition != "" {
		if e = s.ProvisionPrincipal(context.Background(), p); e != nil {
			return e
		}
	} else {
		var active int
		if e = s.DB.QueryRow("SELECT count(*) FROM auth_principals WHERE id=? AND revoked=0", id).Scan(&active); e != nil {
			return e
		}
		if active != 1 {
			return errors.New("active principal required")
		}
	}
	token, e := s.IssueCredential(context.Background(), id, 15*time.Minute)
	if e != nil {
		return e
	}
	defer func() {
		if !complete {
			s.DB.Exec("UPDATE auth_credentials SET revoked=1 WHERE token_hash=?", domain.Digest([]byte(token)))
		}
	}()
	if e = json.NewEncoder(f).Encode(map[string]any{"token": token, "principal_id": id, "expires_in_seconds": 900}); e != nil {
		return e
	}
	if e = f.Sync(); e != nil {
		return e
	}
	complete = true
	return nil
}
