"""Strict, read-only W07 profile. Product LIVE and injected faults stay separate.

Loaded only from the integrator's fixed repository path; receipt code is never
imported. The caller supplies the frozen W04 reader primitives without altering
their prefix or their acceptance behavior.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit

PREFIX = "execution/v2.4/receipts/W07/W07-99/"
MODULE = "execution/v2.4/formal_profile_w07.py"
SCHEMAS = {"context": "researchos.w07.current-context.v1",
           "review": "researchos.w07.independent-review.v1",
           "issuance": "researchos.w07.root-observed-issuance.v1"}
IDS = tuple("A05-0" + str(i) for i in range(1, 6))
GATES = ("W07-G01", "W07-G02", "W07-H07")
FROZEN_W07 = {"harness.contract.json": "36aa036ee6f1ca3eecc33d71a12580ddf680b51be3eb055cc7fcc43dd649b920",
              "W07-99.md": "eceedadbf3f14bba86587b6619f89e42182e5c1ab2428ece599133d93043d4de"}
FAULTS = {"not_configured": "NOT_CONFIGURED", "429": "RATE_LIMITED",
          "401_or_revoked": "UNAVAILABLE", "timeout": "PARTIAL",
          "empty_valid_result": "COMPLETE", "visible_empty": "PARTIAL",
          "index_only": "PARTIAL", "pr_open": "COMPLETE",
          "pr_closed_unmerged": "COMPLETE", "pr_merged": "COMPLETE"}
EXTRA_FAULTS = {"cycle_partial", "effect_confirmed", "effect_unresolved"}
MINIMUM_SOURCE = {MODULE, "execution/v2.4/formal_case_index.py",
                  "execution/command_dispatcher/dispatch.py", "ops/ci/sources.py",
                  "tests/sources/check/main.py", "tests/sources/live/main.go",
                  "internal/domain/sources.go", "internal/domain/sources_health.go",
                  "internal/domain/research.go", "internal/domain/research_acceptance.go",
                  "internal/domain/research_source_windows.go",
                  "internal/domain/operations.go",
                  "adapters/sources/health.go", "adapters/sources/github_pr.go",
                  "adapters/sources/x.go"}


def _digest(value):
    return value[7:] if isinstance(value, str) and value.startswith("sha256:") else value


def _same_ref(api, left, right):
    for ref in (left, right):
        api.fields(ref, ("path", "sha256"), label="W07 reference identity")
    return left["path"] == right["path"] and _digest(left["sha256"]) == _digest(right["sha256"])


def _ref(api, reader, ref, *, raw=False):
    api.fields(ref, ("path", "sha256"), ("locator",) if raw else (), "W07 reference")
    normalized = dict(ref, sha256=_digest(ref["sha256"]))
    return reader.ref(normalized, PREFIX, locator=raw)


def _document(api, reader, ref):
    return reader.read(_ref(api, reader, ref))


def _bytes(api, reader, ref):
    return _ref(api, reader, ref).read_bytes()


def raw(api, reader, ref):
    """W07-bound locator; never changes Reader.raw's fixed W04 boundary."""
    content = _ref(api, reader, ref, raw=True).read_bytes()
    loc = api.obj(ref.get("locator"), "raw locator")
    if set(loc) == {"json_pointer"}:
        pointer = loc["json_pointer"]
        api.require(type(pointer) is str and (not pointer or pointer.startswith("/")), "RAW_LOCATOR", str(pointer))
        value = api.strict_json(content)
        for token in pointer[1:].split("/") if pointer else ():
            api.require(re.search(r"~(?![01])", token) is None, "RAW_LOCATOR", pointer)
            token = token.replace("~1", "/").replace("~0", "~")
            if isinstance(value, dict):
                api.require(token in value, "RAW_LOCATOR_MISSING", pointer)
                value = value[token]
            else:
                api.require(isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", token)
                            and int(token) < len(value), "RAW_LOCATOR_MISSING", pointer)
                value = value[int(token)]
    else:
        api.fields(loc, ("line_start", "line_end"), label="raw locator")
        first, last = loc["line_start"], loc["line_end"]
        lines = content.decode("utf-8").splitlines()
        api.require(type(first) is int and type(last) is int and 1 <= first <= last <= len(lines), "RAW_LOCATOR", ref["path"])
        value = "\n".join(lines[first - 1:last])
    api.require(api.meaningful(value), "RAW_EMPTY", ref["path"])
    return value


def _vector(api, reader, context):
    vector = api.fields(context["version_vector"],
                        ("schema", "package_version", "spec_files", "source_files", "input_files", "lock_files",
                         "tool_files", "environment", "components"), label="W07 vector")
    api.require(vector["schema"] == "researchos.w07.version-vector.v1" and vector["package_version"] == "2.4.0", "SCHEMA", "W07 vector")
    pinned, paths = {}, set()
    for group in ("spec_files", "source_files", "input_files", "lock_files", "tool_files"):
        local = set()
        for ref in api.sequence(vector[group], group):
            try:
                path = reader.ref(ref)
            except api.InvalidEvidence as exc:
                if exc.code in {"HASH_MISMATCH", "FILE_MISSING"}:
                    raise api.InvalidEvidence("NEEDS_REVALIDATION", ref["path"]) from exc
                raise
            api.require(path not in local, "DUPLICATE_REFERENCE", group)
            local.add(path)
            if path in pinned:
                api.require(pinned[path] == ref["sha256"], "VECTOR_CONFLICT", ref["path"])
            pinned[path] = ref["sha256"]
            paths.add(ref["path"])
    source = {ref["path"] for ref in vector["source_files"]}
    api.require(MINIMUM_SOURCE <= source, "SOURCE_COVERAGE", "missing W07 implementation or trusted tooling")
    api.coverage(reader, context["source_coverage"], vector["source_files"])
    for name, digest in {**api.FROZEN_HASHES, **FROZEN_W07}.items():
        api.require(any(ref["sha256"] == digest and Path(ref["path"]).name == name for ref in vector["spec_files"]), "VECTOR_BASELINE", name)
    tools = {}
    for ref in vector["tool_files"]:
        identity = reader.document(ref)
        api.fields(identity, ("schema", "locked_ref", "tools"), label="W07 tool identity")
        api.require(identity["schema"] == "researchos.w07.tool-identity.v1", "SCHEMA", "tools")
        lock_path = reader.ref(identity["locked_ref"])
        api.require(pinned.get(lock_path) == identity["locked_ref"]["sha256"], "TOOL_LOCK", "tool identity")
        locked = reader.read(lock_path)
        for tool in api.sequence(identity["tools"], "tools"):
            api.fields(tool, ("name", "version", "path", "sha256"), label="tool")
            name = api.text(tool["name"], "tool name")
            api.require(name not in tools, "DUPLICATE_ID", name)
            actual = reader.local_tool(tool["path"], tool["sha256"])
            expected = locked.get("tools", {}).get(name, {})
            api.require(expected.get("sha256") == tool["sha256"] and Path(expected.get("path", "")).resolve() == actual
                        and expected.get("version_output") == tool["version"], "TOOL_LOCK", name)
            tools[name] = tool
    api.require({"go", "python", "browser_act"} <= set(tools), "TOOL_LOCK", "three execution tools")
    environment = api.fields(vector["environment"], ("os", "arch", "timezone"), label="environment")
    for name, value in environment.items():
        api.text(value, name)
    components = api.fields(vector["components"], ("model", "adapter", "rubric", "policy"), label="components")
    for name, component in components.items():
        if name in {"model", "rubric"}:
            api.fields(component, ("status", "reason"), label=name)
            api.require(component["status"] == "not_applicable", "COMPONENT_STATUS", name)
            api.text(component["reason"], name)
        else:
            api.fields(component, ("status", "version", "refs"), label=name)
            api.require(component["status"] == "applicable", "COMPONENT_STATUS", name)
            api.text(component["version"], name)
            for ref in api.sequence(component["refs"], name):
                api.require(pinned.get(reader.ref(ref)) == ref["sha256"], "COMPONENT_UNPINNED", name)
    for key in ("execution/v2.4/commands.json", "execution/commands.json", "execution/toolchains/locked.json"):
        api.require(key in paths, "VECTOR_INPUT", key)
    # Preserve the separately reviewed strict compatibility implementation.
    prefix = reader.path("execution/v2.4/formal_case_index.py").read_bytes()[:51719]
    api.require(hashlib.sha256(prefix).hexdigest() == "92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1", "W04_PREFIX_CHANGED", "strict W04 compatibility")
    return pinned, tools


class Graph:
    """Only fixed, parameterized source evidence queries on immutable snapshots."""
    def __init__(self, api, reader, ref, closed):
        self.api = api
        api.require(closed is True, "DB_SNAPSHOT", "closed or VACUUM snapshot required")
        self.path = _ref(api, reader, ref)
        companions = [Path(str(self.path) + suffix) for suffix in ("-wal", "-journal")]
        api.require(all(not p.exists() or p.stat().st_size == 0 for p in companions), "DB_SNAPSHOT", "uncheckpointed companion")
        self.db = sqlite3.connect(self.path.as_uri() + "?mode=ro&immutable=1", uri=True)
        self.db.execute("PRAGMA query_only=ON")

    def close(self):
        self.db.close()

    def object(self, project, kind, ident, revision=None):
        self.api.require(kind in {"Artifact", "Evidence", "SourceCursor", "ProjectProfile", "ResearchCycle", "ResourceRequest"}, "DB_QUERY_SCOPE", kind)
        if revision is None:
            rows = self.db.execute("SELECT body FROM domain_objects WHERE project=? AND kind=? AND id=?", (project, kind, ident)).fetchall()
        else:
            rows = self.db.execute("SELECT body FROM domain_versions WHERE project=? AND kind=? AND id=? AND revision=?", (project, kind, ident, revision)).fetchall()
        self.api.require(len(rows) == 1, "DB_REFERENCE", str((kind, ident, revision)))
        body = self.api.obj(self.api.strict_json(rows[0][0]), "domain body")
        self.api.require(body.get("id") == ident and (revision is None or body.get("revision") == revision), "DB_REFERENCE", ident)
        return body

    def referenced(self, project, ref, kind):
        self.api.fields(ref, ("entity_type", "id", "revision", "content_hash"), label="domain ref")
        self.api.require(ref["entity_type"] == kind and type(ref["revision"]) is int and ref["revision"] > 0, "DB_REFERENCE", kind)
        body = self.object(project, kind, ref["id"], ref["revision"])
        self.api.require(body.get("content_hash") == ref["content_hash"], "DB_BODY_HASH", ref["id"])
        if kind in {"Artifact", "Evidence"}:
            current = self.object(project, kind, ref["id"])
            self.api.require(current.get("validity") == "CURRENT" and current.get("content_hash") == ref["content_hash"], "DB_REFERENCE_VALIDITY", ref["id"])
        return body

    @staticmethod
    def ref(body, kind):
        return {"entity_type": kind, "id": body["id"], "revision": body["revision"], "content_hash": body.get("content_hash")}

    def artifact(self, project, ref):
        body = self.referenced(project, ref, "Artifact")
        rows = self.db.execute("SELECT bytes,content_hash,sealed FROM uploaded_content WHERE project=? AND storage_key=?", (project, body["storage_key"])).fetchall()
        self.api.require(len(rows) == 1 and rows[0][2] == 1, "DB_SEALED", ref["id"])
        content = bytes(rows[0][0])
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        self.api.require(digest == rows[0][1] == body["content_hash"] == ref["content_hash"] and len(content) == body["byte_size"], "DB_BODY_HASH", ref["id"])
        return body, content

    def artifact_id(self, project, ident):
        body = self.object(project, "Artifact", ident)
        return self.artifact(project, self.ref(body, "Artifact"))

    def health(self, project, ref, reported):
        artifact, content = self.artifact(project, ref)
        doc = self.api.obj(self.api.strict_json(content), "sealed health")
        self.api.require(artifact["kind"] == "REPORT" and artifact["evidence_kind"] == "GENERATED"
                         and artifact["media_type"] == "application/vnd.researchos.source-health.v1+json"
                         and doc["schema"] == "researchos.source-health.v1" and doc["health"] == reported, "DB_HEALTH", ref["id"])
        cursor = self.referenced(project, doc["cursor_ref"], "SourceCursor")
        profile = self.referenced(project, doc["profile_ref"], "ProjectProfile")
        configs = [v for v in profile["source_configs"] if v["source_id"] == doc["source_id"]]
        self.api.require(len(configs) == 1 and "sha256:" + self.api.object_sha256(configs[0]) == doc["config_hash"]
                         and cursor["source_id"] == doc["source_id"] and cursor["query_hash"] == doc["query_hash"], "DB_HEALTH_BINDING", ref["id"])
        self.api.require(doc["query"] == configs[0]["query"]
                         and doc["query_hash"] == "sha256:" + self.api.object_sha256(configs[0]["query"]),
                         "DB_HEALTH_BINDING", "sealed configured query/hash")
        self.api.require(doc["source_refs"] == artifact["source_refs"], "DB_HEALTH_BINDING", "health lineage")
        for source in doc["source_refs"]:
            self.referenced(project, source, source["entity_type"])
        return doc, cursor


def _url(api, value, kind):
    parsed = urlsplit(api.text(value, "provider URL"))
    allowed = {"GITHUB": {"github.com", "api.github.com", "raw.githubusercontent.com"},
               "PAPER": {"arxiv.org", "export.arxiv.org"}, "X": {"x.com"}}[kind]
    api.require(parsed.scheme == "https" and parsed.hostname in allowed and not parsed.username and not parsed.password
                and not parsed.fragment, "SOURCE_ORIGIN", value)
    return parsed


def _invocation(api, reader, row, mode, bounds, require_output=True):
    api.require(row.get("measurement_mode") == mode and type(row.get("exit_code")) is int
                and row["exit_code"] == 0 and row.get("timed_out", False) is False, "COMMAND_EXIT", mode)
    start, end = api.interval(row, mode)
    api.require(bounds[0] <= start <= end <= bounds[1], "INVOCATION_TIME", mode)
    for arg in api.sequence(row.get("actualargv"), "actualargv"):
        api.text(arg, "argv")
    api.require(Path(row.get("cwd", "")).is_absolute(), "CWD", mode)
    stdout, stderr = _bytes(api, reader, row["stdout_ref"]), _bytes(api, reader, row["stderr_ref"])
    api.require(bool(stdout) or not require_output, "RAW_EMPTY", mode)
    return stdout, stderr


def _source(api, reader, row, bounds, tools, binary_ref):
    kind = row["kind"]
    api.require(kind in {"GITHUB", "PAPER", "X"}, "SOURCE_KIND", kind)
    stdout, _ = _invocation(api, reader, row, "LIVE_SERVICE", bounds)
    report = _document(api, reader, row["report_ref"])
    api.require(api.strict_json(stdout) == report, "SOURCE_RAW_REPORT", kind)
    api.require(report.get("status") == "PASS" and report.get("scope") == "LIVE_SERVICE" and report.get("source") == kind,
                "SOURCE_POSITIVE", kind)
    inputs = _document(api, reader, row["request_inputs_ref"])
    for field in ("source_id", "query", "window_from", "window_to"):
        api.require(inputs.get(field) == report[field], "SOURCE_REQUEST", kind + ":" + field)
    api.require(inputs["kind"] == kind, "SOURCE_REQUEST", kind)
    if kind == "X":
        api.require(inputs.get("browser_id") == "direct_local_120993884286222444", "AUTHORIZED_BROWSER", kind)
    window = (api.stamp(report["window_from"], "from"), api.stamp(report["window_to"], "to"))
    api.require(window[0] < window[1] <= api.stamp(report["fetched_at"], "fetched"), "SOURCE_WINDOW", kind)
    for key in ("request_urls", "final_urls"):
        for value in api.sequence(report.get(key), key):
            _url(api, value, kind)
    binary = Path(row["cwd"]) / binary_ref["path"]
    _ref(api, reader, binary_ref)
    api.require(len(row["actualargv"]) == 1 and Path(row["actualargv"][0]) == binary, "SOURCE_COMMAND", kind)
    graph = Graph(api, reader, row["db_snapshot_ref"], row.get("db_closed_or_vacuum_snapshot"))
    try:
        api.require(reader.path(report["db_path"].replace("\\", "/"), PREFIX) == graph.path, "DB_SNAPSHOT", kind)
        project = report["project_id"]
        cursor = graph.object(project, "SourceCursor", report["cursor_id"])
        api.require(cursor["source_id"] == report["source_id"], "DB_CURSOR", kind)
        health_doc, _ = graph.health(project, report["health_artifact_ref"], report["health"])
        profile = graph.referenced(project, health_doc["profile_ref"], "ProjectProfile")
        config = next(c for c in profile["source_configs"] if c["source_id"] == report["source_id"])
        api.require(health_doc["source_id"] == report["source_id"] and health_doc["query_hash"] == cursor["query_hash"]
                    and health_doc["query"] == report["query"] and config["kind"] == kind, "DB_HEALTH_BINDING", kind)
        health = report["health"]
        api.require(health["requested_from"] == report["window_from"] and health["requested_to"] == report["window_to"], "SOURCE_WINDOW", kind)
        api.require(health["status"] in {"PARTIAL", "COMPLETE"} and health["full_read_count"] > 0, "SOURCE_POSITIVE", kind)
        manifest_a, manifest_raw = graph.artifact_id(project, report["manifest"]["artifact_id"])
        manifest = api.strict_json(manifest_raw)
        api.require(manifest_a["content_hash"] == report["manifest"]["sha256"] and manifest["source_id"] == report["source_id"]
                    and manifest["query_hash"] == cursor["query_hash"] and manifest["window_from"] == report["window_from"]
                    and manifest["window_to"] == report["window_to"], "DB_MANIFEST", kind)
        api.require(manifest["complete"] == report["page_complete"] and manifest["health"] == health
                    and manifest["request_urls"] == report["request_urls"] and manifest["final_urls"] == report["final_urls"], "DB_MANIFEST", "page coverage/provenance")
        raw_a, raw_bytes = graph.artifact_id(project, report["raw_page"]["artifact_id"])
        api.require(raw_a["content_hash"] == report["raw_page"]["sha256"] and manifest["raw_artifact_ref"] == graph.ref(raw_a, "Artifact"), "DB_MANIFEST", kind)
        items = api.sequence(report["items"], "positive items")
        api.require(health["full_read_count"] == len(items), "SOURCE_FULL_READ", kind)
        seen = set()
        for item in items:
            api.require(item["evidence_id"] not in seen, "DUPLICATE_ID", kind)
            seen.add(item["evidence_id"])
            ev = graph.object(project, "Evidence", item["evidence_id"])
            api.require(graph.ref(ev, "Evidence") in manifest["evidence_refs"], "DB_LINEAGE", kind)
            for a, b in (("source_kind", "source"), ("canonical_url", "url"), ("publisher", "author"),
                         ("upstream_revision", "upstream_revision"), ("published_at", "published_at"),
                         ("retrieved_at", "retrieved_at"), ("snapshot_artifact_ref", "artifact_ref")):
                api.require(ev.get(a) == (report[b] if b == "source" else item[b]), "DB_ITEM", kind + ":" + a)
            for name in ("url", "author", "upstream_revision", "locator"):
                api.text(item[name], kind + ":" + name)
            _url(api, item["url"], kind)
            api.require(window[0] <= api.stamp(item["published_at"], "published") <= window[1], "SOURCE_WINDOW", kind)
            _, content = graph.artifact(project, item["artifact_ref"])
            api.require(content and item["body_sha256"] == item["artifact_ref"]["content_hash"], "DB_BODY_HASH", kind)
            metas = [m for m in manifest["item_metadata"] if m["upstream_id"] == item["upstream_id"]]
            api.require(len(metas) == 1 and metas[0]["canonical_url"] == item["url"] and metas[0]["body_sha256"] == item["body_sha256"]
                        and metas[0].get("read_level") != "INDEX", "SOURCE_FULL_READ", kind)
            if kind == "X":
                api.require(ev["stance"] == "CONTEXT" and ev["verification_status"] == "UNVERIFIED"
                            and ev.get("origin_evidence_id") is None, "X_ADOPTION", item["evidence_id"])
        if report["page_complete"] is not True:
            api.require(cursor.get("covered_until") is None, "FALSE_WINDOW_COVERAGE", kind)
        pages = graph.db.execute("SELECT window_from,window_to,page_cursor_out,complete FROM source_pages WHERE project=? AND cursor_id=? AND source_id=? AND query_hash=? AND raw_artifact_id=?",
                                 (project, report["cursor_id"], report["source_id"], cursor["query_hash"], raw_a["id"])).fetchall()
        if kind != "X":
            api.require(len(pages) == 1 and pages[0][0:2] == (report["window_from"], report["window_to"])
                        and bool(pages[0][3]) == report["page_complete"], "DB_PAGE_CHAIN", kind)
        if kind == "X":
            api.require(health["exhaustive"] is False and not report.get("next_cursor")
                        and not cursor.get("next_cursor"), "FALSE_WINDOW_COVERAGE", kind)
            public = api.strict_json(raw_bytes)
            api.require(set(public) <= {"url", "items", "empty"} and all(set(x) <= {"url", "published_at", "text", "author"}
                        for x in public.get("items", [])), "X_PUBLIC_ONLY", kind)
            _claim(api, graph, report)
        return report
    finally:
        graph.close()


def _claim(api, graph, report):
    claim = api.obj(report.get("claim_check"), "X disposition")
    artifact, content = graph.artifact(report["project_id"], claim["artifact_ref"])
    doc = api.strict_json(content)
    project = report["project_id"]
    api.require(doc["adoption_authority"] is False and claim["adoption_authority"] is False
                and doc["conclusion"] == claim["conclusion"], "X_ADOPTION", "disposition")
    xref = doc["x_evidence_ref"]
    api.require(claim.get("x_evidence_ref") == xref, "X_SELECTED_ITEM", "reported selected reference")
    for key in ("x_snapshot_ref", "primary_evidence_ref", "primary_snapshot_ref", "primary_url", "primary_commit",
                "primary_locator", "primary_excerpt", "unverified_claims"):
        if key in claim:
            api.require(claim[key] == doc.get(key), "X_PRIMARY", "reported " + key)
    api.require(xref["id"] in {x["evidence_id"] for x in report["items"]}, "X_SELECTED_ITEM", "claim body")
    ev = graph.referenced(project, xref, "Evidence")
    api.require(ev["source_kind"] == "X" and ev["stance"] == "CONTEXT" and ev["verification_status"] == "UNVERIFIED"
                and doc["x_snapshot_ref"] == ev["snapshot_artifact_ref"], "X_SELECTED_ITEM", "unverified original")
    _, xcontent = graph.artifact(project, ev["snapshot_artifact_ref"])
    if doc["conclusion"] == "NOT_CORROBORATED":
        api.text(doc["reason"], "missing primary reason")
        api.require(doc.get("primary_evidence_ref") is None and artifact["source_refs"] == artifact["input_refs"] == [xref], "X_PRIMARY", "uncorroborated")
    else:
        api.require(doc["conclusion"] == "SUPPORTED_NARROW_SCOPE", "X_PRIMARY", "unknown disposition")
        pref = doc["primary_evidence_ref"]
        api.require(claim.get("primary_evidence_ref") == pref, "X_PRIMARY", "reported primary reference")
        primary = graph.referenced(project, pref, "Evidence")
        _, primary_content = graph.artifact(project, doc["primary_snapshot_ref"])
        api.require(primary["source_kind"] == "GITHUB" and primary["snapshot_artifact_ref"] == doc["primary_snapshot_ref"]
                    and primary.get("origin_evidence_id") is None, "X_PRIMARY", "primary identity")
        api.require(b"paperclipai/paperclip" in xcontent.lower() and b"agent management" in xcontent.lower()
                    and doc["primary_excerpt"] == "manage AI agents for work"
                    and doc["primary_excerpt"].casefold() in primary_content.decode("utf-8").casefold(), "X_PRIMARY_BODY", "narrow claim")
        commit = doc["primary_commit"]
        api.require(api.COMMIT.fullmatch(commit) and primary["upstream_revision"] == commit
                    and doc["primary_url"] == primary["canonical_url"]
                    and doc["primary_url"].endswith("/blob/" + commit + "/README.md")
                    and doc["primary_locator"] == "README.md#intro", "X_PRIMARY", "commit/locator")
        api.require(artifact["source_refs"] == artifact["input_refs"] == [xref, pref], "X_PRIMARY", "sealed lineage")
    api.sequence(doc["unverified_claims"], "unverified X claims")


def _h07(api, reader, row, bounds):
    stdout, _ = _invocation(api, reader, row, "INJECTED", bounds)
    locked = reader.read(reader.path("execution/toolchains/locked.json"))["tools"]["go"]
    go = reader.local_tool(locked["path"], locked["sha256"])
    argv = row["actualargv"]
    api.require(len(argv) == 9 and Path(argv[0]).resolve() == go
                and argv[1:] == ["test", "-count=1", "-json", "-run", "^TestW07",
                                  "./adapters/sources", "./internal/domain", "./tests/sources/live"],
                "H07_COMMAND", "actual uncached Go invocation")
    expected_packages = {"researchos.local/research-os/" + name
                         for name in ("adapters/sources", "internal/domain", "tests/sources/live")}
    packages, tests = {}, {}
    streams, passed, failed = {}, set(), set()
    for line in stdout.decode("utf-8").splitlines():
        event = api.strict_json(line)
        key = (event.get("Package"), event.get("Test"))
        package, test = key
        action = event.get("Action")
        api.require(package in expected_packages and action in {"start", "run", "pause", "cont", "output", "pass"},
                    "H07_TEST_RESULTS", "unexpected package or action")
        api.require(bounds[0] <= api.stamp(event.get("Time"), "Go event") <= bounds[1]
                    and "(cached)" not in event.get("Output", ""), "H07_TEST_RESULTS", "time or cached result")
        if not test:
            if action == "start":
                api.require(package not in packages, "H07_TEST_RESULTS", "duplicate package start")
                packages[package] = "running"
            else:
                api.require(packages.get(package) == "running", "H07_TEST_RESULTS", "package lifecycle")
                if action == "pass":
                    api.require(all(state == "passed" for identity, state in tests.items() if identity[0] == package),
                                "H07_TEST_RESULTS", "unfinished tests")
                    packages[package] = "passed"
                else:
                    api.require(action == "output", "H07_TEST_RESULTS", "package action")
        else:
            api.require(packages.get(package) == "running" and test.startswith("TestW07"),
                        "H07_TEST_RESULTS", "test/package identity")
            transitions = {"run": (None, "running"), "pause": ("running", "paused"),
                           "cont": ("paused", "running"), "pass": ("running", "passed")}
            if action in transitions:
                before, after = transitions[action]
                api.require(tests.get(key) == before, "H07_TEST_RESULTS", "test lifecycle")
                tests[key] = after
            else:
                api.require(action == "output" and tests.get(key) in {"running", "paused"},
                            "H07_TEST_RESULTS", "output without running test")
        if event.get("Action") in {"fail", "skip"}:
            failed.add(key)
        if event.get("Action") == "pass" and event.get("Test"):
            passed.add(event["Test"])
        streams[key] = streams.get(key, "") + event.get("Output", "")
    api.require(set(packages) == expected_packages and set(packages.values()) == {"passed"}
                and tests and set(tests.values()) == {"passed"}, "H07_TEST_RESULTS", "incomplete event stream")
    api.require(not failed and passed, "H07_TEST_RESULTS", "zero, failed or skipped test")
    required_tests = {"TestW07HealthH07ProductionFaultMatrix", "TestW07HealthRealCyclePartialProgressAndIndependentSources",
                      "TestW07HealthBoundPartialEffectRemainsConfirmed", "TestW07HealthFailureBeforeCommitStaysUnresolved",
                      "TestW07MissingAuthorizedXChannelDoesNotFetch", "TestW07HealthCASAndUnconfiguredResourceDedup",
                      "TestW07PRDetailStatesAndIndexRejection", "TestW07HealthPartialPrefixNoProviderCursorAndNoFalseComplete"}
    api.require(required_tests <= passed and all(tests.get(("researchos.local/research-os/" +
                    ("adapters/sources" if name == "TestW07PRDetailStatesAndIndexRejection" else "internal/domain"), name)) == "passed"
                    for name in required_tests), "H07_TEST_RESULTS", "production package/test identities")
    typed = []
    for stream in streams.values():
        for line in stream.splitlines():
            if line.startswith("H07_ASSERTION "):
                value = api.strict_json(line[len("H07_ASSERTION "):])
                if value.get("db_snapshot_path"):
                    typed.append(value)
    rows = _document(api, reader, row["assertions_ref"])
    api.require(typed == rows, "H07_RAW_ROWS", "typed output differs from collector")
    ids = [x["id"] for x in rows]
    api.exact_ids(ids, set(FAULTS) | EXTRA_FAULTS, "H07 scenarios")
    snapshots = {str(_ref(api, reader, r)): r for r in api.sequence(row["db_snapshots"], "H07 DB")}
    api.require(len(snapshots) == len(rows), "DB_SNAPSHOT", "independent scenario snapshots")
    for item in rows:
        ident = item["id"]
        api.require(item["measurement_mode"] == "INJECTED" and item["status"] == "PASS", "H07_MODE", ident)
        snapshot = Path(item["db_snapshot_path"])
        api.require(snapshot.is_relative_to(Path(row["cwd"])), "PATH_ESCAPE", ident)
        path = str(reader.path(snapshot.relative_to(Path(row["cwd"])).as_posix(), PREFIX))
        api.require(path in snapshots, "DB_SNAPSHOT", ident)
        graph = Graph(api, reader, snapshots[path], item.get("db_closed_or_vacuum_snapshot"))
        try:
            project, actual, inputs = item["project_id"], item["actual"], item["input"]
            api.require(api.meaningful(inputs) and api.meaningful(actual), "H07_INPUT", ident)
            if ident in FAULTS:
                doc, _ = graph.health(project, actual["health_artifact_ref"], actual["health"])
                h = doc["health"]
                api.require(h["status"] == FAULTS[ident], "H07_MAPPING", ident)
                api.require(h["requested_from"] == inputs["requested_from"] and h["requested_to"] == inputs["requested_to"], "H07_INPUT", ident)
                cursor = graph.object(project, "SourceCursor", actual["cursor"]["id"])
                api.require(cursor == actual["cursor"] and cursor.get("covered_until") is None, "H07_CURSOR", ident)
                api.require(h.get("requested_from") and h.get("requested_to") and h.get("access_scope"), "H07_WINDOW", ident)
                if ident == "timeout":
                    api.require(h["reason"] == "page_timeout" and h["provider_result"] == inputs["page"]["ProviderResult"]
                                == {"exit_code": 0, "status": "ok", "detail_errors": ["page_timeout"]}, "H07_DETAIL_TIMEOUT", ident)
                if ident == "not_configured":
                    api.require(h["reason"] == inputs["page"]["Failure"] == "NOT_CONFIGURED" and h["full_read_count"] == 0, "H07_CONFIGURATION", ident)
                if ident == "429":
                    api.require(h["http_status"] == inputs["page"]["HTTPStatus"] == 429 and h.get("retry_after") == cursor.get("retry_after")
                                and api.stamp(h["retry_after"], "retry") > api.stamp(doc["fetched_at"], "fetched"), "H07_RETRY", ident)
                if ident == "401_or_revoked":
                    api.require(h["http_status"] == inputs["page"]["HTTPStatus"] == 401 and h["reason"] == "AUTH_REVOKED", "H07_AUTH", ident)
                if ident in {"empty_valid_result", "visible_empty", "index_only"}:
                    api.require(h["full_read_count"] == 0, "H07_EMPTY", ident)
                if ident == "empty_valid_result":
                    api.require(h["exhaustive"] is True, "H07_EMPTY", ident)
                if ident == "visible_empty":
                    api.require(h["exhaustive"] is False, "H07_EMPTY", ident)
                if ident.startswith("pr_"):
                    expected = {"pr_open": "OPEN", "pr_closed_unmerged": "CLOSED", "pr_merged": "MERGED"}[ident]
                    state_refs = [r for r in doc["source_refs"] if r["entity_type"] == "Evidence"]
                    api.require(len(state_refs) == 1, "H07_PR", ident)
                    evidence = graph.referenced(project, state_refs[0], "Evidence")
                    _, content = graph.artifact(project, evidence["snapshot_artifact_ref"])
                    payload = api.strict_json(content)
                    _, manifest_bytes = graph.artifact(project, graph.ref(actual["manifest"], "Artifact"))
                    manifest = api.strict_json(manifest_bytes)
                    api.require(payload["state"] == expected and inputs["page"]["Items"][0]["PRState"] == expected
                                and manifest["item_metadata"][0]["pr_state"] == expected, "H07_PR", ident)
            elif ident == "cycle_partial":
                cycle = graph.object(project, "ResearchCycle", actual["cycle"]["id"])
                api.require(cycle == actual["cycle"] and cycle["status"] == "PARTIAL", "H07_CYCLE", ident)
            else:
                effects = graph.db.execute("SELECT body FROM resource_effects WHERE project=? AND effect_key=? ORDER BY sequence DESC LIMIT 1", (project, inputs["effect_key"])).fetchall()
                api.require(len(effects) == 1, "H07_EFFECT", ident)
                effect = api.strict_json(effects[0][0])
                api.require(effect == actual["effect"] and effect["state"] == ("CONFIRMED" if ident == "effect_confirmed" else "UNKNOWN"), "H07_EFFECT", ident)
        finally:
            graph.close()
    return rows


def _compiled_inputs(api, reader, context, proof, source_before, tools, bounds):
    """Reconstruct compilation coverage from recorded Go output and current files."""
    invocation = _document(api, reader, context["compilation_invocation_ref"])
    inventory_interval = api.interval(invocation, "Go inventory")
    api.require(inventory_interval[1] <= bounds[0] and (inventory_interval[1] - inventory_interval[0]).total_seconds() <= 180,
                "INVOCATION_TIME", "bounded dependency preflight before source freeze")
    content, _ = _invocation(api, reader, dict(invocation, measurement_mode="LIVE_SERVICE"), "LIVE_SERVICE",
                              (inventory_interval[0], bounds[1]))
    api.require(invocation["stdout_ref"] == proof["compilation_inputs_ref"], "SOURCE_BUILD", "Go inventory raw")
    argv = invocation["actualargv"]
    api.require(len(argv) == 5 and Path(argv[0]).resolve() == Path(tools["go"]["path"]).resolve()
                and argv[1:] == ["list", "-deps", "-json", "./tests/sources/live"], "SOURCE_BUILD", "Go dependency inventory command")
    cwd = Path(invocation["cwd"])
    api.require(all(Path(row["cwd"]) == cwd for row in proof["source_invocations"] + proof["h07_invocations"])
                and Path(_document(api, reader, proof["build_invocation_ref"])["cwd"]) == cwd,
                "SOURCE_BUILD", "one recorded compilation/capture root")
    raw_text, offset, local, local_directories = content.decode("utf-8"), 0, {}, set()
    referenced_packages = set()
    decoder = json.JSONDecoder()
    while offset < len(raw_text):
        if raw_text[offset].isspace():
            offset += 1
            continue
        try:
            _, end = decoder.raw_decode(raw_text, offset)
        except ValueError as exc:
            raise api.InvalidEvidence("SOURCE_BUILD", "invalid Go JSON stream") from exc
        package = api.obj(api.strict_json(raw_text[offset:end]), "Go package")
        offset = end
        import_path = package.get("ImportPath", "")
        for dependency in package.get("Imports", []) + package.get("Deps", []):
            if dependency.startswith("researchos.local/research-os/"):
                referenced_packages.add(dependency)
        if not import_path.startswith("researchos.local/research-os/"):
            continue
        directory = Path(package["Dir"])
        api.require(directory.is_relative_to(cwd), "PATH_ESCAPE", "compiled local package")
        relative = directory.relative_to(cwd)
        api.require(relative.as_posix() == import_path[len("researchos.local/research-os/"):]
                    and import_path not in local, "SOURCE_COVERAGE", "unique package identity/directory mapping")
        local[import_path] = package
        local_directories.add(relative)
        files = package.get("GoFiles", []) + package.get("CgoFiles", [])
        api.require(files and len(files) == len(set(files)), "SOURCE_COVERAGE", "compiled Go files")
        for name in files:
            api.require(Path(name).name == name and name not in {".", ".."}, "PATH_ESCAPE", "compiled file")
            api.require((relative / name).as_posix() in source_before, "SOURCE_COVERAGE", "missing compiled dependency")
        # Receipt GoFiles cannot choose which existing implementation we read.
        # Conservatively include platform variants; any unresolved dependency
        # stays blocked until an independently reviewed platform qualification.
        current_files = [path.name for path in (reader.repo / relative).glob("*.go") if not path.name.endswith("_test.go")]
        api.require(current_files, "SOURCE_COVERAGE", "current production package sources")
        for name in current_files:
            source_name = (relative / name).as_posix()
            api.require(source_name in source_before, "SOURCE_COVERAGE", "missing compiled dependency")
            current = reader.ref({"path": source_name, "sha256": _digest(source_before[source_name])}).read_bytes().decode("utf-8")
            for directive in re.findall(r"(?m)^//go:embed\s+([^\r\n]+)", current):
                for literal in re.findall(r'"(?:\\.|[^"\\])*"|`[^`]*`|\S+', directive):
                    pattern = json.loads(literal) if literal.startswith('"') else literal[1:-1] if literal.startswith('`') else literal
                    api.require(pattern and not pattern.startswith("all:") and not any(c in pattern for c in "*?[]\\")
                                and not Path(pattern).is_absolute() and not Path(pattern).drive
                                and all(part not in {".", ".."} for part in pattern.split("/")),
                                "SOURCE_COVERAGE", "unqualified embedded input pattern")
                    embedded = (relative / pattern).as_posix()
                    api.require(embedded in source_before, "SOURCE_COVERAGE", "missing embedded compilation input")
                    reader.ref({"path": embedded, "sha256": _digest(source_before[embedded])})
            # Read imports from the pinned Go source, never from receipt code.
            tokens = re.findall(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|`[^`]*`|[A-Za-z_]\w*|[^\s]', current, re.S)
            tokens = [t for t in tokens if not t.startswith(("//", "/*"))]
            for index, token in enumerate(tokens):
                if token != "import":
                    continue
                end = tokens.index(")", index + 1) if tokens[index + 1] == "(" else index + 3
                for literal in tokens[index + 1:end]:
                    if not literal.startswith(('"', '`')):
                        continue
                    try:
                        imported = literal[1:-1] if literal.startswith('`') else json.loads(literal)
                    except ValueError as exc:
                        raise api.InvalidEvidence("SOURCE_COVERAGE", "unsupported import escaping") from exc
                    if imported.startswith("researchos.local/research-os/"):
                        referenced_packages.add(imported)
    api.require({"researchos.local/research-os/" + name for name in
                 ("internal/domain", "internal/store", "adapters/sources", "tests/sources/live")} <= set(local),
                "SOURCE_COVERAGE", "compiled local packages")
    api.require(referenced_packages <= set(local), "SOURCE_COVERAGE", "complete local import/dependency closure")
    required = {"ops/ci/sources.py", "go.mod", "go.sum"}
    for directory in local_directories:
        required.update(path.relative_to(reader.repo).as_posix() for path in (reader.repo / directory).glob("*.go") if path.is_file())
    for pattern in ("adapters/sources/*.go", "internal/domain/*.go", "tests/sources/live/*.go",
                    "tests/sources/check/*.py", "internal/store/*.go", "migrations/sqlite/*.sql", "spec/v2.0/contracts/*"):
        required.update(path.relative_to(reader.repo).as_posix() for path in reader.repo.glob(pattern) if path.is_file())
    api.require(required <= set(source_before), "SOURCE_COVERAGE", "complete current source packages, contracts and migrations")


def product(api, reader, context, tools):
    proof = _document(api, reader, context["proof_ref"])
    api.require(proof.get("schema") == "researchos.w07.product-proof.v1" and proof.get("task_id") == "W07"
                and proof.get("step_id") == "W07-99" and proof.get("mode") == "LIVE_SERVICE"
                and proof.get("executor_id") == context["executor_id"] and proof.get("run_id") == context["run_id"], "PROOF_IDENTITY", "W07")
    bounds = api.interval(proof, "product proof")
    source_before = _document(api, reader, proof["source_before_ref"])
    source_after = _document(api, reader, proof["source_after_ref"])
    api.require(source_before == source_after and source_before, "SOURCE_DRIFT", "capture source")
    source_refs = {x["path"]: x["sha256"] for x in context["version_vector"]["source_files"]}
    input_refs = {x["path"]: x["sha256"] for x in context["version_vector"]["input_files"] + context["version_vector"]["lock_files"]}
    for path, digest in source_before.items():
        api.require(source_refs.get(path, input_refs.get(path)) == _digest(digest), "SOURCE_STALE_VECTOR", path)
    api.require({"internal/domain/sources.go", "adapters/sources/x.go", "internal/store/sqlite.go", "go.mod", "go.sum"}
                <= set(source_before) and any(p.startswith("migrations/sqlite/") for p in source_before)
                and any(p.startswith("spec/v2.0/contracts/") for p in source_before), "SOURCE_COVERAGE", "capture dependencies")
    original_vector = _document(api, reader, proof["version_vector_ref"])
    api.require(original_vector["source"] == source_before, "SOURCE_STALE_VECTOR", "product vector")
    api.require({"go", "browser_act"} <= set(original_vector["tool"]), "TOOL_LOCK", "product execution tools")
    for name, tool in original_vector["tool"].items():
        api.require(name in tools and Path(tool["path"]).resolve() == Path(tools[name]["path"]).resolve()
                    and _digest(tool["sha256"]) == tools[name]["sha256"], "TOOL_LOCK", name)
    _compiled_inputs(api, reader, context, proof, source_before, tools, bounds)
    invocations = api.sequence(proof["source_invocations"], "real source invocations")
    api.exact_ids([r["kind"] for r in invocations], ("GITHUB", "PAPER", "X"), "real sources")
    build = _document(api, reader, proof["build_invocation_ref"])
    _invocation(api, reader, dict(build, measurement_mode="LIVE_SERVICE"), "LIVE_SERVICE", bounds, require_output=False)
    binary_ref = proof["live_binary_ref"]
    _ref(api, reader, binary_ref)
    argv = build["actualargv"]
    api.require(len(argv) == 5 and Path(argv[0]).resolve() == Path(tools["go"]["path"]).resolve()
                and argv[1:3] == ["build", "-o"] and Path(argv[3]) == Path(build["cwd"]) / binary_ref["path"]
                and argv[4] == "./tests/sources/live", "SOURCE_BUILD", "actual pinned binary build")
    reports = {row["kind"]: _source(api, reader, row, bounds, tools, binary_ref) for row in invocations}
    h07 = api.sequence(proof["h07_invocations"], "H07 invocations")
    api.require(len(h07) == 1, "H07_INVOCATIONS", "one full injection matrix")
    _h07(api, reader, h07[0], bounds)
    events = [api.strict_json(line) for line in _bytes(api, reader, h07[0]["stdout_ref"]).decode("utf-8").splitlines()]
    api.require(any(e.get("Action") == "pass" and e.get("Test") == "TestW07HealthPublicIngressCannotForgeCapturedSource"
                    for e in events), "H07_INGRESS_BOUNDARY", "actual production HTTP forgery rejection")
    assertions = api.sequence(proof["assertion_rows"], "A05 rows")
    api.exact_ids([r["id"] for r in assertions], IDS, "A05 assertions")
    baseline = reader.document(context["acceptance_baseline_ref"])
    spec = next(r for r in baseline["cases"] if r["id"] == "A05")
    api.require(spec["mode"] == "LIVE_SERVICE", "MODE", "A05 baseline")
    expected = {row["id"]: row["expected"] for row in spec["assertions"]}
    for row in assertions:
        api.require(row["status"] == "PASS" and row["expected"] == expected[row["id"]] and api.meaningful(row["actual"]), "ASSERTION_RESULT", row["id"])
        for ref in api.sequence(row["raw_evidence_refs"], row["id"]):
            raw(api, reader, ref)
    gates = api.sequence(proof["gate_rows"], "parent gates")
    api.exact_ids([r["id"] for r in gates], GATES, "parent gates")
    api.require(all(row["status"] == "PASS" and api.meaningful(row["actual"]) for row in gates), "GATE_RESULT", "W07")
    return proof, reports


def _dispatches(api, reader, context, pinned, proof):
    rows = api.sequence(context["registered_commands"], "registered W07 commands")
    api.exact_ids([r["id"] for r in rows], (*GATES, "A05"), "command selectors")
    for row in rows:
        ident = row["id"]
        key = "test.sources.fixture" if ident == "W07-G01" else "test.sources.live"
        mode = "FIXTURE" if ident == "W07-G01" else "LIVE_SERVICE"
        receipt = _document(api, reader, row["receipt_ref"])
        api.require(receipt.get("command_key") == key and receipt.get("status") == "PASS"
                    and type(receipt.get("exit_code")) is int and receipt["exit_code"] == 0
                    and type(receipt.get("child_exit_code")) is int and receipt["child_exit_code"] == 0, "COMMAND_EXIT", ident)
        selector_key = "case_id" if ident == "A05" else "check_id"
        expected_selectors = {"task_id": "W07", "case_id": "", "check_id": "", selector_key: ident}
        api.require(receipt["selectors"] == expected_selectors, "COMMAND_BINDING", ident)
        registry_relative = "execution/commands.json" if ident == "W07-G01" else "execution/v2.4/commands.json"
        registry_path = reader.path(registry_relative)
        registry = reader.read(registry_path)
        api.require(receipt["registry_spec"] == ("v2.0" if ident == "W07-G01" else "v2.4")
                    and receipt["registered_command_revision"] == pinned.get(registry_path), "COMMAND_REVISION", ident)
        entry = registry["commands"][key]
        api.require(entry["state"] == "BOUND" and "W07" in entry["selectors"]["task_id"]
                    and ident in entry["selectors"][selector_key], "COMMAND_UNBOUND", ident)
        api.require(receipt["argv"][1:] == entry["argv"] and Path(receipt["cwd"]).resolve() == reader.repo, "DISPATCH_ARGV", ident)
        api.require(api.COMMIT.fullmatch(receipt.get("code_revision", ""))
                    and receipt.get("scope") == "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE", "DISPATCH_SCOPE", ident)
        ids = IDS if ident == "A05" else [ident]
        api.exact_ids(receipt["assertion_ids"], ids, "dispatch assertions")
        api.interval(receipt, ident)
        locked_path = reader.path("execution/toolchains/locked.json")
        api.require(receipt["toolchain_revision"] == pinned.get(locked_path), "DISPATCH_TOOLCHAIN", ident)
        locked = reader.read(locked_path)["tools"][entry["executable_tool"]]
        api.require(Path(receipt["argv"][0]).resolve() == Path(locked["path"]).resolve(), "DISPATCH_EXECUTABLE", ident)
        reader.local_tool(locked["path"], locked["sha256"])
        api.require(pinned.get(reader.path("execution/command_dispatcher/dispatch.py")) == receipt["dispatcher_sha256"], "DISPATCHER_CHANGED", ident)
        for reference in api.sequence(receipt.get("input_versions"), "dispatcher input versions"):
            api.require(pinned.get(reader.ref(reference)) == reference["sha256"], "DISPATCH_INPUT_UNPINNED", ident)
        # Dispatcher output belongs to a canonical invocation namespace, not
        # to W07 raw source evidence. Never load code from either namespace.
        for name in ("stdout", "stderr"):
            ref = receipt[name]
            expected_path = "execution/invocations/" + receipt["invocation_id"] + "/" + name + ".txt"
            api.require(ref["path"] == expected_path, "DISPATCH_RAW_IDENTITY", ident)
            reader.ref(ref, "execution/invocations/")
        output = reader.document(receipt["stdout"])
        api.require(output.get("status") == "PASS" and output.get("task_id") == "W07"
                    and output.get("scope", output.get("mode")) == mode and output.get(selector_key) == ident,
                    "COMMAND_OUTPUT", ident)
        api.exact_ids(output.get("assertion_ids"), ids, "dispatch raw assertions")
        api.require(type(output.get("assertions")) is int and output["assertions"] == len(ids), "COUNT", ident)
        output_ref = output.get("product_proof_ref")
        if ident == "W07-G01" and not _same_ref(api, output_ref, context["proof_ref"]):
            fixture_proof = _document(api, reader, output_ref)
            api.require(fixture_proof.get("mode") == "FIXTURE" and fixture_proof.get("task_id") == "W07"
                        and _document(api, reader, fixture_proof["source_before_ref"]) == _document(api, reader, proof["source_before_ref"])
                        == _document(api, reader, fixture_proof["source_after_ref"]), "DISPATCH_EXECUTION_LINK", ident)
            fixture_rows = api.sequence(fixture_proof["h07_invocations"], "fixture invocations")
            api.require(len(fixture_rows) == 1, "H07_INVOCATIONS", ident)
            _h07(api, reader, fixture_rows[0], api.interval(fixture_proof, "fixture proof"))
        else:
            api.require(_same_ref(api, output_ref, context["proof_ref"]), "DISPATCH_EXECUTION_LINK", ident)


def _global(api, reader, context, proof, review_path):
    """The frozen GLOBAL_EVIDENCE_V1 files remain explicit and independently read."""
    refs = api.fields(context.get("global_evidence_refs"),
                      ("run_receipt", "version_manifest", "command_receipt", "assertion_results"), label="A05 GLOBAL files")
    paths = [_ref(api, reader, ref) for ref in refs.values()]
    api.require(len(set(paths)) == 4 and review_path not in paths, "DUPLICATE_REFERENCE", "GLOBAL files")
    run, manifest, command, assertions = [reader.read(path) for path in paths]
    api.fields(run, ("schema", "case_id", "run_id", "environment_mode", "os", "arch", "timezone",
                     "started_at", "ended_at", "executor_id", "verifier_id"), label="run receipt")
    api.require(run["schema"] == "researchos.w07.run-receipt.v1" and run["case_id"] == "A05"
                and run["run_id"] == context["run_id"] and run["environment_mode"] == "LIVE_SERVICE"
                and run["executor_id"] == context["executor_id"]
                and run["verifier_id"] == reader.read(review_path)["reviewer_id"], "RUN_IDENTITY", "A05")
    api.require({k: run[k] for k in ("os", "arch", "timezone")} == context["version_vector"]["environment"], "ENVIRONMENT", "A05")
    api.require(api.interval(run, "run receipt") == api.interval(proof, "actual proof"), "INVOCATION_TIME", "A05")
    api.fields(manifest, ("schema", "case_id", "run_id", "package_version", "package_manifest_ref", "code_revision",
                          "dirty", "version_vector_ref", "product_version_vector_ref"), label="version manifest")
    api.require(manifest["schema"] == "researchos.w07.version-manifest.v1" and manifest["case_id"] == "A05"
                and manifest["run_id"] == context["run_id"] and manifest["package_version"] == "2.4.0"
                and manifest["package_manifest_ref"]["sha256"] == "4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964",
                "MANIFEST_IDENTITY", "A05")
    package = reader.ref(manifest["package_manifest_ref"])
    api.require(package.name == "PACKAGE_MANIFEST.json" and any(r == manifest["package_manifest_ref"] for r in context["version_vector"]["spec_files"]),
                "VECTOR_BASELINE", "package manifest")
    api.require(api.COMMIT.fullmatch(manifest["code_revision"]) and type(manifest["dirty"]) is bool, "CODE_REVISION", "A05")
    execution_report = _document(api, reader, context["execution_report_ref"])
    api.require(_same_ref(api, execution_report.get("product_proof_ref"), context["proof_ref"])
                and execution_report.get("execution_head") == manifest["code_revision"]
                and bool(execution_report.get("dirty_before")) == manifest["dirty"], "CODE_REVISION", "actual capture commit/dirty")
    api.require(_document(api, reader, manifest["version_vector_ref"]) == context["version_vector"]
                and manifest["product_version_vector_ref"] == proof["version_vector_ref"], "STALE_VECTOR", "A05")
    api.fields(command, ("schema", "case_id", "run_id", "registered_commands", "source_invocations", "h07_invocations", "build_invocation_ref"), label="command receipt")
    api.require(command["schema"] == "researchos.w07.command-receipt.v1" and command["case_id"] == "A05"
                and command["run_id"] == context["run_id"] and command["registered_commands"] == context["registered_commands"]
                and command["source_invocations"] == proof["source_invocations"] and command["h07_invocations"] == proof["h07_invocations"]
                and command["build_invocation_ref"] == proof["build_invocation_ref"], "COMMAND_IDENTITY", "A05")
    api.fields(assertions, ("schema", "case_id", "run_id", "assertions"), label="assertion results")
    api.require(assertions["schema"] == "researchos.w07.assertion-results.v1" and assertions["case_id"] == "A05"
                and assertions["run_id"] == context["run_id"], "ASSERTION_IDENTITY", "A05")
    rows = api.sequence(assertions["assertions"], "A05 GLOBAL assertions")
    api.exact_ids([r["id"] for r in rows], IDS, "A05 GLOBAL assertions")
    originals = {r["id"]: r for r in proof["assertion_rows"]}
    for row in rows:
        api.fields(row, ("id", "expected", "actual", "status", "raw_evidence_refs", "refusal_evidence_refs", "command_keys"), label="A05 assertion")
        api.require(all(row[k] == originals[row["id"]][k] for k in ("expected", "actual", "status", "raw_evidence_refs")), "ASSERTION_RESULT", row["id"])
        api.exact_ids(row["command_keys"], ["test.sources.live"], "A05 command keys")
        for ref in api.sequence(row["refusal_evidence_refs"], "negative source receipts"):
            raw(api, reader, ref)


def _independent(api, reader, owner, context_path, review_path, issuance_path, context):
    review, issuance = reader.read(review_path), reader.read(issuance_path)
    api.require(review.get("schema") == SCHEMAS["review"] and issuance.get("schema") == SCHEMAS["issuance"], "SCHEMA", "W07 review/issuance")
    executor, reviewer = context["executor_id"], api.text(review.get("reviewer_id"), "reviewer")
    api.require(len({executor.casefold(), reviewer.casefold(), "codex:/root"}) == 3 and review.get("executor_id") == executor
                and issuance.get("actor") == "codex:/root" and issuance.get("reviewer_id") == reviewer
                and issuance.get("executor_id") == executor, "INDEPENDENT_ACTOR", "review boundary")
    for doc in (review, issuance):
        api.require(doc.get("task_id") == "W07" and doc.get("step_id") == "W07-99"
                    and doc.get("run_id") == context["run_id"], "REVIEW_IDENTITY", "W07")
        api.require(reader.ref(doc["context_ref"], PREFIX) == context_path, "REVIEW_CONTEXT", "W07")
    api.require(_ref(api, reader, issuance["review_ref"]) == review_path
                and review.get("proof_ref") == context["proof_ref"] and not review.get("supersedes_review_refs"), "REVIEW_PROOF", "W07")
    api.require(review.get("acceptance_baseline_ref") == context["acceptance_baseline_ref"]
                and review.get("evidence_index_ref") == review.get("context_ref"), "REVIEW_BASELINE", "GLOBAL acceptance receipt")
    api.require(review.get("decision") == "ACCEPTED" and review.get("missing") == [] and review.get("failed") == [], "REVIEW_VERDICT", "W07")
    for key, ids in (("assertion_verdicts", IDS), ("gate_verdicts", GATES)):
        rows = api.sequence(review.get(key), key)
        api.exact_ids([r["id"] for r in rows], ids, key)
        api.require(all(r.get("status") == "PASS" and api.meaningful(r.get("actual")) and r.get("raw_evidence_refs") for r in rows), "REVIEW_VERDICT", key)
        for row in rows:
            for ref in row["raw_evidence_refs"]:
                raw(api, reader, ref)
    api.require(review.get("version_vector") == context["version_vector"], "REVIEW_CONTEXT", "reviewed exact inputs")
    message = _document(api, reader, issuance["delivery_ref"])
    api.require(message.get("schema") == "researchos.root-received-independent-message.v1"
                and message.get("recorded_by") == "codex:/root" and message.get("recipient") == "codex:/root"
                and message.get("sender") == reviewer and message.get("event_type") in {"MESSAGE", "FINAL_ANSWER"}
                and message.get("review_ref") == issuance["review_ref"], "ROOT_OBSERVED_DELIVERY", "actual independent message")
    content = api.text(message.get("content"), "received independent content")
    api.require(issuance["review_ref"]["sha256"] in content and context["proof_ref"]["sha256"] in content,
                "ROOT_OBSERVED_DELIVERY", "review and proof hashes in received message")
    proof = _document(api, reader, context["proof_ref"])
    api.require(api.stamp(proof["ended_at"], "execution ended") <= api.stamp(context["created_at"], "current context")
                <= api.stamp(review["issued_at"], "review") <= api.stamp(message["received_at"], "received")
                <= api.stamp(issuance["observed_at"], "observed") <= api.stamp(owner.get("accepted_at"), "accepted"),
                "REGISTERED_TIME_ORDER", "W07")


def verify_owner(api, reader, owner, roots, plan_path):
    api.require(owner.get("status") == "ACCEPTED", "OWNER_NOT_ACCEPTED", "W07-99")
    context = reader.read(roots["context"])
    api.require(context.get("schema") == SCHEMAS["context"] and context.get("task_id") == "W07"
                and context.get("step_id") == "W07-99", "SCHEMA", "W07 context")
    api.text(context.get("executor_id"), "executor")
    api.text(context.get("run_id"), "run id")
    api.require(reader.ref(context["acceptance_baseline_ref"]).name == "acceptance.json"
                and context["acceptance_baseline_ref"]["sha256"] == api.FROZEN_HASHES["acceptance.json"], "FROZEN_BASELINE", "W07")
    pinned, tools = _vector(api, reader, context)
    plan = reader.read(Path(plan_path).resolve(strict=True))
    step = next(s for s in plan["steps"] if s["id"] == "W07-99")
    state = reader.read(reader.path("execution/v2.4/step_state.json"))
    statuses = {r["id"]: r["status"] for r in state["steps"]}
    api.require(all(statuses.get(k) == "ACCEPTED" for k in step["dependencies"]), "DEPENDENCY", "W07")
    proof, _ = product(api, reader, context, tools)
    _dispatches(api, reader, context, pinned, proof)
    _global(api, reader, context, proof, roots["review"])
    _independent(api, reader, owner, roots["context"], roots["review"], roots["issuance"], context)
    reader.finish()
    return context
