from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def digest(raw):return hashlib.sha256(raw).hexdigest()
p=ROOT/'internal/domain/backup_upgrade_test.go';raw=p.read_bytes();lines=raw.splitlines(keepends=True)
assert digest(raw)=='9ccce431024be0f84e412ee1e3ce7154bebd6c18317ab41ab2e8333dd57e9275'
prefix=b''.join(lines[:974]);old=b''.join(lines[974:981]);suffix=b''.join(lines[981:])
assert digest(prefix)=='fbbcf34d236471f80387ac272d53f95c546852fc7a92b79ace4f924dc9a2764a'
assert digest(old)=='ca0ebd3dcedb691da8081acd7986da5e416d160a6d36d09557b691abdc05d2a5'
assert digest(suffix)=='4be4995717198092dbee3e94c37fcbadfddd353e699e00d552dd2193dc932e1e'
replacement='''	control := filepath.Join(t.TempDir(), "control.exe")
	if historical := os.Getenv("RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL"); historical != "" {
		const artifactHash = "sha256:aeda2d5eff0028529eaa53e9f5cc91fbcd668842577315eb744bd5f066834032"
		artifact, err := os.ReadFile(historical)
		if err != nil {
			t.Fatalf("historical schema14 artifact read: %v", err)
		}
		if Digest(artifact) != artifactHash {
			t.Fatal("historical schema14 artifact hash mismatch")
		}
		goBytes, err := os.ReadFile(goexe)
		if err != nil || Digest(goBytes) != "sha256:d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490" {
			t.Fatal("historical schema14 requires the actual locked Go executable")
		}
		if err = os.WriteFile(control, artifact, 0700); err != nil {
			t.Fatal(err)
		}
		staged, err := os.ReadFile(control)
		if err != nil || Digest(staged) != artifactHash {
			t.Fatal("historical schema14 staged artifact hash mismatch")
		}
		metadata, err := exec.Command(goexe, "version", "-m", control).CombinedOutput()
		if err != nil {
			t.Fatalf("historical schema14 buildinfo: %v %s", err, metadata)
		}
		metadataLines := strings.Split(string(metadata), "\\n")
		if len(metadataLines) == 0 || strings.TrimSuffix(metadataLines[0], "\\r") != control+": go1.27.1" {
			t.Fatal("historical schema14 Go version mismatch")
		}
		for _, expected := range []string{
			"\\tpath\\tresearchos.local/research-os/apps/control",
			"\\tbuild\\tGOOS=windows",
			"\\tbuild\\tGOARCH=amd64",
			"\\tbuild\\tvcs.revision=09a6a5ecfba40c1596a3ec46be25c34ba1f2fce0",
			"\\tbuild\\tvcs.modified=true",
		} {
			matches := 0
			for _, line := range metadataLines[1:] {
				if strings.TrimSuffix(line, "\\r") == expected {
					matches++
				}
			}
			if matches != 1 {
				t.Fatalf("historical schema14 buildinfo mismatch: %s", expected)
			}
		}
		t.Logf("HISTORICAL_SCHEMA14_PROFILE artifact=%s staged=%s buildinfo=%s", artifactHash, control, metadata)
	} else {
		build := exec.Command(goexe, "build", "-o", control, "./apps/control")
		build.Dir = "../.."
		if output, err := build.CombinedOutput(); err != nil {
			t.Fatalf("build control: %v %s", err, output)
		}
	}
	opt.TargetProgram = control
'''
newline=b'\r\n' if old.count(b'\r\n') else b'\n'
new=replacement.encode().replace(b'\n',newline)
assert not (HERE/'original_backup_upgrade_test.go.txt').exists()
(HERE/'original_backup_upgrade_test.go.txt').write_bytes(raw)
p.write_bytes(prefix+new+suffix)
audit={'path':'internal/domain/backup_upgrade_test.go','before_sha256':digest(raw),'after_sha256':digest(p.read_bytes()),'prefix_sha256':digest(prefix),'suffix_sha256':digest(suffix),'old_span_sha256':digest(old),'new_span_sha256':digest(new),'prefix_bytes':len(prefix),'suffix_bytes':len(suffix),'new_span_bytes':len(new),'all_exterior_bytes_preserved':p.read_bytes().startswith(prefix) and p.read_bytes().endswith(suffix)}
(HERE/'source_span_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audit,indent=2))
