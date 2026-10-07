from pathlib import Path
import hashlib,json
W=Path(r'D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-session-list-proof-r312');P=W/'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex/907592b8e03d433da7de947435274481';f=W/'internal/api/v2_sessions_test.go';b=f.read_bytes();assert hashlib.sha256(b).hexdigest()=='e095e2be7418d4ca7bb677e33679f25e377e084bec305f538799baf8523ea9b0';(P/'source.before.go').write_bytes(b)
s=b.decode();s=s.replace('\t"net/http/httptest"\n','\t"net/http/httptest"\n\t"net/url"\n',1)
a=s.index('func (f *sessionListFixture) closeEvidence(');z=s.index('\nfunc TestSessionListHTTPOriginalContextIdentity',a)
replacement='''// readonlyCopyOpen is only for a fully closed, standalone evidence copy.
// URL.Path escapes spaces, non-ASCII characters and URI metacharacters.
func readonlyCopyOpen(path string) (*sql.DB, error) {
	absolute, err := filepath.Abs(path)
	if err != nil {
		return nil, err
	}
	uriPath := filepath.ToSlash(absolute)
	if !strings.HasPrefix(uriPath, "/") {
		uriPath = "/" + uriPath
	}
	u := url.URL{Scheme: "file", Path: uriPath}
	u.RawQuery = url.Values{"mode": {"ro"}, "immutable": {"1"}}.Encode()
	db, err := sql.Open("sqlite", u.String())
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	if err = db.Ping(); err != nil {
		if closeErr := db.Close(); closeErr != nil {
			return nil, fmt.Errorf("open readonly copy: %v; close: %w", err, closeErr)
		}
		return nil, err
	}
	return db, nil
}

func (f *sessionListFixture) closeEvidence(t *testing.T) {
	t.Helper()
	if f.server != nil {
		f.server.Close()
	}
	if f.db == nil {
		return
	}
	open := sessionListCaptureRows(t, f.db)
	sessionListJSON(t, f.dir, "post-open.rows.json", open)
	fileHashes := func() map[string]any {
		out := map[string]any{}
		for _, s := range []string{"", "-wal", "-shm"} {
			b, e := os.ReadFile(f.dbPath + s)
			if os.IsNotExist(e) {
				out[s] = nil
			} else if e != nil {
				t.Error(e)
			} else {
				out[s] = domain.Object{"bytes": len(b), "sha256": sessionListDigest(b)}
			}
		}
		return out
	}
	sidecarsAbsent := func(path, receipt string) bool {
		facts := domain.Object{}
		absent := true
		for _, suffix := range []string{"-wal", "-shm"} {
			_, err := os.Lstat(path + suffix)
			if os.IsNotExist(err) {
				facts[suffix] = domain.Object{"exists": false, "error": nil}
			} else if err != nil {
				facts[suffix] = domain.Object{"exists": nil, "error": err.Error()}
				absent = false
				t.Error(err)
			} else {
				facts[suffix] = domain.Object{"exists": true, "error": nil}
				absent = false
				t.Errorf("standalone closed evidence has sidecar %s", path+suffix)
			}
		}
		sessionListJSON(t, f.dir, receipt, facts)
		return absent
	}
	sessionListJSON(t, f.dir, "before-close.files.json", fileHashes())
	if e := f.db.Close(); e != nil {
		t.Error(e)
		return
	}
	sessionListJSON(t, f.dir, "closed-original.files.json", fileHashes())
	if !sidecarsAbsent(f.dbPath, "closed-original.sidecars.json") {
		return
	}
	raw, e := os.ReadFile(f.dbPath)
	if e != nil {
		t.Error(e)
		return
	}
	// sessionListSave uses O_EXCL: never reuse an earlier evidence copy.
	sessionListSave(t, f.dir, "closed.sqlite", raw)
	closedPath := filepath.Join(f.dir, "closed.sqlite")
	if !sidecarsAbsent(closedPath, "closed-copy.before.sidecars.json") {
		return
	}
	db, e := readonlyCopyOpen(closedPath)
	if e != nil {
		t.Error(e)
		sidecarsAbsent(closedPath, "closed-copy.after.sidecars.json")
		return
	}
	var closed sessionListRows
	copySidecarsAbsent := false
	func() {
		defer func() {
			if e := db.Close(); e != nil {
				t.Error(e)
			}
			copySidecarsAbsent = sidecarsAbsent(closedPath, "closed-copy.after.sidecars.json")
		}()
		closed = sessionListCaptureRows(t, db)
	}()
	sessionListJSON(t, f.dir, "closed.rows.json", closed)
	equal := reflect.DeepEqual(open, closed)
	after, e := os.ReadFile(closedPath)
	if e != nil {
		t.Error(e)
	}
	byteEqual := bytes.Equal(raw, after)
	sessionListJSON(t, f.dir, "closed-proof.json", domain.Object{"all_table_schema_multisets_equal": equal, "closed_copy_bytes_unchanged_by_read": byteEqual, "closed_copy_sha256": sessionListDigest(after), "closed_copy_sidecars_absent": copySidecarsAbsent, "HTTP_calls_including_setup": f.calls, "SDK_worker_model_external_paid": 0, "fixture_ports": "SYNTHETIC_METADATA_AND_BINDING_ONLY", "case_failed": t.Failed()})
	if !equal || !byteEqual || !copySidecarsAbsent {
		t.Error("closed SQLite evidence drift")
	}
}
'''
s=s[:a]+replacement+s[z:];f.write_bytes(s.encode());(P/'source.edited.go').write_bytes(f.read_bytes());print(json.dumps({'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':len(f.read_bytes())}))
