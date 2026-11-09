"""Pure-IO derivation of a trial-only readonly sealed-vault seam."""
import difflib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
repo = Path(r"D:\作品集\ResearchOS\research-os")
out = Path(__file__).resolve().parent

changes = {
    "internal/host/vault.go": [
        ('\tdir  string\n\tpath string\n',
         '\tdir  string\n\tpath string\n\treadOnly bool\n\tallowedRef string\n\tallowedProvider string\n'),
        ('func openVault(dir string) (*Vault, error) {',
         '''// openVaultReadOnly references one existing sealed record without copying,
// importing, revoking or changing the original vault directory.
func openVaultReadOnly(hostDir, ref, provider string) (*Vault, error) {
	if !filepath.IsAbs(hostDir) || ref == "" || provider == "" {
		return nil, ErrUnknownCredential
	}
	resolved, err := filepath.EvalSymlinks(hostDir)
	if err != nil || !strings.EqualFold(resolved, filepath.Clean(hostDir)) {
		return nil, ErrUnknownCredential
	}
	d := filepath.Join(resolved, "credentials")
	info, err := os.Lstat(d)
	if err != nil || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
		return nil, ErrUnknownCredential
	}
	canonicalCredentials, err := filepath.EvalSymlinks(d)
	if err != nil || !strings.EqualFold(canonicalCredentials, filepath.Clean(d)) {
		return nil, ErrUnknownCredential
	}
	for _, name := range []string{"index.json", ref + ".dpapi"} {
		path := filepath.Join(d, name)
		entry, err := os.Lstat(path)
		if err != nil || !entry.Mode().IsRegular() || entry.Mode()&os.ModeSymlink != 0 {
			return nil, ErrUnknownCredential
		}
	}
	v := &Vault{dir: d, path: filepath.Join(d, "index.json"), readOnly: true,
		allowedRef: ref, allowedProvider: provider}
	idx, err := v.load()
	if err != nil {
		return nil, err
	}
	found := false
	for _, known := range idx.Records {
		if known == ref { found = true }
	}
	if !found { return nil, ErrUnknownCredential }
	record, err := v.record(ref)
	if err != nil || record.Revoked || record.Provider != provider {
		return nil, ErrUnknownCredential
	}
	return v, nil
}

func openVault(dir string) (*Vault, error) {'''),
        ('\t}()\n\tif len(material) == 0 || len(material) > MaxCredentialBytes {',
         '\t}()\n\tif v.readOnly { return "", ErrCredentialProtected }\n\tif len(material) == 0 || len(material) > MaxCredentialBytes {'),
        ('func (v *Vault) record(ref string) (*vaultRecord, error) {\n',
         'func (v *Vault) record(ref string) (*vaultRecord, error) {\n\tif v.readOnly && ref != v.allowedRef { return nil, ErrUnknownCredential }\n'),
        ('\tif rec.Ref == "" || rec.Ref != ref {\n',
         '\tif rec.Ref == "" || rec.Ref != ref || v.readOnly && rec.Provider != v.allowedProvider {\n'),
        ('func (v *Vault) Revoke(ref string) error {\n',
         'func (v *Vault) Revoke(ref string) error {\n\tif v.readOnly { return ErrCredentialProtected }\n'),
    ],
    "internal/host/host.go": [
        ('\tDB            *sql.DB\n\tDir           string\n',
         '\tDB            *sql.DB\n\tDir           string\n\t// Trial-only read access to one existing DPAPI record; the new DB stays isolated.\n\tReadOnlyModelVaultDir string\n\tReadOnlyModelCredentialRef string\n\tReadOnlyModelProvider string\n'),
        ('\tif h.vault, err = openVault(cfg.Dir); err != nil {\n\t\treturn nil, err\n\t}\n',
         '''	if cfg.ReadOnlyModelVaultDir != "" {
		if h.vault, err = openVaultReadOnly(cfg.ReadOnlyModelVaultDir,
			cfg.ReadOnlyModelCredentialRef, cfg.ReadOnlyModelProvider); err != nil {
			return nil, err
		}
	} else if h.vault, err = openVault(cfg.Dir); err != nil {
		return nil, err
	}
'''),
    ],
    "apps/control/main.go": [
        ('\tcoordinatorFile := flag.String("runtime-coordinator-config", "", "private host configuration for the single runtime coordinator")\n',
         '''	coordinatorFile := flag.String("runtime-coordinator-config", "", "private host configuration for the single runtime coordinator")
	trialVault := flag.String("trial-readonly-model-vault-dir", "", "trial-only exact existing sealed host vault directory")
	trialCredential := flag.String("trial-readonly-credential-ref", "", "trial-only single protected credential reference")
	trialProvider := flag.String("trial-readonly-provider", "", "trial-only provider identity")
'''),
        ('\tlocalHost, err := hostboundary.New(hostboundary.Config{DB: db, Dir: filepath.Join(dataDir, "host"), ContractsDir: filepath.Join("spec", "v2.0", "contracts"), MigrationFile: filepath.Join("migrations", "sqlite", "0002_domain.sql"), SchemaDir: filepath.Join("internal", "api", "contracts")})\n',
         '''	if *trialVault != "" && (*coordinatorFile == "" || *trialCredential == "" || *trialProvider == "" || filepath.Clean(*trialVault) == filepath.Clean(filepath.Join(dataDir, "host"))) {
		log.Fatal("trial readonly vault requires coordinator, exact credential/provider and separate isolated data root")
	}
	if *trialVault == "" && (*trialCredential != "" || *trialProvider != "") {
		log.Fatal("partial trial readonly vault configuration")
	}
	localHost, err := hostboundary.New(hostboundary.Config{DB: db, Dir: filepath.Join(dataDir, "host"), ContractsDir: filepath.Join("spec", "v2.0", "contracts"), MigrationFile: filepath.Join("migrations", "sqlite", "0002_domain.sql"), SchemaDir: filepath.Join("internal", "api", "contracts"), ReadOnlyModelVaultDir: *trialVault, ReadOnlyModelCredentialRef: *trialCredential, ReadOnlyModelProvider: *trialProvider})
'''),
    ],
}

for relative, edits in changes.items():
    source = repo / relative
    original = source.read_text(encoding="utf-8")
    changed = original
    counts = []
    for old, new in edits:
        count = changed.count(old)
        counts.append(count)
        if count == 1:
            changed = changed.replace(old, new, 1)
    if any(count != 1 for count in counts):
        print(f"SOURCE_DRIFT {relative} counts={counts}")
        continue
    short = relative.replace("/", "_")
    with (out / (short + ".proposed.go")).open("xb") as f:
        f.write(changed.encode("utf-8"))
    diff = "".join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True),
                                        fromfile="a/" + relative, tofile="b/" + relative))
    with (out / (short + ".patch")).open("xb") as f:
        f.write(diff.encode("utf-8"))
    print(f"SOURCE_DERIVED {relative} counts={counts} bytes={len(changed.encode('utf-8'))}")
