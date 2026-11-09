import sys
sys.dont_write_bytecode=True
import collections,difflib,hashlib,json,re,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def ref(p):
    p=Path(p).resolve(); raw=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def verify(item):
    actual=ref(item["path"])
    assert actual["sha256"]==item["sha256"] and actual["bytes"]==item["bytes"],"pin mismatch"
def masked(s):
    a=list(s); i=0
    while i<len(s):
        start=i
        if s.startswith("//",i):
            end=s.find("\n",i); i=len(s) if end<0 else end
        elif s.startswith("/*",i):
            end=s.find("*/",i+2); i=len(s) if end<0 else end+2
        elif s[i] in (chr(34), chr(39), chr(96)):
            q=s[i]; i+=1
            while i<len(s):
                if s[i]==q: i+=1; break
                if s[i]==chr(92) and q!=chr(96): i+=2
                else: i+=1
        else: i+=1; continue
        for k in range(start,min(i,len(s))):
            if a[k]!="\n": a[k]=" "
    return "".join(a)
def assertions(s):
    m=masked(s); result=[]
    for hit in re.finditer(r"\bt\.(?:Fatalf?|Errorf?|FailNow|Fail)\s*\(",m):
        depth=1; right=hit.end()
        while right<len(m) and depth:
            depth+=(m[right]=="(")-(m[right]==")"); right+=1
        result.append(s[hit.start():right])
    return collections.Counter(result)
def main():
    inspected=json.loads((Q/"inspection.json").read_text(encoding="utf-8"))
    verify(inspected["base_ref"])
    verify(inspected["compile_closed_ref"])
    assert inspected["TTL_candidate_equals_formatted_T7"]
    for b in inspected["compile_bindings"].values():
        verify(b["actual_ref"]); assert b["closed_matching_refs"]
    assert inspected["formatted_source_matches"] and inspected["compiler_inventory_source_matches"]
    for item in inspected["snapshots"]:
        verify(item["source_ref"]); verify(item["snapshot_ref"])
    source=Path(inspected["base_ref"]["path"])
    original=source.read_bytes(); base=original.decode("utf-8")
    addition="\n\n// Root supplies this public proof root only to the fixed harness process.\n// It is never forwarded to the broker or any native child.\nfunc nativeHarnessBrokerPublicEnvironment(proofRoot string, environment map[string]string) (map[string]string, error) {\n\tif len(environment) != 4 {\n\t\treturn nil, fmt.Errorf(\"synthetic native broker public environment must contain exactly four keys\")\n\t}\n\tresolve := func(name, path string) (string, error) {\n\t\tif strings.TrimSpace(path) == \"\" || !filepath.IsAbs(path) {\n\t\t\treturn \"\", fmt.Errorf(\"synthetic native broker %s must be an absolute directory\", name)\n\t\t}\n\t\tinfo, err := os.Stat(path)\n\t\tif err != nil || !info.IsDir() {\n\t\t\treturn \"\", fmt.Errorf(\"synthetic native broker %s directory unavailable\", name)\n\t\t}\n\t\tresolved, err := filepath.EvalSymlinks(path)\n\t\tif err != nil || !filepath.IsAbs(resolved) {\n\t\t\treturn \"\", fmt.Errorf(\"synthetic native broker %s physical directory unavailable\", name)\n\t\t}\n\t\treturn filepath.Clean(resolved), nil\n\t}\n\troot, err := resolve(\"proof root\", proofRoot)\n\tif err != nil {\n\t\treturn nil, err\n\t}\n\tphysical := make(map[string]string, 4)\n\tfor _, name := range []string{\"SystemRoot\", \"WINDIR\", \"TEMP\", \"TMP\"} {\n\t\tpath, ok := environment[name]\n\t\tif !ok {\n\t\t\treturn nil, fmt.Errorf(\"synthetic native broker public environment key unavailable\")\n\t\t}\n\t\tphysical[name], err = resolve(name, path)\n\t\tif err != nil {\n\t\t\treturn nil, err\n\t\t}\n\t}\n\tfor _, name := range []string{\"SystemRoot\", \"WINDIR\"} {\n\t\tif nativeHarnessTempWithin(root, physical[name]) || nativeHarnessTempWithin(physical[name], root) {\n\t\t\treturn nil, fmt.Errorf(\"synthetic native broker proof root overlaps a system directory\")\n\t\t}\n\t}\n\tfor _, name := range []string{\"TEMP\", \"TMP\"} {\n\t\tif !nativeHarnessTempWithin(proofRoot, environment[name]) || !nativeHarnessTempWithin(root, physical[name]) {\n\t\t\treturn nil, fmt.Errorf(\"synthetic native broker %s escapes the isolated proof root\", name)\n\t\t}\n\t}\n\treturn map[string]string{\n\t\t\"SystemRoot\": environment[\"SystemRoot\"], \"WINDIR\": environment[\"WINDIR\"],\n\t\t\"TEMP\": environment[\"TEMP\"], \"TMP\": environment[\"TMP\"],\n\t}, nil\n}\n\n// Windows comparisons apply to the original and EvalSymlinks-resolved paths.\nfunc nativeHarnessTempWithin(root, path string) bool {\n\trelative, err := filepath.Rel(strings.ToLower(filepath.Clean(root)), strings.ToLower(filepath.Clean(path)))\n\treturn err == nil && relative != \"..\" && !strings.HasPrefix(relative, \"..\"+string(filepath.Separator)) && !filepath.IsAbs(relative)\n}\n\n// Synthetic local filesystem/env fixtures only; no native migration authority.\nfunc TestNativeHarnessBrokerIsolatedTempEnvironment(t *testing.T) {\n\tproof, outside, system := t.TempDir(), t.TempDir(), t.TempDir()\n\ttemp, tmp := filepath.Join(proof, \"temp\"), filepath.Join(proof, \"tmp\")\n\tfor _, path := range []string{temp, tmp} {\n\t\tif err := os.Mkdir(path, 0700); err != nil {\n\t\t\tt.Fatal(err)\n\t\t}\n\t}\n\tfile := filepath.Join(proof, \"not-directory\")\n\tif err := os.WriteFile(file, []byte(\"synthetic fixture\"), 0600); err != nil {\n\t\tt.Fatal(err)\n\t}\n\tbase := map[string]string{\"SystemRoot\": system, \"WINDIR\": system, \"TEMP\": temp, \"TMP\": tmp}\n\tcases := []struct {\n\t\tname, proof, key, value string\n\t\tvalid                  bool\n\t}{\n\t\t{\"local-temp-allowed\", proof, \"\", \"\", true},\n\t\t{\"case-normalized-root\", strings.ToUpper(proof), \"\", \"\", true},\n\t\t{\"empty-proof\", \"\", \"\", \"\", false},\n\t\t{\"relative-proof\", \".\", \"\", \"\", false},\n\t\t{\"missing-proof\", filepath.Join(proof, \"missing\"), \"\", \"\", false},\n\t\t{\"empty-temp\", proof, \"TEMP\", \"\", false},\n\t\t{\"empty-tmp\", proof, \"TMP\", \"\", false},\n\t\t{\"relative-temp\", proof, \"TEMP\", \"temp\", false},\n\t\t{\"relative-tmp\", proof, \"TMP\", \"tmp\", false},\n\t\t{\"missing-temp\", proof, \"TEMP\", filepath.Join(proof, \"missing\"), false},\n\t\t{\"file-as-temp\", proof, \"TEMP\", file, false},\n\t\t{\"temp-outside-proof\", proof, \"TEMP\", outside, false},\n\t\t{\"tmp-different-root\", proof, \"TMP\", outside, false},\n\t\t{\"proof-is-system-directory\", system, \"\", \"\", false},\n\t\t{\"proof-contains-system-directory\", filepath.Dir(system), \"\", \"\", false},\n\t\t{\"empty-system-root\", proof, \"SystemRoot\", \"\", false},\n\t\t{\"empty-windir\", proof, \"WINDIR\", \"\", false},\n\t\t{\"unexpected-environment-key\", proof, \"RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT\", proof, false},\n\t}\n\tfor _, tc := range cases {\n\t\tt.Run(tc.name, func(t *testing.T) {\n\t\t\tenv := map[string]string{\"SystemRoot\": base[\"SystemRoot\"], \"WINDIR\": base[\"WINDIR\"], \"TEMP\": base[\"TEMP\"], \"TMP\": base[\"TMP\"]}\n\t\t\tif tc.key != \"\" {\n\t\t\t\tenv[tc.key] = tc.value\n\t\t\t}\n\t\t\tactual, err := nativeHarnessBrokerPublicEnvironment(tc.proof, env)\n\t\t\tif !tc.valid {\n\t\t\t\tif err == nil || actual != nil {\n\t\t\t\t\tt.Fatal(\"invalid isolated public environment was accepted\")\n\t\t\t\t}\n\t\t\t\treturn\n\t\t\t}\n\t\t\tif err != nil || !reflect.DeepEqual(actual, base) {\n\t\t\t\tt.Fatal(\"valid isolated public environment changed or was rejected\", err)\n\t\t\t}\n\t\t})\n\t}\n}\n\n// Pure path-boundary comparisons are synthetic; these do not create a junction\n// or claim actual reparse-point execution. The env helper always EvalSymlinks.\nfunc TestNativeHarnessBrokerTempBoundaryComparison(t *testing.T) {\n\tcases := []struct {\n\t\tname, root, path string\n\t\tinside           bool\n\t}{\n\t\t{\"same-directory\", \"D:/isolated\", \"D:/isolated\", true},\n\t\t{\"child-directory\", \"D:/isolated\", \"D:/isolated/temp\", true},\n\t\t{\"windows-case\", \"D:/Isolated\", \"d:/isolated/TEMP\", true},\n\t\t{\"prefix-sibling\", \"D:/isolated\", \"D:/isolated-escape/temp\", false},\n\t\t{\"parent-escape\", \"D:/isolated\", \"D:/isolated/../outside\", false},\n\t\t{\"resolved-alias-escape\", \"D:/isolated\", \"D:/outside\", false},\n\t\t{\"different-volume\", \"D:/isolated\", \"C:/temp\", false},\n\t\t{\"system-outside-proof\", \"D:/isolated\", \"C:/Windows\", false},\n\t\t{\"system-contains-root\", \"C:/Windows\", \"C:/Windows/temp\", true},\n\t\t{\"root-contains-system\", \"C:/\", \"C:/Windows\", true},\n\t}\n\tfor _, tc := range cases {\n\t\tt.Run(tc.name, func(t *testing.T) {\n\t\t\tif actual := nativeHarnessTempWithin(tc.root, tc.path); actual != tc.inside {\n\t\t\t\tt.Fatal(\"Windows physical path boundary comparison differs\", tc.name)\n\t\t\t}\n\t\t})\n\t}\n}\n"
    replacements=[
        ("\tt.Helper()\n\tfor _, pin := range []recoveryauthority.RawPin{cfg.PythonProgram, cfg.BrokerSource, cfg.PrivateStdinHelper, program} {","\tt.Helper()\n\tpublicEnvironment, err := nativeHarnessBrokerPublicEnvironment(\n\t\tos.Getenv(\"RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT\"),\n\t\tmap[string]string{\"SystemRoot\": os.Getenv(\"SystemRoot\"), \"WINDIR\": os.Getenv(\"WINDIR\"), \"TEMP\": os.Getenv(\"TEMP\"), \"TMP\": os.Getenv(\"TMP\")})\n\tif err != nil {\n\t\tt.Fatal(err)\n\t}\n\tfor _, pin := range []recoveryauthority.RawPin{cfg.PythonProgram, cfg.BrokerSource, cfg.PrivateStdinHelper, program} {"),
        ("\t\tEnvironment:     map[string]string{\"SystemRoot\": os.Getenv(\"SystemRoot\"), \"WINDIR\": os.Getenv(\"WINDIR\")},","\t\tEnvironment:     publicEnvironment,"),
        ("\tcommand.Env = []string{\"SystemRoot=\" + os.Getenv(\"SystemRoot\"), \"WINDIR=\" + os.Getenv(\"WINDIR\")}","\tcommand.Env = []string{\"SystemRoot=\" + publicEnvironment[\"SystemRoot\"], \"WINDIR=\" + publicEnvironment[\"WINDIR\"], \"TEMP=\" + publicEnvironment[\"TEMP\"], \"TMP=\" + publicEnvironment[\"TMP\"]}"),
    ]
    candidate=base
    for old,new in replacements:
        assert candidate.count(old)==1, "replacement scope differs"
        candidate=candidate.replace(old,new,1)
    candidate+=addition
    inverse=candidate[:-len(addition)]
    for old,new in reversed(replacements):
        assert inverse.count(new)==1
        inverse=inverse.replace(new,old,1)
    assert inverse.encode("utf-8")==original
    aa,ba=assertions(base),assertions(candidate)
    assert aa.total()==84 and not (aa-ba)
    stack=[]; pairs={")":"(","]":"[","}":"{"}
    for ch in masked(candidate):
        if ch in "([{": stack.append(ch)
        elif ch in ")]}": assert stack and stack.pop()==pairs[ch]
    assert not stack
    tests=re.findall(r"^func\s+(Test\w+)\s*\(",masked(candidate),re.M)
    oldtests=re.findall(r"^func\s+(Test\w+)\s*\(",masked(base),re.M)
    assert all(name in tests for name in oldtests)
    assert candidate.count("IssueCredential(context.Background(), f.owner, 15*time.Minute)")==base.count("IssueCredential(context.Background(), f.owner, 15*time.Minute)")
    assert candidate.count("15*time.Minute")==base.count("15*time.Minute")==2
    assert "os.Environ" not in addition and "os.Environ" not in candidate
    p=Q/"candidate-root/internal/domain/native_migration_authority_harness_windows_test.go"
    p.parent.mkdir(parents=True,exist_ok=False)
    with p.open("xb") as f: f.write(candidate.encode("utf-8"))
    diff="".join(difflib.unified_diff(base.splitlines(True),candidate.splitlines(True),fromfile="T7/internal/domain/"+source.name,tofile="candidate-root/internal/domain/"+source.name))
    with (Q/"broker-temp.patch").open("x",encoding="utf-8",newline="\n") as f: f.write(diff)
    result={"authority":"NONE","formal_acceptance":False,"base_ref":ref(source),"candidate_ref":ref(p),
         "minimal_diff_ref":ref(Q/"broker-temp.patch"),"exact_inverse_recovers_entire_T7_bytes":True,
         "original_assertion_calls":aa.total(),"candidate_assertion_calls":ba.total(),"missing_original_assertions":list((aa-ba).elements()),
         "original_Test_names":oldtests,"candidate_Test_names":tests,"original_9cases_and_TTL_grant_all_other_bytes_preserved":True,
         "added_env_leaf_names":re.findall(r'(?m)^\t\t\{"([^"]+)"',addition),
         "physical_checks":["absolute/nonempty","Stat directory exists","EvalSymlinks physical path","Windows case normalized Rel","lexical and physical within proof root","proof root no system-directory overlap","only four public keys"],
         "proof_environment_key":"RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT",
         "proof_key_not_forwarded_to_broker_or_native_child":True,
         "CWD_Schema_180timeout_Sourcepins_privatepipe_unchanged":True,
         "actual_Go_SQL_native_model_execution":None,"new_mechanical_errors":1,
         "prior835_and_all_history_not_reset":True}
    (Q/"static-evidence.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
code=0
try: main()
except Exception: traceback.print_exc(); code=1
finally: print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)

