package domain

import (
    "bufio"
    "context"
    "encoding/json"
    "fmt"
    "io"
    "os"
    "os/exec"
    "path/filepath"
    "strings"
    "testing"
    "time"

    "researchos.local/research-os/internal/store"
)

const historical22BridgeProfile = "schema22-public-fixture-v1"
const historical22BridgePrefix = "SCHEMA22_FIXTURE_RESULT "
const historical22BridgeInputSHA = "sha256:dac30037bdc1b6ebae7b9effd74fe84511f710560be259d1035ddf2887918981"

type historical22BridgeRequest struct {
    Profile string `json:"profile"`
    Nonce string `json:"nonce"`
    FixtureRoot string `json:"fixture_root"`
    ReleaseRoot string `json:"release_root"`
    Owner string `json:"owner"`
}
type historical22BridgeRelease struct {
    Profile string `json:"profile"`
    Nonce string `json:"nonce"`
    Release bool `json:"release"`
}
type historical22BridgeCommand struct {
    Envelope *Envelope `json:"envelope"`
    Response *Response `json:"response"`
}
type historical22BridgeResult struct {
    Profile string `json:"profile"`
    Nonce string `json:"nonce"`
    Source string `json:"source"`
    Snapshot string `json:"snapshot"`
    Destination string `json:"destination"`
    KeyFile string `json:"key_file"`
    SourceRoot string `json:"source_root"`
    SourceProgram string `json:"source_program"`
    SourceProgramSHA string `json:"source_program_sha256"`
    SourceDatabaseSHA string `json:"source_database_sha256"`
    SourceSchemaSHA string `json:"source_schema_sha256"`
    SourceRowsSHA string `json:"source_rows_sha256"`
    InputManifestSHA string `json:"input_manifest_sha256"`
    Versions []int `json:"versions"`
    Project string `json:"project"`
    Session string `json:"session"`
    RunID string `json:"run_id"`
    RunEpoch int64 `json:"run_epoch"`
    Commands []historical22BridgeCommand `json:"commands"`
    FixturePhaseReceiptCount int `json:"fixture_phase_receipt_count"`
    ExternalDispatchCount int `json:"external_dispatch_count"`
}

// All data paths must resolve inside a parent-created, fresh fixture directory.
// Nonexistent output leaves are allowed only below an existing contained parent.
func historical22FixturePath(root, path string) error {
    resolvedRoot, err := filepath.EvalSymlinks(root)
    if err != nil { return err }
    if !filepath.IsAbs(path) { return fmt.Errorf("fixture path must be absolute") }
    parent, err := filepath.EvalSymlinks(filepath.Dir(path))
    if err != nil { return err }
    rel, err := filepath.Rel(resolvedRoot, parent)
    if err != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(os.PathSeparator)) || filepath.IsAbs(rel) {
        return fmt.Errorf("fixture path escaped parent temporary root")
    }
    if _, err = os.Lstat(path); err == nil {
        resolved, resolveErr := filepath.EvalSymlinks(path)
        if resolveErr != nil { return resolveErr }
        rel, resolveErr = filepath.Rel(resolvedRoot, resolved)
        if resolveErr != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(os.PathSeparator)) || filepath.IsAbs(rel) {
            return fmt.Errorf("fixture member escaped parent temporary root")
        }
    } else if !os.IsNotExist(err) { return err }
    return nil
}

type historical22BridgeRead struct { result historical22BridgeResult; err error }

// Only this test helper launches the privately piped, exactly selected old test.
// There is no current-service fallback and no production schema compatibility
// switch. The child creates every source fixture path under t.TempDir().
func configurationHistorical22UpgradeFixture(t *testing.T) (LocalUpgradeOptions, *fixture, historical22BridgeResult) {
    t.Helper()
    program := os.Getenv("RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER")
    programSHA := os.Getenv("RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER_SHA256")
    sourceRoot := os.Getenv("RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER_ROOT")
    targetProgram := os.Getenv("RESEARCHOS_CONFIGURATION_TARGET_PROGRAM")
    if program == "" || sourceRoot == "" || len(programSHA) != 71 || !strings.HasPrefix(programSHA, "sha256:") || targetProgram == "" {
        t.Fatal("explicit pinned schema22 fixture helper, source root, and target23 program required")
    }
    raw, err := os.ReadFile(program)
    if err != nil || Digest(raw) != programSHA { t.Fatal("schema22 fixture helper binary mismatch") }
    sourceRoot, err = filepath.Abs(sourceRoot)
    if err != nil { t.Fatal(err) }
    program, err = filepath.Abs(program)
    if err != nil { t.Fatal(err) }
    // The ordinary release inventory is still checked by the existing matcher.
    if _, _, err = upgradeConfigurationRelease(sourceRoot, 22); err != nil { t.Fatal(err) }

    fixtureRoot := t.TempDir()
    nonce := ID()
    marker, err := os.OpenFile(filepath.Join(fixtureRoot, ".schema22-fixture-nonce"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
    if err != nil { t.Fatal(err) }
    if _, err = marker.WriteString(nonce); err != nil { marker.Close(); t.Fatal(err) }
    if err = marker.Close(); err != nil { t.Fatal(err) }
    request := historical22BridgeRequest{Profile: historical22BridgeProfile, Nonce: nonce, FixtureRoot: fixtureRoot, ReleaseRoot: sourceRoot, Owner: "queue-upgrade-owner"}

    // The child has no descendants. It inherits Root's owned Windows job and
    // receives neither a product DataRoot nor any RESEARCHOS service setting.
    ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
    cmd := exec.CommandContext(ctx, program, "-test.run=^TestConfigurationHistorical22FixtureBridge$", "-test.count=1", "-test.timeout=150s")
    cmd.Dir = filepath.Join(sourceRoot, "internal/domain")
    cmd.WaitDelay = 3*time.Second
    for _, entry := range os.Environ() {
        key, _, _ := strings.Cut(entry, "=")
        upper := strings.ToUpper(key)
        if strings.HasPrefix(upper, "RESEARCHOS_") || upper == "TMP" || upper == "TEMP" || upper == "TMPDIR" { continue }
        cmd.Env = append(cmd.Env, entry)
    }
    cmd.Env = append(cmd.Env, "RESEARCHOS_CONFIGURATION_SCHEMA22_BRIDGE=1", "TMP="+fixtureRoot, "TEMP="+fixtureRoot, "TMPDIR="+fixtureRoot)
    input, err := cmd.StdinPipe()
    if err != nil { cancel(); t.Fatal(err) }
    output, err := cmd.StdoutPipe()
    if err != nil { input.Close(); cancel(); t.Fatal(err) }
    // Arbitrary test diagnostics are not credential-safe public results.
    // In particular an old assertion could include a claim response.
    cmd.Stderr = io.Discard
    if err = cmd.Start(); err != nil { input.Close(); output.Close(); cancel(); t.Fatal(err) }

    read := make(chan historical22BridgeRead, 1)
    scanned := make(chan struct{})
    go func() {
        defer close(scanned)
        scanner := bufio.NewScanner(output)
        scanner.Buffer(make([]byte, 4096), 4*1024*1024)
        sent := false
        for scanner.Scan() {
            line := scanner.Text()
            if !strings.HasPrefix(line, historical22BridgePrefix) { continue }
            if sent { continue } // Only the pinned child's single result is consumed.
            var result historical22BridgeResult
            decoder := json.NewDecoder(strings.NewReader(strings.TrimPrefix(line, historical22BridgePrefix)))
            decoder.DisallowUnknownFields()
            decodeErr := decoder.Decode(&result)
            if decodeErr == nil {
                var extra any
                if endErr := decoder.Decode(&extra); endErr != io.EOF { decodeErr = fmt.Errorf("trailing public bridge data") }
            }
            read <- historical22BridgeRead{result: result, err: decodeErr}
            sent = true
        }
        if !sent {
            // Do not expose arbitrary child stdout or its credential-bearing
            // request, even on a failing old fixture assertion.
            read <- historical22BridgeRead{err: fmt.Errorf("historical22 child closed without a public fixture result")}
        }
    }()
    waited := make(chan struct{})
    var waitErr error
    go func() { <-scanned; waitErr = cmd.Wait(); close(waited) }()

    // Register immediately after Start, before every decode/check/t.Fatal path.
    // Release and Close are bounded; Kill is a fallback, and Wait is observed.
    t.Cleanup(func() {
        releaseDone := make(chan struct{})
        go func() {
            _ = json.NewEncoder(input).Encode(historical22BridgeRelease{Profile: historical22BridgeProfile, Nonce: nonce, Release: true})
            close(releaseDone)
        }()
        select {
        case <-releaseDone:
        case <-time.After(2*time.Second):
        }
        _ = input.Close()
        select {
        case <-waited:
        case <-time.After(5*time.Second):
            cancel()
            _ = cmd.Process.Kill()
            select {
            case <-waited:
            case <-time.After(5*time.Second):
                _ = output.Close()
                t.Errorf("historical22 helper Wait did not complete after bounded Kill")
            }
        }
        cancel()
        select {
        case <-waited:
            if waitErr != nil { t.Errorf("historical22 helper exit: %v", waitErr) }
        default:
        }
    })

    sent := make(chan error, 1)
    go func() { sent <- json.NewEncoder(input).Encode(request) }()
    select {
    case err = <-sent:
        if err != nil { t.Fatal("private fixture request pipe failed") }
    case <-time.After(5*time.Second):
        t.Fatal("private fixture request pipe timed out")
    }
    var result historical22BridgeResult
    select {
    case response := <-read:
        if response.err != nil { t.Fatal(response.err) }
        result = response.result
    case <-time.After(90*time.Second):
        t.Fatal("historical22 fixture setup timed out")
    }
    if result.Profile != historical22BridgeProfile || result.Nonce != nonce || result.InputManifestSHA != historical22BridgeInputSHA ||
        result.SourceProgramSHA != programSHA || result.ExternalDispatchCount != 0 || result.FixturePhaseReceiptCount != 6 ||
        result.Project == "" || result.Session == "" || result.RunID == "" || result.RunEpoch <= 0 ||
        Hash(result.Versions) != Hash(upgradeVersions(22)) {
        t.Fatal("historical22 public fixture result scope mismatch")
    }
    for _, pair := range [][2]string{{result.SourceRoot, sourceRoot}, {result.SourceProgram, program}} {
        actual, actualErr := filepath.EvalSymlinks(pair[0])
        expected, expectedErr := filepath.EvalSymlinks(pair[1])
        if actualErr != nil || expectedErr != nil || !strings.EqualFold(actual, expected) { t.Fatal("historical22 code identity mismatch") }
    }
    for _, path := range []string{result.Source, result.Snapshot, result.Destination, result.KeyFile} {
        if err = historical22FixturePath(fixtureRoot, path); err != nil { t.Fatal(err) }
    }
    dbBytes, err := os.ReadFile(result.Source)
    if err != nil || Digest(dbBytes) != result.SourceDatabaseSHA { t.Fatal("historical22 closed source digest mismatch") }
    if len(result.Commands) != 9 { t.Fatal("historical22 public command coverage mismatch") }
    doc := configurationSchema(t)
    for i, command := range result.Commands {
        method := "session.send"
        if i == 0 { method = "goal.start" }
        if i == 8 { method = "session.control" }
        if command.Envelope == nil || command.Response == nil || deref(command.Envelope.Method) != method || deref(command.Response.Method) != method {
            t.Fatal("historical22 public command method mismatch")
        }
        decoded, decodeErr := DecodeEnvelope(Bytes(command.Envelope))
        if decodeErr != nil || deref(decoded.ProjectID) != result.Project { t.Fatal("historical22 public request binding mismatch") }
        if i > 0 && deref(decoded.SessionID) != result.Session { t.Fatal("historical22 public session binding mismatch") }
        if deref(command.Response.CommandID) != deref(decoded.CommandID) { t.Fatal("historical22 public response command mismatch") }
        var generic any
        if err = json.Unmarshal(Bytes(command.Response), &generic); err != nil { t.Fatal(err) }
        if err = doc.ValidateDef("CommandResponse", generic); err != nil { t.Fatal(err) }
        if err = ValidateResultAgainstMethod(method, command.Response, doc); err != nil { t.Fatal(err) }
    }
    snapshot, ok := result.Commands[0].Response.Result["snapshot"].(map[string]any)
    if !ok || Str(snapshot, "session_id") != result.Session { t.Fatal("historical22 goal session mismatch") }

    db, err := store.Open(result.Source)
    if err != nil { t.Fatal(err) }
    t.Cleanup(func() { db.Close() }) // Runs before releasing the child fixture.
    schema, err := backupSchema(db)
    if err != nil || schema != result.SourceSchemaSHA { t.Fatal("historical22 reopened schema mismatch") }
    rows, err := upgradeRows(db)
    if err != nil || Hash(rows) != result.SourceRowsSHA { t.Fatal("historical22 reopened rows mismatch") }
    versions, err := backupMigrations(db)
    if err != nil || Hash(versions) != Hash(upgradeVersions(22)) { t.Fatal("historical22 reopened version mismatch") }
    for _, command := range result.Commands {
        decoded, decodeErr := DecodeEnvelope(Bytes(command.Envelope))
        if decodeErr != nil { t.Fatal(decodeErr) }
        wantHash, hashErr := decoded.ContentHash()
        if hashErr != nil { t.Fatal(hashErr) }
        var storedHash string
        var storedBody []byte
        if err = db.QueryRow(`SELECT request_hash,body FROM idempotency WHERE principal=? AND project=? AND operation=? AND key=?`, request.Owner, result.Project, "v2:"+deref(decoded.Method), deref(decoded.CommandID)).Scan(&storedHash, &storedBody); err != nil {
            t.Fatal("historical22 public response has no original idempotency row")
        }
        var storedResponse Response
        if err = json.Unmarshal(storedBody, &storedResponse); err != nil || storedHash != wantHash || Hash(storedResponse) != Hash(command.Response) {
            t.Fatal("historical22 public response differs from original idempotency row")
        }
    }

    opt := LocalUpgradeOptions{
        Source: result.Source, Snapshot: result.Snapshot, Destination: result.Destination, KeyFile: result.KeyFile,
        SourceRoot: sourceRoot, TargetRoot: configurationUpgradeReleaseFixture(t, 23),
        SourceProgram: program, TargetProgram: targetProgram, Plan: ConfigurationSchemaUpgradePlan,
    }
    // The returned parent fixture is read-only scaffolding for existing snapshot
    // and invariant assertions. It contains no Service or authentication token.
    f := &fixture{db: db, project: result.Project, t: t}
    return opt, f, result
}

