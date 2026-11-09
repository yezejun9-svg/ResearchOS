package main

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
)

func runtimeOS() string { return runtime.GOOS }

func mustMkTree(base string) {
	os.MkdirAll(filepath.Join(base, "notes"), 0o755)
	os.WriteFile(filepath.Join(base, "notes", "a.md"), []byte("ok"), 0o600)
}

// diskLeaks lists files under dir that still carry the secret. Every transport encoding counts:
// a store that "protects" material by base64-ing it leaves exactly the same bytes recoverable by
// anyone who can read the file, so scanning only for the raw ASCII would pass that store.
func diskLeaks(dir, secret string) []string {
	variants := encodingsOf(secret)
	leaks := []string{}
	filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info == nil || info.IsDir() {
			return nil
		}
		f, e := os.Open(path)
		if e != nil {
			return nil
		}
		defer f.Close()
		b, _ := io.ReadAll(io.LimitReader(f, 1<<20))
		text := string(b)
		for _, v := range variants {
			if strings.Contains(text, v) {
				leaks = append(leaks, filepath.Base(path)+"="+v[:12])
				break
			}
		}
		return nil
	})
	return leaks
}

// encodingsOf returns the secret plus the forms a lazy "protection" would leave behind.
func encodingsOf(secret string) []string {
	raw := []byte(secret)
	return []string{
		secret,
		base64.StdEncoding.EncodeToString(raw),
		base64.URLEncoding.EncodeToString(raw),
		base64.RawStdEncoding.EncodeToString(raw),
		hex.EncodeToString(raw),
		strings.ToUpper(hex.EncodeToString(raw)),
	}
}

func randomToken() string {
	var b [12]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "fallback-token-material-1"
	}
	return "sk-QUAL-" + hex.EncodeToString(b[:])
}

// statusCmd builds one host.status envelope with a fresh command id, which is how the check asks
// the HTTP layer whether a credential is still live.
func statusCmd(id string) string {
	return `{"protocol_version":"researchos-client/2","command_id":"` + id +
		`","client_id":"cli-a","project_id":null,"session_id":null,"expected_revision":null,` +
		`"writer_epoch":null,"method":"host.status","payload":{}}`
}

// vaultRecord reads one stored credential record so the check can grade the protection itself
// rather than trusting the store's word. The wrapped field is a reference-shaped blob; nothing
// here returns plaintext to the caller.
func vaultRecord(dir, ref string) (map[string]any, error) {
	raw, err := os.ReadFile(filepath.Join(dir, "credentials", ref+".dpapi"))
	if err != nil {
		return nil, err
	}
	var rec map[string]any
	if err := json.Unmarshal(raw, &rec); err != nil {
		return nil, err
	}
	return rec, nil
}

// tamperVaultRecord flips one byte inside the protected blob and writes the record back, which is
// how the check proves the blob carries integrity rather than being an encoding of the material.
func tamperVaultRecord(dir, ref string) error {
	rec, err := vaultRecord(dir, ref)
	if err != nil {
		return err
	}
	b64, _ := rec["wrapped"].(string)
	buf, err := base64.StdEncoding.DecodeString(b64)
	if err != nil {
		return err
	}
	if len(buf) == 0 {
		return fmt.Errorf("empty wrapped blob for %s", ref)
	}
	mid := len(buf) / 2
	buf[mid] ^= 0x01
	rec["wrapped"] = base64.StdEncoding.EncodeToString(buf)
	out, err := json.Marshal(rec)
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(dir, "credentials", ref+".dpapi"), out, 0o600)
}

// sourceReferences counts how often a package tree mentions forbidden access patterns; the host
// must never read command-line arguments or the environment for credential material.
func sourceReferences(roots, needles []string) int {
	count := 0
	for _, r := range roots {
		root := filepath.Join(repoRoot(), filepath.FromSlash(r))
		filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
			if err != nil || info == nil || info.IsDir() || !strings.HasSuffix(path, ".go") {
				return nil
			}
			b, _ := os.ReadFile(path)
			for _, n := range needles {
				if strings.Contains(string(b), n) {
					count++
				}
			}
			return nil
		})
	}
	return count
}

func decodeEnvelopeStrict(raw string) (*domain.Envelope, error) {
	return domain.DecodeEnvelope([]byte(raw))
}

func describe(v any) string { return fmt.Sprintf("%v", v) }

// seedSession maps one v2 client session onto the existing authority, exactly the way the
// product's own session creation does, so the HTTP chain runs against real state.
func seedSession(ctx context.Context, h *harness, id string) error {
	now := time.Now().UTC()
	s := domain.ClientSession{ID: id, ProjectID: "p1", Revision: 1, CreatedAt: now, UpdatedAt: now,
		WriterEpoch: 1, WriterClientID: "cli-b", UpstreamSession: "up-" + id,
		WorkspaceRef: strp("ws-p1"), Title: strp("w17 chain"), ModelConfigRef: strp("model-x"),
		CoreBuildID: strp("core-w17"), Protocol: domain.ClientSessionProtocol, ResumeExplicit: 1,
		LeaseExpiresAt: timep(now.Add(time.Hour))}
	tx, err := h.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err := domain.MapClientSession(ctx, tx, s); err != nil {
		return err
	}
	return tx.Commit()
}

func strp(s string) *string        { return &s }
func timep(t time.Time) *time.Time { return &t }
