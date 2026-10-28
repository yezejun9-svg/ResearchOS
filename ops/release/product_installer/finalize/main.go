// Static P1a finalization of an already staged, fresh Windows product tree.
// No product process, user data, registration, or existing installation is touched.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"syscall"
)

// Bound by build.py -ldflags. An unbound development build must fail closed.
var trustedManifestSHA256 string

const verifierPath = "apps/desktop/resources/control/runtime-verifier-installation.json"
const markerPath = "installed-product.json"
const candidateSHA256 = "c785a1bb1b328cac9c37794e8fbd7cf607c4e4322f80963ea203436ba4e2f8e3"
const sourceCommit = "5c4c94022bd92da68ef544f2779527bfe065c428"

var roles = []string{"cli", "control", "electron", "verifier", "validator"}

type row struct {
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
	Bytes  int64  `json:"bytes"`
}
type binary struct {
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
}
type payload struct {
	Schema                string            `json:"schema"`
	CandidateMarkerSHA256 string            `json:"candidate_marker_sha256"`
	Metadata              map[string]any    `json:"metadata"`
	Binaries              map[string]binary `json:"binaries"`
	Files                 []row             `json:"files"`
	VerifierTemplate      map[string]any    `json:"verifier_template"`
}

func shaBytes(b []byte) string { s := sha256.Sum256(b); return hex.EncodeToString(s[:]) }
func validSHA(s string) bool {
	if len(s) != 64 {
		return false
	}
	for _, c := range s {
		if c < '0' || c > '9' && c < 'a' || c > 'f' {
			return false
		}
	}
	return true
}
func validRelative(p string) bool {
	if p == "" || strings.Contains(p, `\`) || strings.HasPrefix(p, "/") {
		return false
	}
	for _, part := range strings.Split(p, "/") {
		if part == "" || part == "." || part == ".." || strings.Contains(part, ":") ||
			strings.HasSuffix(part, ".") || strings.HasSuffix(part, " ") {
			return false
		}
	}
	return true
}
func parseManifest(raw []byte, bound string) (*payload, error) {
	if !validSHA(bound) || shaBytes(raw) != bound {
		return nil, errors.New("unbound or changed payload manifest")
	}
	var p payload
	decoder := json.NewDecoder(strings.NewReader(string(raw)))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&p); err != nil {
		return nil, err
	}
	var trailing any
	if err := decoder.Decode(&trailing); err != io.EOF {
		return nil, errors.New("trailing manifest data")
	}
	if p.Schema != "researchos.static-payload/1" || p.CandidateMarkerSHA256 != candidateSHA256 ||
		p.Metadata["source_commit"] != sourceCommit || p.Metadata["schema"] != "researchos.product-layout/1" ||
		p.Metadata["mode"] != "OWNED_PRODUCT_LAYOUT_NOT_INSTALLER" ||
		p.Metadata["product_version"] != "2.4.0" || p.Metadata["client_protocol"] != "researchos-client/2" ||
		p.Metadata["schema_version"] != float64(24) || !validSHA(fmt.Sprint(p.Metadata["source_digest"])) ||
		len(p.Files) < 100 || len(p.Binaries) != 5 {
		return nil, errors.New("unsupported payload provenance")
	}
	if p.VerifierTemplate["schema"] != "researchos.runtime-verifier-installation.v1" ||
		p.VerifierTemplate["source_commit"] != sourceCommit ||
		p.VerifierTemplate["service_id"] != "researchos.runtime-qualification-verifier.v1" ||
		p.VerifierTemplate["protocol"] != "researchos.runtime-verifier/1" ||
		p.VerifierTemplate["executable"] != nil || p.VerifierTemplate["executable_hash"] != nil {
		return nil, errors.New("invalid verifier template")
	}
	args, ok := p.VerifierTemplate["arguments"].([]any)
	if !ok || len(args) != 0 {
		return nil, errors.New("verifier arguments changed")
	}
	previous := ""
	names := map[string]row{}
	for _, r := range p.Files {
		if !validRelative(r.Path) || !validSHA(r.SHA256) || r.Bytes < 0 || r.Path <= previous ||
			r.Path == verifierPath || r.Path == markerPath {
			return nil, fmt.Errorf("invalid payload row: %q", r.Path)
		}
		lower := strings.ToLower(r.Path)
		if _, exists := names[lower]; exists {
			return nil, fmt.Errorf("case alias: %s", r.Path)
		}
		names[lower] = r
		previous = r.Path
	}
	for _, role := range roles {
		b, exists := p.Binaries[role]
		r, found := names[strings.ToLower(b.Path)]
		if !exists || !found || b.Path != r.Path || !validSHA(b.SHA256) || b.SHA256 != r.SHA256 {
			return nil, fmt.Errorf("binary role mismatch: %s", role)
		}
	}
	return &p, nil
}

// checkPhysical validates spelling and redirection on every existing component.
func checkPhysical(path string, wantDir bool) error {
	clean := filepath.Clean(path)
	if !filepath.IsAbs(path) || clean != path {
		return errors.New("noncanonical absolute path")
	}
	volume := filepath.VolumeName(clean)
	if len(volume) != 2 || volume[1] != ':' || volume[0] < 'A' || volume[0] > 'Z' {
		return errors.New("canonical uppercase drive path required")
	}
	current := volume + `\`
	rest := strings.TrimPrefix(clean, current)
	parts := strings.Split(rest, `\`)
	for i, part := range parts {
		if part == "" || part == "." || part == ".." || strings.HasSuffix(part, ".") || strings.HasSuffix(part, " ") {
			return errors.New("noncanonical path component")
		}
		entries, err := os.ReadDir(current)
		if err != nil {
			return err
		}
		exact := false
		for _, item := range entries {
			if item.Name() == part {
				exact = true
				break
			}
		}
		if !exact {
			return fmt.Errorf("case alias or missing path: %s", part)
		}
		current = filepath.Join(current, part)
		info, err := os.Lstat(current)
		if err != nil {
			return err
		}
		if info.Mode()&os.ModeSymlink != 0 {
			return errors.New("redirected path")
		}
		if attrs, ok := info.Sys().(*syscall.Win32FileAttributeData); ok &&
			attrs.FileAttributes&syscall.FILE_ATTRIBUTE_REPARSE_POINT != 0 {
			return errors.New("reparse path")
		}
		if i < len(parts)-1 || wantDir {
			if !info.IsDir() {
				return errors.New("expected directory")
			}
		} else if !info.Mode().IsRegular() {
			return errors.New("expected regular file")
		}
	}
	return nil
}

func fileRow(root, name string) (row, error) {
	full := filepath.Join(root, filepath.FromSlash(name))
	if err := checkPhysical(full, false); err != nil {
		return row{}, err
	}
	file, err := os.Open(full)
	if err != nil {
		return row{}, err
	}
	defer file.Close()
	var info syscall.ByHandleFileInformation
	if err = syscall.GetFileInformationByHandle(syscall.Handle(file.Fd()), &info); err != nil {
		return row{}, err
	}
	if info.NumberOfLinks != 1 {
		return row{}, errors.New("hardlink file refused")
	}
	hash := sha256.New()
	n, err := io.Copy(hash, file)
	if err != nil {
		return row{}, err
	}
	return row{Path: name, SHA256: hex.EncodeToString(hash.Sum(nil)), Bytes: n}, nil
}

func verifyTree(root string, expected []row) error {
	if err := checkPhysical(root, true); err != nil {
		return err
	}
	wanted := make(map[string]row, len(expected))
	dirs := map[string]bool{".": true}
	for _, r := range expected {
		wanted[r.Path] = r
		dir := filepath.ToSlash(filepath.Dir(r.Path))
		for dir != "." {
			dirs[dir] = true
			dir = filepath.ToSlash(filepath.Dir(dir))
		}
	}
	count := 0
	err := filepath.WalkDir(root, func(path string, item os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if path == root {
			return nil
		}
		rel, err := filepath.Rel(root, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		if item.IsDir() {
			if !dirs[rel] {
				return fmt.Errorf("extra directory: %s", rel)
			}
			return checkPhysical(path, true)
		}
		r, exists := wanted[rel]
		if !exists {
			return fmt.Errorf("extra or aliased file: %s", rel)
		}
		actual, err := fileRow(root, rel)
		if err != nil {
			return err
		}
		if actual != r {
			return fmt.Errorf("changed file: %s", rel)
		}
		count++
		return nil
	})
	if err != nil {
		return err
	}
	if count != len(expected) {
		return fmt.Errorf("missing payload files: %d of %d", count, len(expected))
	}
	return nil
}

func inventoryDigest(rows []row) string {
	var b strings.Builder
	b.WriteString("researchos.product-inventory/1\n")
	for _, r := range rows {
		fmt.Fprintf(&b, "%s\n%s\n%d\n", r.Path, r.SHA256, r.Bytes)
	}
	return shaBytes([]byte(b.String()))
}
func installationID(root string, p *payload, inventory string) string {
	fields := []string{"researchos.product-layout/1", root, sourceCommit,
		p.Metadata["source_digest"].(string), inventory, "2.4.0", "researchos-client/2", "24"}
	for _, role := range roles {
		fields = append(fields, p.Binaries[role].SHA256)
	}
	return shaBytes([]byte(strings.Join(fields, "\n") + "\n"))
}
func jsonLine(v any) ([]byte, error) {
	raw, err := json.Marshal(v)
	return append(raw, '\n'), err
}
func writeNew(path string, raw []byte) error {
	file, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	if _, err = file.Write(raw); err == nil {
		err = file.Sync()
	}
	closeErr := file.Close()
	if err != nil {
		return err
	}
	return closeErr
}

// MoveFileW fails if target exists. os.Rename replaces an existing target on
// Windows, so it cannot publish the marker under the create-new contract.
func publishMarkerNoReplace(temp, target string, beforeMove func() error) error {
	if beforeMove != nil {
		if err := beforeMove(); err != nil {
			return err
		}
	}
	from, err := syscall.UTF16PtrFromString(temp)
	if err != nil {
		return err
	}
	to, err := syscall.UTF16PtrFromString(target)
	if err != nil {
		return err
	}
	return syscall.MoveFile(from, to)
}

func finalize(root, manifest string, bound string) (string, error) {
	raw, err := os.ReadFile(manifest)
	if err != nil {
		return "", err
	}
	p, err := parseManifest(raw, bound)
	if err != nil {
		return "", err
	}
	if err = verifyTree(root, p.Files); err != nil {
		return "", err
	}
	verifier := make(map[string]any, len(p.VerifierTemplate)+2)
	for key, value := range p.VerifierTemplate {
		verifier[key] = value
	}
	verifier["executable"] = filepath.Join(root, filepath.FromSlash(p.Binaries["verifier"].Path))
	verifier["executable_hash"] = "sha256:" + p.Binaries["verifier"].SHA256
	verifierRaw, err := jsonLine(verifier)
	if err != nil {
		return "", err
	}
	verifierFull := filepath.Join(root, filepath.FromSlash(verifierPath))
	if err = writeNew(verifierFull, verifierRaw); err != nil {
		return "", err
	}
	verifierRow, err := fileRow(root, verifierPath)
	if err != nil {
		return "", err
	}
	rows := append(append([]row{}, p.Files...), verifierRow)
	sort.Slice(rows, func(i, j int) bool { return rows[i].Path < rows[j].Path })
	if err = verifyTree(root, rows); err != nil {
		return "", err
	}
	marker := make(map[string]any, len(p.Metadata)+5)
	for key, value := range p.Metadata {
		marker[key] = value
	}
	marker["binaries"] = p.Binaries
	marker["files"] = rows
	marker["install_root"] = root
	inventory := inventoryDigest(rows)
	marker["inventory_digest"] = inventory
	marker["installation_id"] = installationID(root, p, inventory)
	markerRaw, err := jsonLine(marker)
	if err != nil {
		return "", err
	}
	temp := filepath.Join(root, ".installed-product.json.tmp")
	if err = writeNew(temp, markerRaw); err != nil {
		return "", err
	}
	if err = publishMarkerNoReplace(temp, filepath.Join(root, markerPath), nil); err != nil {
		return "", err
	}
	return marker["installation_id"].(string), nil
}

func main() {
	root := flag.String("root", "", "fresh absolute staged product root")
	manifest := flag.String("manifest", "", "approved payload manifest")
	flag.Parse()
	if !validSHA(trustedManifestSHA256) || *root == "" || *manifest == "" {
		fmt.Fprintln(os.Stderr, "refused: bound manifest and explicit root required")
		os.Exit(2)
	}
	id, err := finalize(*root, *manifest, trustedManifestSHA256)
	if err != nil {
		fmt.Fprintln(os.Stderr, "refused:", err)
		os.Exit(1)
	}
	fmt.Printf("%s\n", id)
}
