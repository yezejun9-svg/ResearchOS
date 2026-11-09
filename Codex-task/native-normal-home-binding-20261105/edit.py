from pathlib import Path

root = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-normal-home-binding-20261105\adapters\runtime")

def edit(name: str, old: str, new: str) -> None:
    path = root / name
    raw = path.read_bytes()
    old_bytes = old.encode("utf-8")
    if raw.count(old_bytes) != 1:
        raise RuntimeError(f"expected exactly one match in {name}: {old[:60]!r}")
    path.write_bytes(raw.replace(old_bytes, new.encode("utf-8"), 1))

edit("codex_qualification_windows.go", "func qualificationSHA(s string) bool {", '''// The Host-supplied OS-account NormalHome is the only trusted side of this
// comparison. Accept ordinary Windows separator and case spelling only;
// never resolve a different path or take authority from USERPROFILE.
func sameQualificationNormalHome(normalHome, userProfile string) bool {
    for _, path := range []string{normalHome, userProfile} {
        if path == "" {
            return false
        }
        normalized := filepath.FromSlash(path)
        if !filepath.IsAbs(normalized) || filepath.Clean(normalized) != normalized ||
            strings.ContainsAny(normalized, `<>"|?*;`) {
            return false
        }
        for _, r := range normalized {
            if r < ' ' {
                return false
            }
        }
        if colon := strings.IndexByte(normalized, ':'); colon >= 0 {
            if colon != 1 || !((normalized[0] >= 'A' && normalized[0] <= 'Z') ||
                (normalized[0] >= 'a' && normalized[0] <= 'z')) ||
                strings.Contains(normalized[colon+1:], ":") {
                return false
            }
        }
    }
    return strings.EqualFold(filepath.FromSlash(normalHome), filepath.FromSlash(userProfile))
}

func qualificationSHA(s string) bool {''')
edit("codex_qualification_windows.go", '!strings.EqualFold(q.rpc.options.NormalHome, os.Getenv("USERPROFILE"))', '!sameQualificationNormalHome(q.rpc.options.NormalHome, os.Getenv("USERPROFILE"))')
edit("codex_qualification_capture_windows.go", '!strings.EqualFold(context.NormalHome, os.Getenv("USERPROFILE"))', '!sameQualificationNormalHome(context.NormalHome, os.Getenv("USERPROFILE"))')

edit("codex_qualification_windows_test.go", 'func TestCodexNativeQualificationEnsureIsSingleUseAndBound(t *testing.T) {', r'''func TestQualificationNormalHomeSpelling(t *testing.T) {
    trusted := `C:\Users\yqyyds`
    for _, tc := range []struct {
        name, normalHome, userProfile string
        want bool
    }{
        {"same", trusted, trusted, true},
        {"forward slashes", trusted, "C:/Users/yqyyds", true},
        {"mixed case and separators", trusted, "c:/uSeRs/YQYYDS", true},
        {"changed user", trusted, `C:\Users\other`, false},
        {"prefix sibling", trusted, `C:\Users\yqyyds2`, false},
        {"changed drive", trusted, `D:\Users\yqyyds`, false},
        {"changed root", trusted, `C:\Other\yqyyds`, false},
        {"empty profile", trusted, "", false},
        {"empty trusted home", "", trusted, false},
        {"relative", trusted, `Users\yqyyds`, false},
        {"drive relative", trusted, `C:Users\yqyyds`, false},
        {"dot segment", trusted, `C:\Users\.\yqyyds`, false},
        {"parent segment", trusted, `C:\Users\other\..\yqyyds`, false},
        {"NUL", trusted, trusted + "\x00", false},
        {"CRLF", trusted, trusted + "\r\n", false},
        {"semicolon", trusted, trusted + ";", false},
        {"invalid character", trusted, trusted + "?", false},
    } {
        t.Run(tc.name, func(t *testing.T) {
            if got := sameQualificationNormalHome(tc.normalHome, tc.userProfile); got != tc.want {
                t.Fatalf("sameQualificationNormalHome(%q, %q) = %t, want %t", tc.normalHome, tc.userProfile, got, tc.want)
            }
        })
    }
}

func TestQualificationNormalHomeEarlyGateRejectsChangedOrEmptyProfile(t *testing.T) {
    for _, tc := range []struct{ name, profile string }{
        {"changed", `C:\Users\a-different-user`},
        {"empty", ""},
    } {
        t.Run(tc.name, func(t *testing.T) {
            q, _ := qualifiedFixture(t)
            t.Setenv("USERPROFILE", tc.profile)
            in := CodexLaunch{TaskID: "task", RunID: "run", Epoch: "1", Workspace: q.options.SyntheticSource, Directory: filepath.Join(q.options.ApprovedRoot, "run"), SourceBindingHash: "sha256:source"}
            obs, err := q.ensureLaunch(context.Background(), in)
            if err == nil || err.Error() != "QUALIFICATION_SCOPE_MISMATCH" || obs.ReceiptPath != "" || q.state != "FAILED" {
                t.Fatal("changed or empty profile passed the prelaunch gate", obs.ReceiptPath, q.state, err)
            }
            if _, err := os.Stat(filepath.Join(q.options.ApprovedRoot, "receipts")); !errors.Is(err, os.ErrNotExist) {
                t.Fatal("prelaunch gate created qualification artifacts", err)
            }
        })
    }
}

func TestCodexNativeQualificationEnsureIsSingleUseAndBound(t *testing.T) {''')

edit("codex_qualification_capture_windows_test.go", 'func TestQualificationPrelaunchIntentProvenanceAndMutation(t *testing.T) {', '''func TestQualificationNormalHomeIntentSpelling(t *testing.T) {
    exe, args, env, cwd, jobName, base, receipt := qualificationFakeCollectorInputs(t, "home-spelling")
    flags := uint32(windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | windows.JOB_OBJECT_LIMIT_JOB_MEMORY)
    limits := qualificationJobLimits{Flags: flags, Processes: qualificationProcessLimit, Memory: uint64(qualificationJobMemory)}
    receipt.NormalHome = filepath.Clean(receipt.NormalHome)
    t.Setenv("USERPROFILE", filepath.ToSlash(receipt.NormalHome))
    if _, err := qualificationIntentRecord(exe, args, env, cwd, jobName, base, receipt, limits); err != nil {
        t.Fatal("separator-equivalent OS-account home rejected by intent validator", err)
    }
    for _, tc := range []struct{ name, profile string }{
        {"changed", filepath.Join(filepath.Dir(receipt.NormalHome), "different-user")},
        {"empty", ""},
    } {
        t.Run(tc.name, func(t *testing.T) {
            t.Setenv("USERPROFILE", tc.profile)
            if _, err := qualificationIntentRecord(exe, args, env, cwd, jobName, base, receipt, limits); err == nil {
                t.Fatal("changed or empty home accepted by prelaunch intent validator")
            }
        })
    }
}

func TestQualificationPrelaunchIntentProvenanceAndMutation(t *testing.T) {''')
