"""Pure stdlib source preparation; never imports or executes product code."""
import collections
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[7]
HERE = Path(__file__).resolve().parent
CENSUS_DIR = ROOT / "execution/v2.4/receipts/W05/W05-99/current58_go_source_census_independent_review_codex/92e770e577424482af1ba726ff73091a"
CENSUS_PATH = CENSUS_DIR / "census.json"
REVIEW_PATH = CENSUS_DIR / "review.json"
MATRIX_PATH = CENSUS_DIR / "test-resource-matrix.json"
SKIP_PATH = CENSUS_DIR / "skip-and-environment.json"
EXPECTED = {
    "census.json": "b03356cf5103c45b78d418f3e588ed0e153f6affdfa04987e0f1517482847c26",
    "review.json": "dc1e165596480a69020241c00bd13ea2818c96d8561dc4fc429719a071045036",
    "test-resource-matrix.json": "60a231b784f00b0c3d57894b64722cacebd5fb670d3888b8805da25c25d496c0",
    "skip-and-environment.json": "18082786744d0230faf051668ba725296353a9546a401eb3395d97558a71bf83",
}


def raw(path):
    return path.read_bytes()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    data = raw(path)
    return {"path": path.as_posix(), "sha256": digest(data), "bytes": len(data)}


def write_json(name, obj):
    (HERE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def mask_go(code):
    """Mask Go strings/comments, preserving source offsets and newlines."""
    out = list(code)
    state, i, n = "code", 0, len(code)
    while i < n:
        c = code[i]
        nxt = code[i + 1] if i + 1 < n else ""
        if state == "code":
            if c == "/" and nxt == "/":
                out[i] = out[i + 1] = " "; state = "line"; i += 2; continue
            if c == "/" and nxt == "*":
                out[i] = out[i + 1] = " "; state = "block"; i += 2; continue
            if c in ('"', "'", "`"):
                out[i] = " "; state = c; i += 1; continue
        elif state == "line":
            if c == "\n": state = "code"
            else: out[i] = " "
        elif state == "block":
            if c == "*" and nxt == "/":
                out[i] = out[i + 1] = " "; state = "code"; i += 2; continue
            if c != "\n": out[i] = " "
        elif state == "`":
            if c == "`": state = "code"
            if c != "\n": out[i] = " "
        else:
            if c == "\\" and i + 1 < n:
                out[i] = " "; i += 1
                if code[i] != "\n": out[i] = " "
                i += 1; continue
            if c == state: state = "code"
            if c != "\n": out[i] = " "
        i += 1
    return "".join(out)


DECL = re.compile(r"(?m)^[ \t]*func[ \t]+(?:\([^()\n]*\)[ \t]*)?([A-Za-z_]\w*)[ \t]*\(")
CALL = re.compile(r"(?:(\b[A-Za-z_]\w*)\s*\.\s*)?\b([A-Za-z_]\w*)\s*\(")
KNOWN_IMPORTS = {"os", "exec", "filepath", "http", "httptest", "net", "tls", "context", "store", "strings", "fmt", "json", "testing", "runtime", "sql", "math", "time", "sync", "atomic", "errors", "strconv", "bytes", "io", "url", "syscall", "windows"}
KEYWORDS = {"if", "for", "switch", "select", "func", "return", "go", "defer", "make", "new", "append", "len", "cap", "copy", "delete", "panic", "recover", "close", "print", "println", "complex", "real", "imag"}
SIGNALS = {
    "env": re.compile(r"(?:os\.)?(?:Getenv|LookupEnv|Setenv)\s*\(|\bt\.Setenv\s*\("),
    "skip": re.compile(r"\bt\.Skip(?:f|Now)?\s*\("),
    "http": re.compile(r"httptest\.|http\.(?:NewRequest|ListenAndServe)|\.ServeHTTP\s*\(|net\.Listen\s*\(|\.Do\s*\("),
    "process": re.compile(r"(?:exec|os)\.(?:Command|StartProcess|CreateProcess)\s*\(|syscall\.(?:ForkExec|Exec)\s*\("),
    "filesystem": re.compile(r"os\.(?:ReadFile|WriteFile|OpenFile|Create|Remove|Rename|Mkdir|MkdirAll|Symlink|Lstat|Stat)\s*\(|\.TempDir\s*\(|store\.Open\s*\("),
    "tls": re.compile(r"httptest\.NewTLSServer\s*\(|tls\.Config|\.TLS\b"),
}
ENV_KEYS = re.compile(r"(?:Getenv|LookupEnv|Setenv)\s*\(\s*\"([^\"]+)\"")


def functions_in(path, code, package_key):
    masked = mask_go(code)
    result = []
    for match in DECL.finditer(masked):
        start = masked.find("{", match.end())
        if start < 0 or start - match.end() > 1500: continue
        depth, end = 0, None
        for at in range(start, len(masked)):
            if masked[at] == "{": depth += 1
            elif masked[at] == "}":
                depth -= 1
                if depth == 0: end = at + 1; break
        if end is None: continue
        line = code.count("\n", 0, match.start()) + 1
        name = match.group(1)
        key = f"{package_key}::{path}:{line}:{name}"
        original = code[start:end]
        clean = masked[start:end]
        calls = []
        for call in CALL.finditer(clean):
            qualifier, target = call.groups()
            if target in KEYWORDS: continue
            calls.append({"qualifier": qualifier, "name": target})
        signs = {kind: len(regex.findall(original)) for kind, regex in SIGNALS.items() if regex.search(original)}
        keys = sorted(set(ENV_KEYS.findall(original)))
        if keys: signs["env_keys"] = keys
        result.append({"key": key, "name": name, "package_key": package_key, "path": path,
                       "line": line, "end_line": code.count("\n", 0, end) + 1,
                       "calls": calls, "lexical_signals": signs})
    return result


def main():
    for name, value in EXPECTED.items():
        assert digest(raw(CENSUS_DIR / name)) == value, name
    census = json.loads(raw(CENSUS_PATH))
    review = json.loads(raw(REVIEW_PATH))
    matrix = json.loads(raw(MATRIX_PATH))
    skip = json.loads(raw(SKIP_PATH))
    catalog_path = Path(census["catalog_ref"]["path"])
    catalog_raw = raw(catalog_path)
    assert digest(catalog_raw) == census["catalog_ref"]["sha256"]
    catalog = json.loads(catalog_raw)
    assert census["source_commit"] == review["source_commit"] == catalog["commit"]
    assert len(census["tests"]) == 745 and len(matrix) == 745
    matrix_by_id = {row["id"]: row for row in matrix}
    assert len(matrix_by_id) == 745
    file_package = {}
    for package in census["packages"]:
        for item in package["go_files"]:
            path = item if isinstance(item, str) else item["path"]
            file_package[path] = package["directory"] + ":" + package["package"]
    go_files = [row for row in catalog["files"] if row["path"].endswith(".go")]
    funcs = []
    source_pins = []
    for item in go_files:
        path = ROOT / item["path"]
        data = raw(path)
        assert digest(data) == item["sha256"] and len(data) == item["bytes"], item["path"]
        source_pins.append({"path": item["path"], "sha256": item["sha256"], "bytes": item["bytes"]})
        key = file_package.get(item["path"])
        if key:
            funcs.extend(functions_in(item["path"], data.decode("utf-8"), key))
    by_name = collections.defaultdict(list)
    by_path_name = collections.defaultdict(list)
    for f in funcs:
        by_name[(f["package_key"], f["name"])].append(f)
        by_path_name[(f["path"], f["name"])].append(f)
    by_key = {f["key"]: f for f in funcs}
    init_refs = [{"path": f["path"], "line": f["line"], "package_key": f["package_key"]}
                 for f in funcs if f["name"] == "init"]
    other_go_test_entry_names = [f["key"] for f in funcs
                                 if f["name"].startswith(("Example", "Fuzz", "Benchmark"))]
    edges = []
    for f in funcs:
        for call in f["calls"]:
            qualifier, name = call["qualifier"], call["name"]
            if qualifier in KNOWN_IMPORTS: continue
            targets = by_name.get((f["package_key"], name), [])
            if len(targets) == 1:
                edges.append({"from": f["key"], "to": targets[0]["key"],
                              "resolution": "UNIQUE_NAME_ONLY" if qualifier else "SAME_PACKAGE_NAME"})
    adjacency = collections.defaultdict(list)
    for edge in edges: adjacency[edge["from"]].append(edge["to"])
    id_seen = set()
    tests = []
    package_rows = collections.defaultdict(list)
    for row in census["tests"]:
        test_id = row["id"]
        assert test_id not in id_seen and test_id in matrix_by_id
        id_seen.add(test_id)
        candidates = by_path_name.get((row["path"], row["name"]), [])
        roots = [f for f in candidates if f["line"] == row["line"]]
        root_key = roots[0]["key"] if len(roots) == 1 else None
        seen = set([root_key]) if root_key else set()
        frontier = [(root_key, 0)] if root_key else []
        truncated = False
        while frontier:
            key, depth = frontier.pop(0)
            if depth >= 8:
                if adjacency[key]: truncated = True
                continue
            for child in adjacency[key]:
                if child not in seen:
                    if len(seen) >= 512: truncated = True; break
                    seen.add(child); frontier.append((child, depth + 1))
        merged = collections.Counter()
        env = set()
        for key in seen:
            signs = by_key[key]["lexical_signals"]
            for kind, value in signs.items():
                if kind == "env_keys": env.update(value)
                else: merged[kind] += value
        flags = matrix_by_id[test_id]["flags"]
        if "EXPLICIT_REAL_MODEL_AUTHORIZATION_REQUIRED" in flags:
            lane = "REAL_MODEL_B01_HOLD"
        elif "ACTUAL_NODE_MU_BUNDLE_REQUIRED_LOCAL_FIXTURE_POSSIBLE" in flags:
            lane = "LOCAL_NODE_MU_TLS"
        elif "NATIVE_CHILD_TOOL_RESOURCES_REQUIRE_SCOPE" in flags:
            lane = "LOCAL_NATIVE_CHILD"
        elif "SKIP_PATH_REACHABLE_STATIC" in flags:
            lane = "CONDITIONAL_SKIP_REVIEW"
        elif "LOCAL_HTTP_FIXTURE_CONSTRUCTION_OBSERVED" in flags:
            lane = "LOCAL_HTTP_FIXTURE_REVIEW"
        else:
            lane = "STATIC_NO_RESOURCE_SIGNAL_REVIEW"
        name = row["name"]
        record = {"id": test_id, "name": name, "path": row["path"], "line": row["line"],
                  "package_directory": row["path"].rsplit("/", 1)[0], "package_key": row["package_key"],
                  "root_function": root_key, "reachable_function_keys": sorted(seen),
                  "graph_truncated": truncated, "lexical_signal_counts": dict(merged),
                  "lexical_env_keys": sorted(env), "census_flags": flags, "lane": lane,
                  "classification_authority": "STATIC_REVIEW_ONLY_NOT_SIDE_EFFECT_PROOF"}
        tests.append(record)
        package_rows[record["package_directory"]].append(record)
    package_dirs = {row["directory"] for row in census["packages"]}
    assert len(tests) == len(id_seen) == 745 and len(package_rows) == 27 and len(package_dirs) == 58
    windows_eligible = {}
    for row in tests:
        path = row["path"]
        text = (ROOT / path).read_text(encoding="utf-8")
        header = "\n".join(text.splitlines()[:10])
        excluded = path.endswith("_unix_test.go") or bool(re.search(r"(?m)^//go:build\s+!windows\b", header))
        windows_eligible[row["id"]] = not excluded
        row["windows_static_eligibility"] = "EXCLUDED_BY_EXPLICIT_SOURCE_CONSTRAINT" if excluded else "CANDIDATE_MUST_RECONCILE_GO_LIST"
    packages = []
    for directory in sorted(package_dirs):
        rows = package_rows.get(directory, [])
        lanes = {}
        for lane in sorted({r["lane"] for r in rows}):
            names = sorted({r["name"] for r in rows if r["lane"] == lane and windows_eligible[r["id"]]})
            lanes[lane] = {"test_ids": sorted(r["id"] for r in rows if r["lane"] == lane),
                           "windows_candidate_names": names,
                           "exact_top_regex": "^(?:" + "|".join(re.escape(name) for name in names) + ")$" if names else None}
        if not rows:
            lanes["BUILD_ONLY_NO_TOP_TEST"] = {"test_ids": [], "windows_candidate_names": [],
                                               "exact_top_regex": "^$", "assertions_expected": 0,
                                               "qualification_semantics": "COMPILE_AND_PACKAGE_EXIT_ONLY_NOT_TEST_PASS"}
        packages.append({"directory": directory, "import_arg": "./" + directory,
                         "all_platform_top_test_ids": sorted(r["id"] for r in rows),
                         "windows_candidate_test_ids": sorted(r["id"] for r in rows if windows_eligible[r["id"]]),
                         "lanes": lanes, "actual_target_roster": None,
                         "runtime_graph_qualified": False})
    lane_counts = collections.Counter(r["lane"] for r in tests)
    assert sum(lane_counts.values()) == 745
    callgraph = {"schema": "researchos.current58-whole-go-static-callgraph.v1",
                 "source_commit": census["source_commit"], "source_catalog_ref": pin(catalog_path),
                 "census_ref": pin(CENSUS_PATH),
                 "method": "Go lexical mask, source function declarations, unique same-package name edges, 8-hop/512-node cap; method dispatch and cross-package semantics unresolved",
                 "functions": [{k: v for k, v in f.items() if k != "calls"} for f in funcs],
                 "edges": edges, "tests": tests,
                 "counts": {"go_source_files_checked": len(go_files), "functions": len(funcs),
                            "name_edges": len(edges), "top_tests": len(tests),
                            "init_functions": len(init_refs),
                            "example_fuzz_benchmark_name_matches": len(other_go_test_entry_names),
                            "package_directories_with_top_tests": len(package_rows),
                            "package_directories_without_top_tests": len(package_dirs) - len(package_rows),
                            "truncated_tests": sum(r["graph_truncated"] for r in tests),
                            "windows_explicit_excluded_tests": sum(not windows_eligible[r["id"]] for r in tests)},
                 "runtime_execution": False, "source_acceptance": False}
    contract = {"schema": "researchos.current58-whole-go-finite-source-contract.v1",
                "source_commit": census["source_commit"], "execution_authorized": False,
                "source_acceptance": False, "whole58_qualified": False, "formal_case_accepted_delta": 0,
                "public_source_catalog_ref": pin(catalog_path), "census_ref": pin(CENSUS_PATH),
                "source_files_go_checked_count": len(source_pins),
                "all_platform_top_tests": 745,
                "source_init_function_refs": init_refs,
                "non_top_go_test_entry_names_source_only": other_go_test_entry_names,
                "packages_with_top_tests": len(package_rows),
                "packages_without_top_tests": len(package_dirs) - len(package_rows),
                "windows_static_candidate_tests": sum(windows_eligible.values()),
                "target_platform_actual_go_list_roster": None,
                "packages": packages, "lane_counts": dict(sorted(lane_counts.items())),
                "lane_policy": {
                    "REAL_MODEL_B01_HOLD": "Exactly two real-model-gated tests. No paid/provider request until B01 monetary hard bound and separate Root model scope; cost remains null.",
                    "LOCAL_NODE_MU_TLS": "Pinned Node/Mu bundle and local TLS/SDK/child resources required. Provider inference is not inferred by SDK name.",
                    "LOCAL_NATIVE_CHILD": "Pinned compiler/binaries/host tools, finite process/IO/OS lifecycle scope required.",
                    "CONDITIONAL_SKIP_REVIEW": "Resource or platform gate may skip; any actual skip blocks whole-suite qualification.",
                    "LOCAL_HTTP_FIXTURE_REVIEW": "Local HTTP construction signal; no public network authorization inferred.",
                    "STATIC_NO_RESOURCE_SIGNAL_REVIEW": "No signal in bounded name graph; side-effect freedom and offline safety NOT established."
                },
                "future_root_literals_required": {"registered_scope_ref": None, "grant_ref": None,
                    "current_authority_ref": None, "complete_runtime_resource_catalog_ref": None,
                    "pinned_go_ref": None, "pinned_git_ref": None, "go_env_ref": None,
                    "actual_target_go_list_ref": None, "actual_compiler_input_closure_ref": None,
                    "actual_model_resource_ref": None, "numeric_per_package_wall_s": None,
                    "numeric_total_wall_s": None, "numeric_stdout_bytes": None,
                    "numeric_stderr_bytes": None, "numeric_max_child_processes": None,
                    "numeric_max_http_requests": None, "numeric_max_model_requests": None,
                    "numeric_max_usd": None, "output_root_ref": None},
                "qualification_rule": "Every target-platform test and all 58 packages must be accounted for by fresh Go graph/list, actual single-run exit and per-test PASS; FAIL/SKIP/missing/unexpected/timeout/output-cap breach leaves whole58 false. Independent source signer must be established, never inferred from prior CLI2/Desktop qualifications."}
    write_json("static-callgraph.json", callgraph)
    write_json("whole58-finite.contract.proposed.json", contract)
    print("source", census["source_commit"], "tests", len(tests), "packages", len(packages), "functions", len(funcs), "edges", len(edges))
    print("lane_counts", json.dumps(dict(sorted(lane_counts.items()))))
    print("windows_static_candidates", sum(windows_eligible.values()), "truncated_graphs", callgraph["counts"]["truncated_tests"])


if __name__ == "__main__":
    main()
