"""Independent probe: does each product.contract verb do the operation it names?

Runs the real CLI against a fake host that logs every request path it receives,
then reports which local_operations from contracts/product.contract.json were
actually exercised. Written by the reviewer; scratch only, not evidence of a pass.
"""
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

REPO = r"D:\作品集\ResearchOS\research-os"
BIN = os.path.join(REPO, ".local", "rev", "ros_probe.exe")
WORK = os.path.join(REPO, ".local", "rev", "probe 工作区")
DISC = os.path.join(REPO, ".local", "rev", "probe_discovery.json")

hits = []


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        hits.append(("GET", self.path))
        body = b'{"state":"READY","protocol":"researchos-client/2"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        hits.append(("POST", self.path))
        body = b'{"state":"ACCEPTED"}'
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def run(args, cwd=REPO):
    env = dict(os.environ)
    env["RESEARCHOS_CLI_DISCOVERY"] = DISC
    env["RESEARCHOS_CLI_CONFIG"] = os.path.join(REPO, ".local", "rev", "probe_config.json")
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([BIN] + args, cwd=cwd, capture_output=True, env=env,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr


def main():
    os.makedirs(WORK, exist_ok=True)
    srv = HTTPServer(("127.0.0.1", 0), H)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with open(DISC, "w", encoding="utf-8") as f:
        json.dump({"url": "http://127.0.0.1:%d" % port, "pid": 1,
                   "data_dir": "x", "started_at": "now"}, f)

    report = {}
    verbs = [["status"], ["cancel", "goal-77"], ["goal", "do the thing"],
             ["go"], ["resume", "sess-42"], ["resume", "--session", "sess-42"],
             ["/cancel"], ["/goal", "text"]]
    for v in verbs:
        hits.clear()
        rc, so, se = run(v)
        lines = [l for l in so.replace("\r\n", "\n").split("\n") if l.strip()]
        rec = json.loads(lines[0]) if lines and lines[0].lstrip().startswith("{") else {}
        report[" ".join(v)] = {"exit": rc, "n_stdout_lines": len(lines),
                               "status": rec.get("status"),
                               "host_paths_hit": list(hits),
                               "stdout_head": (so or "")[:220]}

    # product.contract declared syntaxes (positional arguments)
    syntax = {
        "init <path>": ["init", WORK],
        "run <prompt> --project <id> --output jsonl": ["run", "hello", "--project", "p1", "--output", "jsonl"],
        "resume <session-id>": ["resume", "sess-42"],
        "cancel <run-or-goal-id>": ["cancel", "goal-77"],
        "goal <text>": ["goal", "do the thing"],
        "doctor": ["doctor"],
        "config": ["config"],
        "interactive (bare)": [],
        "interactive (--project)": ["--project", "p1"],
    }
    smap = {}
    for name, argv in syntax.items():
        rc, so, se = run(argv)
        lines = [l for l in so.replace("\r\n", "\n").split("\n") if l.strip()]
        rec = json.loads(lines[0]) if lines and lines[0].lstrip().startswith("{") else {}
        smap[name] = {"exit": rc, "reason": rec.get("reason"), "status": rec.get("status"),
                      "stdout_lines": len(lines), "stderr_head": (se or "")[:160]}
    report["_contract_syntax"] = smap

    # doctor against a host that answers 503 (the product.contract exit-code vocabulary has no 4)
    bad = HTTPServer(("127.0.0.1", 0), type("Bad", (BaseHTTPRequestHandler,), {
        "do_GET": lambda s: (s.send_response(503), s.send_header("Content-Length", "2"),
                             s.end_headers(), s.wfile.write(b"no"))[0],
        "log_message": lambda *a: None}))
    bport = bad.server_address[1]
    threading.Thread(target=bad.serve_forever, daemon=True).start()
    with open(DISC, "w", encoding="utf-8") as f:
        json.dump({"url": "http://127.0.0.1:%d" % bport, "pid": 1, "data_dir": "x",
                   "started_at": "now"}, f)
    rc, so, se = run(["doctor"])
    report["_doctor_503"] = {"exit": rc, "stdout": so[:300], "stderr": se[:200]}
    bad.shutdown()

    rc, so, se = run(["version"])
    report["_version"] = {"exit": rc, "stdout": so[:200], "stderr": se[:200]}

    srv.shutdown()
    with open(os.path.join(REPO, ".local", "rev", "probe_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("WROTE probe_report.json", file=sys.stderr)


if __name__ == "__main__":
    main()
