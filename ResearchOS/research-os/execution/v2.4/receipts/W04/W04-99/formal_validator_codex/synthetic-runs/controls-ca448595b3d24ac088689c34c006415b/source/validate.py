"""Read-only W04 evidence integrity checks; this is not a product acceptance service.

All JSON shapes in this module are implementation conventions, except values
derived from the pinned frozen package. No subprocesses or filesystem writes.
The caller supplies root-observed trust inputs; different identity strings alone
are never enough to make a formal case countable. See README.md.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys


PREFIX = "execution/v2.4/receipts/W04/W04-99/"
ROOT_INPUT_PREFIX = PREFIX + "integration_codex/"
CASE_IDS = ("C03", "C04", "A01")
GATE_IDS = ("W04-G01", "W04-G02", "W04-G03", "W04-H01", "W04-B01")
PHASES = ("execution", "reviewed", "registered")
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
FROZEN_HASHES = {
    "acceptance.json": "ae8aa1ce632aecce595b2adbcb05fd73aa7360b8fd4186fcef6fd5e7872caa66",
    "tasks.json": "37e1bc901a8843b91ae750c90164ef58560bccc50fa011908b5f3c30809cb8d4",
    "execution.plan.json": "a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17",
}


class InvalidEvidence(ValueError):
    """A stable reason code makes single-defect synthetic controls meaningful."""

    def __init__(self, code, detail):
        super().__init__(f"{code}: {detail}")
        self.code = code


def require(condition, code, detail):
    if not condition:
        raise InvalidEvidence(code, detail)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_sha256(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "JSON_DUPLICATE_KEY", key)
        result[key] = value
    return result


def _float(raw):
    value = float(raw)
    require(math.isfinite(value), "JSON_NONFINITE", raw)
    return value


def strict_json(raw):
    def nonfinite(value):
        raise InvalidEvidence("JSON_NONFINITE", value)
    try:
        return json.loads(raw, object_pairs_hook=_pairs,
                          parse_constant=nonfinite, parse_float=_float)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise InvalidEvidence("JSON_INVALID", str(exc)) from exc


def obj(value, label):
    require(type(value) is dict, "TYPE_OBJECT", label)
    return value


def fields(value, required, optional=(), label="object"):
    obj(value, label)
    require(set(required) <= set(value), "MISSING_FIELD", label + ": " + str(sorted(set(required) - set(value))))
    require(set(value) <= set(required) | set(optional), "UNKNOWN_FIELD", label + ": " + str(sorted(set(value) - set(required) - set(optional))))
    return value


def text(value, label):
    require(type(value) is str and value.strip() and value == value.strip(), "TYPE_TEXT", label)
    return value


def sequence(value, label, nonempty=True):
    require(type(value) is list and (bool(value) or not nonempty), "TYPE_ARRAY", label)
    return value


def exact_ids(value, expected, label):
    sequence(value, label)
    for entry in value:
        text(entry, label)
    require(len(set(value)) == len(value), "DUPLICATE_ID", label)
    require(set(value) == set(expected), "ID_SET", label)


def stamp(value, label):
    text(value, label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidEvidence("TIME_INVALID", label) from exc
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None, "TIME_ZONE", label)
    return parsed


def interval(value, label):
    start = stamp(value["started_at"], label + ".started_at")
    end = stamp(value["ended_at"], label + ".ended_at")
    require(start <= end, "TIME_ORDER", label)
    return start, end


def meaningful(value):
    # False and zero are meaningful observations; empty/missing output is not.
    return value is not None and value != "" and value != [] and value != {}


class Reader:
    def __init__(self, repo):
        self.repo = Path(repo).resolve(strict=True)
        require(self.repo.is_dir(), "REPO", str(repo))
        self.read_hashes = {}

    def path(self, relative, prefix=None):
        text(relative, "path")
        require("\\" not in relative and "\x00" not in relative, "PATH_FORMAT", relative)
        posix, windows = PurePosixPath(relative), PureWindowsPath(relative)
        require(not posix.is_absolute() and not windows.drive and not windows.root,
                "PATH_ESCAPE", relative)
        require(all(part not in ("", ".", "..") for part in relative.split("/")), "PATH_ESCAPE", relative)
        if prefix:
            require(relative.startswith(prefix), "PATH_SCOPE", relative)
        try:
            resolved = (self.repo / relative).resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise InvalidEvidence("FILE_MISSING", relative) from exc
        require(resolved.is_relative_to(self.repo) and resolved.is_file(), "PATH_ESCAPE", relative)
        if prefix:
            boundary = (self.repo / prefix).resolve(strict=True)
            require(resolved.is_relative_to(boundary), "PATH_ESCAPE", relative)
        return resolved

    def supplied(self, path, prefix=None):
        candidate = Path(path)
        if not candidate.is_absolute():
            return self.path(candidate.as_posix(), prefix)
        require(candidate.is_relative_to(self.repo), "PATH_ESCAPE", str(path))
        return self.path(candidate.relative_to(self.repo).as_posix(), prefix)

    def read(self, path):
        raw = Path(path).read_bytes()
        current = hashlib.sha256(raw).hexdigest()
        if path in self.read_hashes:
            require(current == self.read_hashes[path], "INPUT_CHANGED_DURING_READ", str(path))
        self.read_hashes[path] = current
        return strict_json(raw)

    def ref(self, value, prefix=None, locator=False):
        fields(value, ("path", "sha256"), ("locator",) if locator else (), "reference")
        expected = value["sha256"]
        require(type(expected) is str and SHA.fullmatch(expected), "HASH_FORMAT", value["path"])
        path = self.path(value["path"], prefix)
        actual = sha256(path)
        require(actual == expected, "HASH_MISMATCH", value["path"])
        if path in self.read_hashes:
            require(actual == self.read_hashes[path], "INPUT_CHANGED_DURING_READ", value["path"])
        self.read_hashes[path] = actual
        return path

    def document(self, value, prefix=None):
        return self.read(self.ref(value, prefix))

    def raw(self, value):
        path = self.ref(value, PREFIX, locator=True)
        require("locator" in value, "RAW_LOCATOR", value["path"])
        location = obj(value["locator"], "raw locator")
        raw = path.read_bytes()
        if set(location) == {"json_pointer"}:
            pointer = location["json_pointer"]
            require(type(pointer) is str and (pointer == "" or pointer.startswith("/")), "RAW_LOCATOR", str(pointer))
            result = strict_json(raw)
            if pointer:
                for token in pointer[1:].split("/"):
                    require(re.search(r"~(?![01])", token) is None, "RAW_LOCATOR", pointer)
                    token = token.replace("~1", "/").replace("~0", "~")
                    if type(result) is dict:
                        require(token in result, "RAW_LOCATOR_MISSING", pointer)
                        result = result[token]
                    elif type(result) is list:
                        require(re.fullmatch(r"0|[1-9][0-9]*", token) is not None,
                                "RAW_LOCATOR_MISSING", pointer)
                        require(int(token) < len(result), "RAW_LOCATOR_MISSING", pointer)
                        result = result[int(token)]
                    else:
                        raise InvalidEvidence("RAW_LOCATOR_MISSING", pointer)
        elif set(location) == {"line_start", "line_end"}:
            start, end = location["line_start"], location["line_end"]
            require(type(start) is int and type(end) is int, "RAW_LOCATOR", "integer lines")
            try:
                lines = raw.decode("utf-8").splitlines()
            except UnicodeError as exc:
                raise InvalidEvidence("RAW_ENCODING", value["path"]) from exc
            require(1 <= start <= end <= len(lines), "RAW_LOCATOR_MISSING", value["path"])
            result = "\n".join(lines[start - 1:end])
        else:
            raise InvalidEvidence("RAW_LOCATOR", "expected JSON pointer or inclusive line range")
        require(meaningful(result), "RAW_EMPTY", value["path"])
        return result

    def finish(self):
        for path, digest in self.read_hashes.items():
            require(path.is_file() and sha256(path) == digest, "INPUT_CHANGED_DURING_READ", str(path))

    def local_tool(self, path, digest):
        text(path, "tool path")
        windows = PureWindowsPath(path)
        require((Path(path).is_absolute() or windows.is_absolute()) and not windows.drive.startswith("\\\\")
                and not path.startswith("//"), "TOOL_PATH", path)
        require(type(digest) is str and SHA.fullmatch(digest), "HASH_FORMAT", path)
        actual = Path(path).resolve(strict=True)
        require(actual.is_file(), "TOOL_PATH", path)
        if actual not in self.read_hashes:
            self.read_hashes[actual] = sha256(actual)
        require(self.read_hashes[actual] == digest, "TOOL_CHANGED", path)
        return actual


def frozen(reader, spec):
    spec = Path(spec)
    if not spec.is_absolute():
        spec = reader.repo / spec
    spec = spec.resolve(strict=True)
    require(spec.is_relative_to(reader.repo), "SPEC_SCOPE", str(spec))
    documents = {}
    for name, digest in FROZEN_HASHES.items():
        path = reader.supplied(spec / "contracts" / name)
        require(sha256(path) == digest, "FROZEN_BASELINE", name)
        documents[name] = reader.read(path)
    acceptance, tasks, plan = (documents[x] for x in FROZEN_HASHES)
    cases = {c["id"]: c for c in acceptance["cases"]}
    task = next(t for t in tasks["tasks"] if t["task_id"] == "W04")
    require(set(task["owned_acceptance_ids"]) == set(CASE_IDS), "FROZEN_OWNER", "W04")
    for cid in CASE_IDS:
        require(cases[cid]["final_owner_task"] == tasks["acceptance_final_owners"][cid] == "W04",
                "FROZEN_OWNER", cid)
        require(cases[cid]["mode"] == "FIXTURE", "FROZEN_MODE", cid)
    selected = tasks["verification_command_selection"]
    formal = [x for x in selected["formal_case_bindings"] if x["task_id"] == "W04"]
    gates = [x for x in selected["parent_check_bindings"] if x["task_id"] == "W04"]
    return cases, formal, gates, plan, spec


def vector(reader, value, spec, forbidden_paths):
    fields(value, ("schema", "package_version", "spec_files", "source_files", "input_files",
                   "lock_files", "tool_files", "environment", "components"), label="version vector")
    require(value["schema"] == "researchos.w04.version-vector.v1" and value["package_version"] == "2.4.0",
            "SCHEMA", "version vector")
    pinned = {}
    for group in ("spec_files", "source_files", "input_files", "lock_files", "tool_files"):
        seen = set()
        for reference in sequence(value[group], group):
            path = reader.ref(reference)
            require(path not in forbidden_paths, "CIRCULAR_REFERENCE", str(path))
            require(path not in seen, "DUPLICATE_REFERENCE", group)
            seen.add(path)
            pinned[path] = reference["sha256"]
    for name, digest in FROZEN_HASHES.items():
        # Worktrees may keep byte-exact frozen copies in their durable evidence
        # tree. The authoritative spec itself was independently pinned above.
        require(digest in {r["sha256"] for r in value["spec_files"]}, "VECTOR_BASELINE", name)
    for reference in value["tool_files"]:
        identity = reader.document(reference)
        fields(identity, ("schema", "locked_ref", "tools"), label="tool identity")
        require(identity["schema"] == "researchos.w04.tool-identity.v1", "SCHEMA", "tool identity")
        locked_path = reader.ref(identity["locked_ref"])
        require(locked_path in pinned and pinned[locked_path] == identity["locked_ref"]["sha256"], "TOOL_LOCK", "tool identity")
        locked = reader.read(locked_path)
        names = set()
        for tool in sequence(identity["tools"], "tools"):
            fields(tool, ("name", "version", "path", "sha256"), label="tool")
            name = text(tool["name"], "tool name")
            require(name not in names, "DUPLICATE_ID", "tools")
            names.add(name)
            text(tool["version"], "tool version")
            actual = reader.local_tool(tool["path"], tool["sha256"])
            frozen_tool = locked.get("tools", {}).get(name, {})
            require(frozen_tool.get("sha256") == tool["sha256"]
                    and Path(frozen_tool.get("path", "")).resolve() == actual
                    and frozen_tool.get("version_output") == tool["version"], "TOOL_LOCK", name)
    fields(value["environment"], ("os", "arch", "timezone"), label="environment")
    for key, entry in value["environment"].items():
        text(entry, "environment." + key)
    components = fields(value["components"], ("model", "adapter", "rubric", "policy"), label="components")
    for name, component in components.items():
        obj(component, name)
        if component.get("status") == "not_applicable":
            fields(component, ("status", "reason"), label=name)
            text(component["reason"], name + ".reason")
        else:
            fields(component, ("status", "version", "refs"), label=name)
            require(component["status"] == "applicable", "COMPONENT_STATUS", name)
            text(component["version"], name + ".version")
            for reference in sequence(component["refs"], name + ".refs"):
                path = reader.ref(reference)
                require(pinned.get(path) == reference["sha256"], "COMPONENT_UNPINNED", name)
    return pinned


def coverage(reader, value, source_files):
    fields(value, ("roots", "exact_files", "paths_sha256"), label="source coverage")
    observed = set()
    for rule in sequence(value["roots"], "coverage roots"):
        fields(rule, ("path", "patterns"), label="coverage root")
        relative = text(rule["path"], "coverage root path")
        require("\\" not in relative and not PureWindowsPath(relative).drive and not relative.startswith("/")
                and all(p not in ("", ".", "..") for p in relative.split("/")), "PATH_ESCAPE", relative)
        root = (reader.repo / relative).resolve(strict=True)
        require(root.is_relative_to(reader.repo) and root.is_dir(), "PATH_ESCAPE", relative)
        patterns = sequence(rule["patterns"], "coverage patterns")
        for pattern in patterns:
            text(pattern, "coverage pattern")
            require("\\" not in pattern and ".." not in pattern.split("/") and not pattern.startswith("/"),
                    "COVERAGE_PATTERN", pattern)
        for directory, dirs, files in os.walk(root, followlinks=False):
            for name in dirs:
                child = Path(directory) / name
                require(not child.is_symlink() and not child.is_junction(), "COVERAGE_LINK", str(child))
            for name in files:
                child = Path(directory) / name
                local = child.relative_to(root).as_posix()
                if any(fnmatch.fnmatchcase(local, pattern) for pattern in patterns):
                    candidate = child.relative_to(reader.repo).as_posix()
                    reader.path(candidate)
                    observed.add(candidate)
    for relative in sequence(value["exact_files"], "coverage exact files", False):
        reader.path(relative)
        observed.add(relative)
    wanted = {ref["path"] for ref in source_files}
    require(observed == wanted, "SOURCE_COVERAGE", "added/deleted/uncovered applicable source: " + str(sorted(observed ^ wanted)))
    require(value["paths_sha256"] == object_sha256(sorted(observed)), "SOURCE_COVERAGE_DIGEST", "source paths")


def command(reader, value, key, selector, ids, run_id, executor, environment, registered=False, registry=None):
    required = ("schema", "command_key", "task_id", "mode", "run_id", "executor_id", "selector",
                "invocation_kind", "registered_command_revision", "actual_argv", "cwd",
                "environment_variable_names", "started_at", "ended_at", "exit_code", "stdout", "stderr")
    fields(value, required, ("original_dispatch_ref", "source_invocation_refs"), "command")
    require(value["schema"] == "researchos.w04.command.v1", "SCHEMA", "command")
    require(value["command_key"] == key and value["task_id"] == "W04" and value["selector"] == selector,
            "COMMAND_BINDING", key + str(selector))
    require(value["mode"] == "FIXTURE", "MODE", key)
    require(value["run_id"] == run_id and value["executor_id"] == executor, "COMMAND_IDENTITY", key)
    for argument in sequence(value["actual_argv"], "actual_argv"):
        text(argument, "argv")
    text(value["cwd"], "cwd")
    require(Path(value["cwd"]).is_absolute() or PureWindowsPath(value["cwd"]).is_absolute(), "CWD", key)
    names = sequence(value["environment_variable_names"], "environment_variable_names", False)
    for name in names:
        require(type(name) is str and bool(name) and "=" not in name and "\x00" not in name, "ENV_NAME", key)
    require(len(set(names)) == len(names), "DUPLICATE_ID", "environment names")
    interval(value, key)
    require(type(value["exit_code"]) is int and value["exit_code"] == 0, "COMMAND_EXIT", key)
    stdout_path = reader.ref(value["stdout"], PREFIX)
    reader.ref(value["stderr"], PREFIX)
    output = obj(reader.read(stdout_path), "command stdout")
    require(output.get("status") == "PASS" and output.get("task_id") == "W04"
            and output.get("mode") == "FIXTURE", "COMMAND_OUTPUT", key)
    require(all(output.get(k) == v for k, v in selector.items()), "COMMAND_OUTPUT_SELECTOR", key)
    # Selector ambiguity is an error: case and parent check namespaces differ.
    other = "check_id" if "case_id" in selector else "case_id"
    require(other not in output or output[other] is None, "COMMAND_OUTPUT_SELECTOR", key)
    exact_ids(output.get("assertion_ids"), ids, "stdout assertions")
    if "assertions" in output:
        require(type(output["assertions"]) is int and output["assertions"] == len(ids), "COUNT", key)
    require(not output.get("errors") and not output.get("open_blockers"), "COMMAND_OUTPUT", key)
    kind = value["invocation_kind"]
    require(kind in ("DIRECT_DRIVER", "REGISTERED_DISPATCH"), "INVOCATION_KIND", key)
    if kind == "DIRECT_DRIVER":
        require(value["registered_command_revision"] is None and not registered, "UNREGISTERED_COMMAND", key)
    else:
        require(registry is not None, "REGISTRY_REQUIRED", key)
        require(type(value["registered_command_revision"]) is int
                and value["registered_command_revision"] == registry["revision"], "COMMAND_REVISION", key)
        entry = registry["commands"].get(key)
        require(type(entry) is dict and entry.get("state") == "BOUND", "COMMAND_UNBOUND", key)
        admitted = entry.get("selectors", {})
        require("W04" in admitted.get("task_id", []) and all(v in admitted.get(k, []) for k, v in selector.items()),
                "COMMAND_UNBOUND", key)
        require("original_dispatch_ref" in value, "DISPATCH_PROVENANCE", key)
        reader.ref(value["original_dispatch_ref"])
    for source in sequence(value.get("source_invocation_refs", []), "source invocation refs", False):
        reader.ref(source, PREFIX)
    return output


def registered_dispatch(reader, row, binding, registry, registry_hash, execution_ref, pinned):
    """Read the existing dispatcher's actual receipt, without normalizing it."""
    selector_key = "case_id" if "case_id" in binding else "check_id"
    fields(row, ("command_key", selector_key, "mode", "receipt_ref"), label="registered dispatch reference")
    selector_id, key = binding[selector_key], binding["key"]
    require(row["command_key"] == key and row[selector_key] == selector_id and row["mode"] == "FIXTURE",
            "COMMAND_BINDING", selector_id)
    receipt = reader.document(row["receipt_ref"], PREFIX)
    required = ("invocation_id", "command_key", "started_at", "ended_at", "status", "exit_code", "child_exit_code",
                "assertion_ids", "selectors", "scope", "registry_spec", "registered_command_revision", "toolchain_revision",
                "dispatcher_sha256", "input_versions", "code_revision", "argv", "cwd", "environment_names", "stdout", "stderr")
    require(type(receipt) is dict and set(required) <= set(receipt), "DISPATCH_RECEIPT", selector_id)
    invocation = text(receipt["invocation_id"], "invocation_id")
    require(re.fullmatch(r"[0-9a-f-]{36}", invocation), "DISPATCH_INVOCATION", invocation)
    selectors = {"task_id": "W04", "case_id": "", "check_id": "", selector_key: selector_id}
    require(receipt["command_key"] == key and receipt["selectors"] == selectors,
            "COMMAND_BINDING", selector_id)
    require(receipt["registry_spec"] == "v2.4" and receipt["registered_command_revision"] == registry_hash,
            "COMMAND_REVISION", selector_id)
    entry = registry["commands"].get(key)
    require(type(entry) is dict and entry.get("state") == "BOUND", "COMMAND_UNBOUND", key)
    admitted = entry.get("selectors", {})
    require("W04" in admitted.get("task_id", []) and selector_id in admitted.get(selector_key, []),
            "COMMAND_UNBOUND", selector_id)
    require(receipt["scope"] == "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE", "DISPATCH_SCOPE", selector_id)
    require(receipt["status"] == "PASS" and all(type(receipt[k]) is int and receipt[k] == 0
            for k in ("exit_code", "child_exit_code")), "COMMAND_EXIT", selector_id)
    interval(receipt, selector_id)
    require(type(receipt["code_revision"]) is str and COMMIT.fullmatch(receipt["code_revision"]), "CODE_REVISION", selector_id)
    exact_ids(receipt["assertion_ids"], binding["expected_assertion_ids"], "dispatcher IDs")
    argv = sequence(receipt["argv"], "dispatcher argv")
    for argument in argv:
        text(argument, "argv")
    require(argv[1:] == entry.get("argv"), "DISPATCH_ARGV", selector_id)
    expected_cwd = (reader.repo / entry["cwd"]).resolve()
    require(Path(receipt["cwd"]).is_absolute() and Path(receipt["cwd"]).resolve() == expected_cwd,
            "CWD", selector_id)
    names = sequence(receipt["environment_names"], "environment_names", False)
    require(all(type(n) is str and n and "=" not in n and "\x00" not in n for n in names)
            and len(set(names)) == len(names), "ENV_NAME", selector_id)
    locked_path = reader.path("execution/toolchains/locked.json")
    require(sha256(locked_path) == receipt["toolchain_revision"] and pinned.get(locked_path) == receipt["toolchain_revision"],
            "DISPATCH_TOOLCHAIN", selector_id)
    locked = reader.read(locked_path)
    tool = locked.get("tools", {}).get(entry.get("executable_tool"), {})
    require(Path(argv[0]).resolve() == Path(tool.get("path", "")).resolve(), "DISPATCH_EXECUTABLE", selector_id)
    reader.local_tool(tool["path"], tool["sha256"])
    dispatcher = reader.path("execution/command_dispatcher/dispatch.py")
    require(sha256(dispatcher) == receipt["dispatcher_sha256"] and pinned.get(dispatcher) == receipt["dispatcher_sha256"],
            "DISPATCHER_CHANGED", selector_id)
    seen = set()
    for reference in sequence(receipt["input_versions"], "dispatch input versions"):
        path = reader.ref(reference)
        require(path not in seen, "DUPLICATE_REFERENCE", "dispatch input versions")
        seen.add(path)
        require(pinned.get(path) == reference["sha256"], "DISPATCH_INPUT_UNPINNED", str(path))
    for key in ("stdout", "stderr"):
        path = reader.ref(receipt[key])
        expected_path = reader.path("execution/invocations/" + invocation + "/" + key + ".txt")
        require(path == expected_path, "DISPATCH_RAW_IDENTITY", selector_id)
    output = obj(reader.document(receipt["stdout"]), "dispatch stdout")
    require(output.get("status") == "PASS" and output.get("task_id") == "W04" and output.get("mode") == "FIXTURE"
            and output.get(selector_key) == selector_id, "COMMAND_OUTPUT", selector_id)
    other = "check_id" if selector_key == "case_id" else "case_id"
    require(other not in output or output[other] is None, "COMMAND_OUTPUT_SELECTOR", selector_id)
    exact_ids(output.get("assertion_ids"), binding["expected_assertion_ids"], "dispatch raw IDs")
    require(not output.get("errors") and not output.get("open_blockers"), "COMMAND_OUTPUT", selector_id)
    if "assertions" in output:
        require(type(output["assertions"]) is int and output["assertions"] == len(binding["expected_assertion_ids"]),
                "COUNT", selector_id)
    require(output.get("execution_index_ref") == execution_ref, "DISPATCH_EXECUTION_LINK", selector_id)
    reader.ref(output["execution_index_ref"], PREFIX)
    return receipt


def _case(reader, cid, reference_map, index, wanted_vector, spec_case, bindings, registry):
    fields(reference_map, ("run_receipt", "version_manifest", "command_receipt", "assertion_results"), label=cid)
    paths = [reader.ref(r, PREFIX) for r in reference_map.values()]
    require(len(set(paths)) == 4, "DUPLICATE_REFERENCE", cid + " GLOBAL files")
    run, manifest, commands, assertions = [reader.read(path) for path in paths]
    fields(run, ("schema", "case_id", "run_id", "environment_mode", "os", "arch", "timezone",
                 "started_at", "ended_at", "executor_id", "verifier_id"), label="run receipt")
    require(run["schema"] == "researchos.w04.run-receipt.v1", "SCHEMA", cid)
    require(run["case_id"] == cid and run["run_id"] == index["run_id"], "RUN_IDENTITY", cid)
    require(run["environment_mode"] == "FIXTURE", "MODE", cid)
    require(run["executor_id"] == index["executor_id"], "RUN_IDENTITY", cid)
    text(run["verifier_id"], "verifier_id")
    require(run["executor_id"].casefold() != run["verifier_id"].casefold(), "SELF_REVIEW", cid)
    interval(run, cid)
    require({k: run[k] for k in ("os", "arch", "timezone")} == wanted_vector["environment"], "ENVIRONMENT", cid)
    fields(manifest, ("schema", "case_id", "run_id", "code_revision", "dirty", "version_vector_ref"), label="version manifest")
    require(manifest["schema"] == "researchos.w04.version-manifest.v1" and manifest["case_id"] == cid
            and manifest["run_id"] == index["run_id"], "MANIFEST_IDENTITY", cid)
    require(type(manifest["code_revision"]) is str and COMMIT.fullmatch(manifest["code_revision"]), "CODE_REVISION", cid)
    require(type(manifest["dirty"]) is bool, "DIRTY_TYPE", cid)
    actual_vector = reader.document(manifest["version_vector_ref"], PREFIX)
    require(actual_vector == wanted_vector, "STALE_VECTOR", cid)
    expected_ids = [a["id"] for a in spec_case["assertions"]]
    fields(commands, ("schema", "case_id", "run_id", "commands"), label="command receipt")
    require(commands["schema"] == "researchos.w04.command-receipt.v1" and commands["case_id"] == cid
            and commands["run_id"] == index["run_id"], "COMMAND_IDENTITY", cid)
    rows = sequence(commands["commands"], "commands")
    expected_keys = [b["key"] for b in bindings if b["case_id"] == cid]
    exact_ids([x.get("command_key") for x in rows], expected_keys, cid + " command keys")
    for row in rows:
        command(reader, row, row["command_key"], {"case_id": cid}, expected_ids,
                index["run_id"], index["executor_id"], wanted_vector["environment"], registry=registry)
    fields(assertions, ("schema", "case_id", "run_id", "assertions", "scenario"), label="assertion results")
    require(assertions["schema"] == "researchos.w04.assertion-results.v1" and assertions["case_id"] == cid
            and assertions["run_id"] == index["run_id"], "ASSERTION_IDENTITY", cid)
    rows = sequence(assertions["assertions"], "assertion results")
    exact_ids([x.get("id") for x in rows], expected_ids, cid + " assertions")
    expected = {a["id"]: a["expected"] for a in spec_case["assertions"]}
    for row in rows:
        fields(row, ("id", "expected", "actual", "status", "raw_evidence_refs", "command_keys"),
               ("refusal_evidence_refs",), "assertion")
        require(row["expected"] == expected[row["id"]], "ASSERTION_EXPECTED", row["id"])
        require(meaningful(row["actual"]), "ASSERTION_ACTUAL", row["id"])
        require(row["status"] == "PASS", "ASSERTION_STATUS", row["id"])
        exact_ids(row["command_keys"], expected_keys, row["id"] + " command keys")
        for raw in sequence(row["raw_evidence_refs"], "raw evidence"):
            reader.raw(raw)
        for raw in row.get("refusal_evidence_refs", []):
            reader.raw(raw)
    scenario = fields(assertions["scenario"], ("expected", "actual", "raw_evidence_refs"), label="scenario")
    require(type(scenario["expected"]) is dict and bool(scenario["expected"])
            and type(scenario["actual"]) is dict and bool(scenario["actual"]), "SCENARIO", cid)
    for raw in sequence(scenario["raw_evidence_refs"], "scenario raw evidence"):
        reader.raw(raw)
    return run, manifest


def _state(reader, path, plan, phase, index, review_path=None, context_path=None, issuance_path=None):
    state_path = reader.supplied(path)
    require(state_path == (reader.repo / "execution/v2.4/step_state.json").resolve(), "CANONICAL_STATE", str(path))
    state = obj(reader.read(state_path), "step state")
    require(state.get("schema_version") == "1.0" and state.get("package_version") == "2.4.0"
            and state.get("plan_sha256") == FROZEN_HASHES["execution.plan.json"], "STATE_BASELINE", "step state")
    rows = sequence(state.get("steps"), "step state", False)
    require(len({x["id"] for x in rows}) == len(rows), "DUPLICATE_ID", "step state")
    indexed = {x["id"]: x for x in rows}
    planned = {x["id"]: x for x in plan["steps"]}
    require(set(indexed) <= set(planned), "STATE_UNKNOWN_STEP", "step state")
    for dependency in planned["W04-99"]["dependencies"]:
        require(indexed.get(dependency, {}).get("status") == "ACCEPTED", "DEPENDENCY", dependency)
    if phase != "registered":
        return
    owner = indexed.get("W04-99", {})
    require(owner.get("status") == "ACCEPTED", "OWNER_NOT_REGISTERED", "W04-99")
    require(owner.get("executor_id") == index["executor_id"], "REGISTERED_IDENTITY", "executor")
    references = sequence(owner.get("evidence"), "registered evidence")
    registered = {}
    for reference in references:
        fields(reference, ("path", "sha256"), label="state reference")
        # Canonical state refs are relative to execution/v2.4, unlike package refs.
        translated = {"path": "execution/v2.4/" + reference["path"], "sha256": reference["sha256"]}
        target = reader.ref(translated)
        require(target not in registered, "DUPLICATE_REFERENCE", "state evidence")
        registered[target] = reference["sha256"]
    for target in (review_path, context_path, issuance_path):
        require(target in registered, "UNREGISTERED_REFERENCE", str(target))
    # A second independently signed owned-case review needs an explicit current
    # supersession chain. We fail closed rather than choose by timestamp.
    for target in registered:
        if target == review_path or target.suffix != ".json":
            continue
        value = reader.read(target)
        if type(value) is dict and value.get("schema") == "researchos.w04.independent-review.v1":
            raise InvalidEvidence("CONFLICTING_REVIEW", str(target))
    return owner


def check(repo, state, spec, current_index, independent_review=None, root_observed_issuance=None, phase="execution"):
    """Validate immutable evidence, returning counts without writing anything.

    Raises InvalidEvidence. current_index and root_observed_issuance are
    root-owned integration inputs, not executor identity assertions.
    """
    require(phase in PHASES, "PHASE", str(phase))
    reader = Reader(repo)
    cases, formal_bindings, gate_bindings, plan, spec_root = frozen(reader, spec)
    context_path = reader.supplied(current_index, ROOT_INPUT_PREFIX)
    context = fields(reader.read(context_path), ("schema", "scope", "task_id", "step_id", "execution_index",
                     "version_vector", "execution_source_snapshot", "source_coverage"), ("registry_ref", "registered_dispatches"), "current context")
    require(context["schema"] == "researchos.w04.current-context.v1" and context["scope"] == "ROOT_CURRENT_APPLICABILITY"
            and context["task_id"] == "W04" and context["step_id"] == "W04-99", "CONTEXT_IDENTITY", "root context")
    index_path = reader.ref(context["execution_index"], PREFIX)
    require(index_path != context_path, "CIRCULAR_REFERENCE", "context/index")
    index = fields(reader.read(index_path), ("schema", "task_id", "step_id", "run_id", "executor_id", "cases", "parent_gates"), label="execution index")
    require(index["schema"] == "researchos.w04.execution-index.v1" and index["task_id"] == "W04"
            and index["step_id"] == "W04-99", "INDEX_IDENTITY", "execution index")
    text(index["run_id"], "run_id")
    text(index["executor_id"], "executor_id")
    fields(index["cases"], CASE_IDS, label="cases")
    fields(index["parent_gates"], GATE_IDS, label="parent gates")
    forbidden = {context_path, index_path}
    pinned = vector(reader, context["version_vector"], spec_root, forbidden)
    coverage(reader, context["source_coverage"], context["version_vector"]["source_files"])
    snapshot = fields(context["execution_source_snapshot"], ("code_revision", "dirty", "version_vector_sha256"), label="root execution snapshot")
    require(type(snapshot["code_revision"]) is str and COMMIT.fullmatch(snapshot["code_revision"])
            and type(snapshot["dirty"]) is bool, "ROOT_SOURCE_SNAPSHOT", "code/dirty")
    require(snapshot["version_vector_sha256"] == object_sha256(context["version_vector"]), "ROOT_SOURCE_SNAPSHOT", "vector digest")
    registry = reader.document(context["registry_ref"]) if "registry_ref" in context else None
    if registry is not None:
        require(reader.ref(context["registry_ref"]) == (reader.repo / "execution/v2.4/commands.json").resolve(),
                "CANONICAL_REGISTRY", "registry")
        require(type(registry.get("revision")) is int and registry["revision"] > 0, "COMMAND_REVISION", "registry")
    runs = {}
    for cid in CASE_IDS:
        runs[cid], manifest = _case(reader, cid, index["cases"][cid], index, context["version_vector"], cases[cid], formal_bindings, registry)
        require(manifest["code_revision"] == snapshot["code_revision"] and manifest["dirty"] == snapshot["dirty"],
                "ROOT_SOURCE_SNAPSHOT", cid)
    for binding in gate_bindings:
        gid = binding["check_id"]
        row = reader.document(index["parent_gates"][gid], PREFIX)
        command(reader, row, binding["key"], {"check_id": gid}, [gid], index["run_id"],
                index["executor_id"], context["version_vector"]["environment"], registry=registry)
    _state(reader, state, plan, phase="execution", index=index)
    result = {"schema": "researchos.w04.integrity-result.v1", "scope": "READ_ONLY_EVIDENCE_INTEGRITY",
              "phase": phase, "integrity": "PASS", "task_id": "W04", "step_id": "W04-99",
              "assertion_count": 10, "executed_case_count": 3, "formal_command_count": 6,
              "parent_gate_count": 5, "eligible_owned_cases": [], "eligible_owned_case_count": 0, "formal_accepted_count": 0,
              "product_business_acceptance_created": False,
              "semantic_limit": "Integrity does not establish scenario correctness or authenticate identities without root-observed issuance."}
    if phase == "execution":
        reader.finish()
        return result
    require(independent_review is not None and root_observed_issuance is not None, "INDEPENDENT_REQUIRED", phase)
    review_path = reader.supplied(independent_review, PREFIX)
    require(not review_path.is_relative_to((reader.repo / (PREFIX + "executor_codex/")).resolve()), "REVIEW_OWNER", str(review_path))
    issuance_path = reader.supplied(root_observed_issuance, ROOT_INPUT_PREFIX)
    require(len({review_path, issuance_path, context_path, index_path}) == 4, "CIRCULAR_REFERENCE", "review graph")
    review = fields(reader.read(review_path), ("schema", "scope", "task_id", "step_id", "executor_id", "verifier_id",
                    "issued_at", "acceptance_baseline_ref", "evidence_index_ref", "current_context_ref",
                    "owned_case_verdicts", "parent_gate_verdicts", "open_blockers", "construction_decision"), label="independent review")
    require(review["schema"] == "researchos.w04.independent-review.v1" and review["scope"] == "EXTERNAL_FIXTURE_VERIFICATION"
            and review["task_id"] == "W04" and review["step_id"] == "W04-99", "REVIEW_SCOPE", "independent review")
    verifier = text(review["verifier_id"], "verifier_id")
    require(review["executor_id"] == index["executor_id"] and verifier.casefold() != index["executor_id"].casefold(),
            "SELF_REVIEW", "independent review")
    issued_at = stamp(review["issued_at"], "issued_at")
    for cid, run in runs.items():
        require(run["verifier_id"] == verifier and stamp(run["ended_at"], cid) <= issued_at, "REVIEW_IDENTITY_TIME", cid)
    require(reader.ref(review["acceptance_baseline_ref"]) == (spec_root / "contracts/acceptance.json").resolve(), "REVIEW_BASELINE", "review")
    require(reader.ref(review["evidence_index_ref"]) == index_path and reader.ref(review["current_context_ref"]) == context_path,
            "REVIEW_INDEX", "review")
    require(review["open_blockers"] == [] and review["construction_decision"] == "ACCEPTED", "REVIEW_DECISION", "review")
    rows = sequence(review["owned_case_verdicts"], "owned case verdicts")
    exact_ids([x.get("case_id") for x in rows], CASE_IDS, "owned cases")
    for row in rows:
        fields(row, ("case_id", "final_owner_task", "mode", "assertion_ids", "status", "evidence_pointer", "semantic_review"), label="case verdict")
        cid = row["case_id"]
        require(row["final_owner_task"] == "W04" and row["mode"] == "FIXTURE", "CASE_OWNER_MODE", cid)
        exact_ids(row["assertion_ids"], [a["id"] for a in cases[cid]["assertions"]], cid)
        require(row["status"] == "PASS" and row["evidence_pointer"] == "/cases/" + cid, "CASE_VERDICT", cid)
        semantic = fields(row["semantic_review"], ("status", "statement", "raw_evidence_refs"), label="semantic review")
        require(semantic["status"] == "CONFIRMED", "SEMANTIC_REVIEW", cid)
        text(semantic["statement"], "semantic statement")
        for raw in sequence(semantic["raw_evidence_refs"], "review raw evidence"):
            reader.raw(raw)
    rows = sequence(review["parent_gate_verdicts"], "parent gate verdicts")
    exact_ids([x.get("check_id") for x in rows], GATE_IDS, "reviewed gates")
    for row in rows:
        fields(row, ("check_id", "mode", "status", "command_ref"), label="gate verdict")
        require(row["mode"] == "FIXTURE" and row["status"] == "PASS", "GATE_VERDICT", row["check_id"])
        require(row["command_ref"] == index["parent_gates"][row["check_id"]], "GATE_REFERENCE", row["check_id"])
    issuance = fields(reader.read(issuance_path), ("schema", "scope", "observer_id", "observed_at", "issuer_id",
                      "review_ref", "current_context_ref", "channel", "message_id", "message_ref"), label="root observed issuance")
    require(issuance["schema"] == "researchos.w04.root-observed-issuance.v1" and issuance["scope"] == "ROOT_OBSERVED_INDEPENDENT_ISSUANCE",
            "ISSUANCE_SCOPE", "issuance")
    observer = text(issuance["observer_id"], "observer_id")
    require(observer.casefold() not in {verifier.casefold(), index["executor_id"].casefold()}, "ISSUANCE_OBSERVER", observer)
    require(issuance["issuer_id"] == verifier and stamp(issuance["observed_at"], "observed_at") >= issued_at,
            "ISSUANCE_IDENTITY", "issuance")
    require(reader.ref(issuance["review_ref"]) == review_path and reader.ref(issuance["current_context_ref"]) == context_path,
            "ISSUANCE_REFERENCE", "issuance")
    require(issuance["channel"] == "independent_agent_message", "ISSUANCE_CHANNEL", "issuance")
    text(issuance["message_id"], "message_id")
    message = obj(reader.document(issuance["message_ref"], ROOT_INPUT_PREFIX), "observed message")
    require(message.get("sender") == verifier and message.get("message_id") == issuance["message_id"]
            and message.get("review_sha256") == sha256(review_path)
            and meaningful(message.get("content")), "ISSUANCE_MESSAGE", "root observed source")
    require(registry is not None and "registered_dispatches" in context, "REGISTERED_DISPATCHES_REQUIRED", phase)
    dispatches = sequence(context["registered_dispatches"], "registered dispatches")
    expected = {b["key"] + ":" + b.get("case_id", b.get("check_id")): b for b in formal_bindings + gate_bindings}
    actual_ids = [row.get("command_key", "") + ":" + row.get("case_id", row.get("check_id", "")) for row in dispatches]
    exact_ids(actual_ids, expected, "registered dispatches")
    for name, row in zip(actual_ids, dispatches):
        registered_dispatch(reader, row, expected[name], registry, context["registry_ref"]["sha256"],
                            context["execution_index"], pinned)
    result["eligible_owned_cases"] = list(CASE_IDS)
    result["eligible_owned_case_count"] = 3
    if phase == "registered":
        owner = _state(reader, state, plan, phase, index, review_path, context_path, issuance_path)
        require(owner.get("verifier_id") == verifier and stamp(owner.get("accepted_at"), "accepted_at") >= issued_at,
                "REGISTERED_IDENTITY", "verifier/time")
        result["formal_accepted_count"] = 3
    reader.finish()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "state", "spec", "current-index"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--independent-review")
    parser.add_argument("--root-observed-issuance")
    parser.add_argument("--phase", choices=PHASES, default="execution")
    args = parser.parse_args(argv)
    try:
        result = check(args.repo, args.state, args.spec, args.current_index,
                       args.independent_review, args.root_observed_issuance, args.phase)
    except (InvalidEvidence, OSError, KeyError, TypeError, StopIteration) as exc:
        result = {"schema": "researchos.w04.integrity-result.v1", "scope": "READ_ONLY_EVIDENCE_INTEGRITY",
                  "integrity": "FAIL", "phase": args.phase, "reason_code": getattr(exc, "code", "MALFORMED_INPUT"),
                  "error": str(exc), "eligible_owned_cases": [], "formal_accepted_count": 0,
                  "product_business_acceptance_created": False}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["integrity"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
