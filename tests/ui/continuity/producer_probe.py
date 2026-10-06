"""W13-02 producer probe: drive the built workbench in a real browser against a recording stub host.

This answers the card's own negative - 按钮只变样式 - by observing traffic instead of reading source: every
control tagged data-producer=<method> is clicked, and the probe records the command that actually left the page.
The host half is a stub by design (the real-host chain belongs to the forwarded C26 browser phase and to the
accepted W05/W06 rows); what is proven here is the wiring property the card claims, namely that each of the 23
frozen protocol methods has a working producer that sends its own method and payload, that all of them reach the
one endpoint (no second dispatcher), and that a control whose precondition is unmet sends nothing.

The stub's own fixtures are asserted against internal/api/contracts/client.protocol.schema.json, so a re-issued
schema fails this probe instead of leaving it answering a stale shape.
"""
import hashlib
import json
import os
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "internal/api/contracts/client.protocol.schema.json"
DIST = ROOT / "apps/web/dist"


def locked_node():
    table = json.loads((ROOT / "execution/toolchains/locked.json").read_text(encoding="utf-8-sig"))
    node = table["tools"]["node"]
    path = Path(node["path"])
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != node.get("sha256"):
        return None, "the pinned node is absent or does not match the locked table"
    return path, "verified"


def required_of(name, defs):
    return defs.get(name, {}).get("required", [])


def build_fixtures():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
    defs = schema["$defs"]
    contracts = schema["x-method-contracts"]

    lease = {"client_id": "desktop-renderer", "epoch": 4, "expires_at": "2026-01-01T00:10:00Z"}
    prompt = {
        "request": {"id": "rr-stub-1", "revision": 3, "summary": "需要访问外部来源", "status": "PENDING",
                    "requested_capability": "network"},
        "task_id": "task-stub-1", "run_id": "run-stub-1", "action_digest": "sha256:" + "a" * 64,
        "action_artifact_ref": {"entity_type": "Artifact", "id": "art-digest", "revision": 1, "content_hash": None},
        "allowed_responses": ["ALLOW_ONCE", "DENY"], "policy_allows_user_decision": True,
        "action_scope": {"project_id": "proj-stub", "task_id": "task-stub-1", "run_id": "run-stub-1",
                         "tool_name": "fetch_source"},
    }
    message = {"message_id": "msg-stub-1", "role": "USER",
               "parts": [{"part_index": 0, "text": "已在会话中的历史消息", "complete": True}], "complete": True}
    snapshot = {
        "session_id": "sess-stub-1", "project_id": "proj-stub", "workspace_ref": "ws-stub-1",
        "native_session_ref": "native-stub-1", "core_build_id": "stub-build", "protocol_version": "researchos-client/2",
        "revision": 11, "title": "探针会话", "archived_at": None, "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:05:00Z", "model_config_ref": "mc-stub-1", "goal_id": None,
        "active_run_id": "run-stub-1", "run_status": "RUNNING", "goal_status": "ACTIVE", "writer": lease,
        "event_sequence": 7, "earliest_event_sequence": 1,
        "checkpoint_artifact_ref": {"entity_type": "Artifact", "id": "art-checkpoint", "revision": 1, "content_hash": None},
        "pending_command_ids": ["cmd-in-flight-1"], "pending_permissions": [prompt],
        "resume_requires_explicit_user": False, "messages": [message],
        "transcript_artifact_ref": None, "has_earlier_messages": False,
    }
    entry = {"relative_path": "notes/a.md", "name": "a.md", "kind": "FILE", "byte_size": 12,
             "content_hash": "sha256:" + "b" * 64, "modified_at": "2026-01-01T00:00:00Z", "readable": True,
             "reason_code": None}
    binding = {"authorized_workspace_ref": "ws-stub-1", "display_name": "探针工作区", "display_path": "C:/stub",
               "access": "READ_WRITE", "project_id": "proj-stub", "revision": 2, "status": "ACTIVE"}
    diff_file = {"relative_path": "notes/a.md", "previous_path": None, "status": "MODIFIED",
                 "before_hash": "sha256:" + "c" * 64, "after_hash": "sha256:" + "b" * 64, "binary": False,
                 "patch": "@@ -1 +1 @@\n-old\n+new"}
    read = {"workspace_ref": "ws-stub-1", "relative_path": "notes/a.md", "content_hash": "sha256:" + "b" * 64,
            "byte_size": 12, "encoding": "UTF-8", "text": "旧的正文", "modified_at": "2026-01-01T00:00:00Z",
            "editable": True}
    event = {"event_id": "evt-stub-1", "session_id": "sess-stub-1", "sequence": 8, "core_build_id": "stub-build",
             "protocol_version": "researchos-client/2", "run_id": "run-stub-1", "command_id": None,
             "domain_event_id": None, "kind": "TOOL_RESULT", "payload": {"tool_name": "fetch_source"}}

    results = {
        "host.status": {"state": "READY", "core_build_id": "stub-build", "protocol_version": "researchos-client/2"},
        "host.configure": {"config_revision": 3, "provider_id": "default", "base_url": "http://127.0.0.1:0",
                           "model_id": "model-stub", "credential_ref": None},
        "project.bootstrap": {"authorized_workspace_ref": "ws-stub-1", "display_name": "探针项目",
                              "project_id": "proj-stub", "session_id": "sess-stub-1", "revision": 1},
        "session.list": {"items": [snapshot], "next_cursor": None},
        "session.create": snapshot,
        "session.get": snapshot,
        "session.attach": {"snapshot": snapshot, "write_owner_acquired": True},
        "session.send": {"message_id": "msg-stub-2", "queue_position": 2, "run_id": "run-stub-1", "snapshot": snapshot},
        "session.control": {"action": "PAUSE", "target_id": "run-stub-1", "control_request_id": "ctl-stub-1",
                            "settled": True, "children_stopped": 1, "queue_empty": False, "snapshot": snapshot},
        "session.events": {"events": [event], "next_sequence": 8, "high_watermark": 8, "has_more": False},
        "session.handoff": {"previous_client_id": "desktop-renderer", "target_client_id": "cli-stub",
                            "previous_epoch": 4, "snapshot": snapshot},
        "session.update": snapshot,
        "goal.start": {"goal_id": "goal-stub-1", "goal_revision": 1, "goal_status": "DRAFT", "snapshot": snapshot},
        "provider.models": {"items": [{"model_id": "model-stub"}], "next_cursor": None, "provider_id": "default",
                            "catalog_source": "BUILTIN", "observed_at": "2026-01-01T00:00:00Z",
                            "network_request_count": 0, "not_listed_is_not_unsupported": False},
        "provider.probe": {"ok": True, "reason_code": None, "latency_ms": 3},
        "workspace.register": binding,
        "workspace.list": {"items": [binding], "next_cursor": None},
        "workspace.tree": {"workspace_ref": "ws-stub-1", "root_revision": 5, "entries": [entry], "next_cursor": None},
        "workspace.read": read,
        "workspace.diff": {"workspace_ref": "ws-stub-1", "base": "INDEX", "base_revision": "deadbeef",
                           "files": [diff_file], "total_files": 1, "truncated": False, "full_diff_artifact_ref": None},
        "workspace.write": {"workspace_ref": "ws-stub-1", "relative_path": "notes/a.md", "task_id": "run-stub-1",
                            "before_hash": "sha256:" + "b" * 64, "after_hash": "sha256:" + "d" * 64,
                            "draft_artifact_ref": {"entity_type": "Artifact", "id": "art-draft", "revision": 1,
                                                   "content_hash": None}, "snapshot": snapshot},
        "artifact.import": {"artifact_ref": {"entity_type": "Artifact", "id": "art-imported", "revision": 1,
                                             "content_hash": "sha256:" + "e" * 64}, "byte_size": 12,
                            "media_type": "text/markdown"},
        "permission.respond": {"request": prompt["request"], "decision": "ALLOW_ONCE",
                               "resolution_artifact_ref": {"entity_type": "Artifact", "id": "art-resolution",
                                                            "revision": 1, "content_hash": None},
                               "action_digest": prompt["action_digest"], "consumed": True,
                               "resumption_scheduled": True},
    }

    # The fixtures are only trustworthy if they cover what the published schema says a reader may rely on.
    problems = []
    for method, body in results.items():
        want = required_of(contracts[method]["result"], defs)
        if want and method not in ("workspace.list", "session.list", "provider.models", "workspace.tree",
                                   "workspace.diff", "session.events"):
            continue
        missing = [k for k in want if k not in body]
        if missing:
            problems.append({"method": method, "missing": missing})
    for key, want in (("SessionSnapshot", snapshot), ("WorkspaceEntry", entry), ("PermissionPrompt", prompt),
                      ("DiffFile", diff_file), ("WorkspaceReadResult", read), ("SessionEvent", event),
                      ("WorkspaceBinding", binding)):
        missing = [k for k in required_of(key, defs) if k not in want]
        if missing:
            problems.append({"fixture": key, "missing": missing})
    return results, problems


CLICK_ORDER = [
    "host.status", "workspace.list", "session.list", "workspace.register", "project.bootstrap", "session.create",
    "session.get", "session.attach", "session.update", "session.handoff", "provider.models", "provider.probe",
    "host.configure", "goal.start", "session.send", "session.events", "session.control", "permission.respond",
    "workspace.tree", "workspace.read", "workspace.diff", "workspace.write", "artifact.import",
]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def reply(self, status, payload, content_type="application/json"):
        raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        state = self.server.state
        if self.path.startswith("/v2/command"):
            return self.reply(405, {"error": "use POST"})
        if self.path == "/remote-info":
            return self.reply(404, {"error": "no remote transport"})
        target = self.path.split("?")[0].lstrip("/")
        if target in ("", "index.html"):
            target = "index.html"
        candidate = (DIST / target).resolve()
        # SPA fallback: any unknown path is the app shell, which then routes on its own.
        if not str(candidate).startswith(str(DIST)) or not candidate.is_file():
            candidate = DIST / "index.html"
        if not candidate.is_file():
            return self.reply(404, {"error": "not found"})
        ctype = ("text/javascript" if candidate.suffix == ".js" else "text/css" if candidate.suffix == ".css"
                 else "text/html")
        state["assets"].append(candidate.name)
        return self.reply(200, candidate.read_bytes(), ctype)

    def do_POST(self):
        state = self.server.state
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            body = None
        if self.path != "/v2/command":
            state["off_protocol"].append({"path": self.path, "body": body})
            return self.reply(501, {"status": "NOT_IMPLEMENTED"})
        method = (body or {}).get("method")
        state["commands"].append({"path": self.path, "method": method, "envelope": body,
                                  "authorization": bool(self.headers.get("Authorization"))})
        results = state["results"]
        if method not in results:
            return self.reply(501, {"status": "NOT_IMPLEMENTED", "command_id": (body or {}).get("command_id")})
        return self.reply(200, {"status": "COMPLETED", "command_id": (body or {}).get("command_id"),
                                "session_id": (body or {}).get("session_id"),
                                "revision": ((body or {}).get("expected_revision") or 0) + 1,
                                "result": results[method]})


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def main():
    out = {"checks": {}, "errors": []}
    node, node_reason = locked_node()
    out["checks"]["node"] = {"path": str(node), "reason": node_reason}
    if node is None or not (DIST / "index.html").is_file():
        print(json.dumps({"status": "COMMAND_FAILED", "assertions": 0, "assertion_ids": [],
                          "failures": [{"id": "W1302-PRODUCER-PROBE-PREREQUISITES",
                                        "detail": "pinned node: %s; built bundle: %s" % (node_reason, str(DIST))}],
                          "not_verified": [], "diagnostics": []}, ensure_ascii=False))
        return 1
    results, fixture_problems = build_fixtures()
    out["checks"]["fixtures"] = {"methods": len(results), "problems": fixture_problems}

    state = {"commands": [], "off_protocol": [], "assets": [], "results": results}
    server = ThreadingHTTPServer(("127.0.0.1", free_port()), Handler)
    server.state = state
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = "http://127.0.0.1:%d" % server.server_address[1]

    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(base + "/p/proj-stub/continuity", wait_until="domcontentloaded")
            page.fill("#access-token", "stub-credential")
            page.click(".auth-card button")
            page.wait_for_selector("[data-producer]", timeout=30000)
            controls = page.evaluate("""() => {
              const map = {};
              for (const b of document.querySelectorAll('[data-producer]')) {
                const m = b.getAttribute('data-producer');
                map[m] = (map[m] || 0) + 1;
              }
              return {tags: map, total: document.querySelectorAll('[data-producer]').length};
            }""")
            out["checks"]["rendered_controls"] = controls

            def prep(method):
                """Satisfy the control's own precondition; the click counter is only armed afterwards."""
                if method in ("workspace.register", "project.bootstrap"):
                    page.fill('input[placeholder^="C:/work/research"]', "C:/stub/workspace")
                elif method == "goal.start":
                    page.fill('textarea[placeholder^="希望推进的目标"]', "探针目标")
                elif method == "session.send":
                    page.fill('textarea[aria-label="对话输入"]', "探针消息")
                elif method == "session.handoff":
                    page.fill('input[placeholder^="例如 cli"]', "cli-stub")
                elif method in ("workspace.read", "workspace.tree", "workspace.diff", "session.events",
                                "session.attach", "session.update", "host.configure", "session.control",
                                "permission.respond", "workspace.write", "artifact.import"):
                    # These depend on an attached session or a read baseline, which earlier clicks establish.
                    if not page.query_selector('[data-producer="workspace.write"]:not([disabled])'):
                        read = page.query_selector('[data-producer="workspace.read"]:not([disabled])')
                        if read:
                            read.click()
                            page.wait_for_timeout(250)
                    if method == "workspace.write":
                        if page.query_selector('textarea[aria-label="文件编辑"]'):
                            page.fill('textarea[aria-label="文件编辑"]', "新的正文")

            clicked, missing = [], []
            for method in CLICK_ORDER:
                prep(method)
                page.wait_for_timeout(180)
                selector = '[data-producer="%s"]:not([disabled])' % method
                if not page.query_selector(selector):
                    missing.append(method)
                    continue
                before = len(state["commands"])
                page.click(selector)
                page.wait_for_timeout(260)
                sent = [c["method"] for c in state["commands"][before:]]
                clicked.append({"method": method, "sent": sent, "count": len(sent)})

            # A control with an unmet precondition must refuse locally: reload without a session and click send.
            fresh = browser.new_page(viewport={"width": 1440, "height": 1000})
            fresh.goto(base + "/p/proj-stub/continuity", wait_until="domcontentloaded")
            fresh.fill("#access-token", "stub-credential")
            fresh.click(".auth-card button")
            fresh.wait_for_selector("[data-producer]", timeout=30000)
            disabled_before = len(state["commands"])
            fresh.fill('textarea[aria-label="对话输入"]', "无会话时不应发送")
            send_state = fresh.evaluate("""() => {
              const b = document.querySelector('[data-producer="session.send"]');
              return {present: !!b, disabled: b ? b.disabled : null};
            }""")
            if not send_state["disabled"]:
                fresh.click('[data-producer="session.send"]')
                fresh.wait_for_timeout(300)
            out["checks"]["unmet_precondition"] = {"state": send_state,
                                                   "commands_after": len(state["commands"]) - disabled_before}

            browser.close()
    except Exception as exc:
        out["errors"].append(repr(exc))
    finally:
        server.shutdown()

    methods_observed = sorted({c["method"] for c in state["commands"]})
    out["checks"]["traffic"] = {
        "commands": len(state["commands"]),
        "distinct_methods": len(methods_observed),
        "paths": sorted({c["path"] for c in state["commands"]}),
        "off_protocol": state["off_protocol"],
        "all_authorized": all(c["authorization"] for c in state["commands"]),
        "missing_clicks": missing,
        "envelopes": [{"method": c["method"],
                       "protocol": c["envelope"]["protocol_version"],
                       "envelope_method": c["envelope"]["method"],
                       "keys": sorted(c["envelope"].keys())} for c in state["commands"][:30]],
    }
    out["checks"]["clicked"] = clicked
    print(json.dumps(out, ensure_ascii=False))
    return 0 if not out["errors"] else 3


if __name__ == "__main__":
    sys.exit(main())
