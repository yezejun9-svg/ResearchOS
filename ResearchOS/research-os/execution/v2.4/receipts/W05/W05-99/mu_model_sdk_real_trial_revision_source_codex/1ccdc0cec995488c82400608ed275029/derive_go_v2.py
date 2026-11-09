"""Derive Go source candidates from the sealed v1 proposals; pure IO only."""
import ast
import difflib
import hashlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
OLD = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_executable_source_codex/1b8bc13521764e508f540dc2399ac33d")
MAIN = Path("D:/作品集/ResearchOS/research-os")


def replace_once(text, before, after, name):
    assert text.count(before) == 1, name
    return text.replace(before, after)


vault = (OLD / "internal_host_vault.go.proposed.go").read_text(encoding="utf-8")
anchor = "func openVault(dir string) (*Vault, error) {"
helper = '''// ValidateTrialVaultIsolation runs before any trial data-root lease, database open,
// migration or host mkdir. Both roots must exist as ordinary directories. EvalSymlinks
// rejects path aliases/reparse ancestors; SameFile catches Windows spelling aliases.
// The new data root must be disjoint from the entire old protected resource root,
// not merely from its host/credentials child.
func ValidateTrialVaultIsolation(dataRoot, oldHostDir string) error {
    if !filepath.IsAbs(dataRoot) || !filepath.IsAbs(oldHostDir) {
        return ErrUnknownCredential
    }
    clean := func(path string) (string, error) {
        path = filepath.Clean(path)
        for current := path; ; current = filepath.Dir(current) {
            info, err := os.Lstat(current)
            if err != nil || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
                return "", ErrUnknownCredential
            }
            resolved, err := filepath.EvalSymlinks(current)
            if err != nil || !strings.EqualFold(resolved, current) {
                return "", ErrUnknownCredential
            }
            if filepath.Dir(current) == current { break }
        }
        return path, nil
    }
    data, err := clean(dataRoot)
    if err != nil { return err }
    hostDir, err := clean(oldHostDir)
    if err != nil { return err }
    protected, err := clean(filepath.Dir(hostDir))
    if err != nil { return err }
    sameAncestor := func(target, descendant string) bool {
        wanted, err := os.Stat(target)
        if err != nil { return true }
        for current := descendant; ; current = filepath.Dir(current) {
            actual, err := os.Stat(current)
            if err != nil || os.SameFile(wanted, actual) { return true }
            if filepath.Dir(current) == current { break }
        }
        return false
    }
    if sameAncestor(data, protected) || sameAncestor(protected, data) {
        return ErrUnknownCredential
    }
    return nil
}

'''
vault = replace_once(vault, anchor, helper + anchor, "vault-isolation-helper")

host = (OLD / "internal_host_host.go.proposed.go").read_text(encoding="utf-8")
old = '''\tif cfg.DB == nil || cfg.Dir == "" || cfg.ContractsDir == "" || cfg.MigrationFile == "" || cfg.SchemaDir == "" {
\t\treturn nil, fmt.Errorf("%w: db, dir, contracts, migration and schema are required", ErrBadState)
\t}
\tttl := cfg.SessionTTL'''
new = '''\tif cfg.DB == nil || cfg.Dir == "" || cfg.ContractsDir == "" || cfg.MigrationFile == "" || cfg.SchemaDir == "" {
\t\treturn nil, fmt.Errorf("%w: db, dir, contracts, migration and schema are required", ErrBadState)
\t}
\tif cfg.ReadOnlyModelVaultDir != "" {
\t\tif cfg.ReadOnlyModelCredentialRef == "" || cfg.ReadOnlyModelProvider == "" ||
\t\t\tfilepath.Base(cfg.Dir) != "host" ||
\t\t\tValidateTrialVaultIsolation(filepath.Dir(cfg.Dir), cfg.ReadOnlyModelVaultDir) != nil {
\t\t\treturn nil, ErrUnknownCredential
\t\t}
\t} else if cfg.ReadOnlyModelCredentialRef != "" || cfg.ReadOnlyModelProvider != "" {
\t\treturn nil, ErrUnknownCredential
\t}
\tttl := cfg.SessionTTL'''
host = replace_once(host, old, new, "host-before-mkdir")

control = (OLD / "apps_control_main.go.proposed.go").read_text(encoding="utf-8")
old = '''\tdataDir := setting("RESEARCHOS_DATA_DIR", filepath.Join(".local", "data"))
\twebDir := setting("RESEARCHOS_WEB_DIR", filepath.Join("apps", "web", "dist"))'''
new = '''\tdataDir := setting("RESEARCHOS_DATA_DIR", filepath.Join(".local", "data"))
\tif *trialVault != "" {
\t\tif adminActions != 0 || *coordinatorFile == "" || *trialCredential == "" || *trialProvider == "" ||
\t\t\thostboundary.ValidateTrialVaultIsolation(dataDir, *trialVault) != nil {
\t\t\tlog.Fatal("trial readonly vault requires an isolated existing data root and exact coordinator/ref/provider")
\t\t}
\t} else if *trialCredential != "" || *trialProvider != "" {
\t\tlog.Fatal("partial trial readonly vault configuration")
\t}
\twebDir := setting("RESEARCHOS_WEB_DIR", filepath.Join("apps", "web", "dist"))'''
control = replace_once(control, old, new, "control-before-lease")
old = '''\tif *trialVault != "" && (*coordinatorFile == "" || *trialCredential == "" || *trialProvider == "" || filepath.Clean(*trialVault) == filepath.Clean(filepath.Join(dataDir, "host"))) {
\t\tlog.Fatal("trial readonly vault requires coordinator, exact credential/provider and separate isolated data root")
\t}
\tif *trialVault == "" && (*trialCredential != "" || *trialProvider != "") {
\t\tlog.Fatal("partial trial readonly vault configuration")
\t}
'''
control = replace_once(control, old, "", "remove-too-late-control-guard")

qual = (OLD / "runtime_qualification.unlimited.v2.proposed.go").read_text(encoding="utf-8")
selected = (
    ("internal/domain/runtime_qualification.go", "runtime_qualification.unlimited.v3.proposed.go", qual),
    ("internal/host/vault.go", "internal_host_vault.v2.proposed.go", vault),
    ("internal/host/host.go", "internal_host_host.v2.proposed.go", host),
    ("apps/control/main.go", "apps_control_main.v2.proposed.go", control),
)
for target, name, candidate in selected:
    original = (MAIN / target).read_text(encoding="utf-8")
    candidate_path = HERE / name
    with candidate_path.open("xb") as out: out.write(candidate.encode("utf-8"))
    forward = "".join(difflib.unified_diff(original.splitlines(keepends=True), candidate.splitlines(keepends=True), fromfile="a/" + target, tofile="b/" + target))
    inverse = "".join(difflib.unified_diff(candidate.splitlines(keepends=True), original.splitlines(keepends=True), fromfile="a/" + target, tofile="b/" + target))
    with (HERE / (name + ".patch")).open("xb") as out: out.write(forward.encode("utf-8"))
    with (HERE / (name + ".inverse.patch")).open("xb") as out: out.write(inverse.encode("utf-8"))
print("SOURCE_DERIVED_4_GO_CANDIDATES_STATIC_ONLY")
