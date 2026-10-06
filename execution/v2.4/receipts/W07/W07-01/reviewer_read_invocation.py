"""Reviewer helper: read a dispatcher invocation's own stdout.txt, pull the check report out of it,
and print the fields that settle a claim. Read-only."""
import io
import json
import os
import sys

REPO = r"D:/作品集/ResearchOS/research-os"


def report_of(invocation_id):
    d = os.path.join(REPO, "execution", "invocations", invocation_id)
    receipt = json.loads(io.open(os.path.join(d, "receipt.json"), encoding="utf-8-sig").read())
    text = io.open(os.path.join(d, "stdout.txt"), encoding="utf-8", errors="replace").read()
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith("{")]
    rep = json.loads(lines[-1]) if lines else None
    err = io.open(os.path.join(d, "stderr.txt"), encoding="utf-8", errors="replace").read()
    return receipt, rep, err


def main():
    inv = sys.argv[1]
    receipt, rep, err = report_of(inv)
    out = {
        "invocation_id": inv,
        "dispatch_status": receipt.get("status"),
        "exit_code": receipt.get("exit_code"),
        "child_exit_code": receipt.get("child_exit_code"),
        "argv": receipt.get("argv"),
        "selectors": receipt.get("selectors"),
        "registered_command_revision": receipt.get("registered_command_revision"),
        "code_revision": receipt.get("code_revision"),
        "input_versions": receipt.get("input_versions"),
        "started_at": receipt.get("started_at"),
        "ended_at": receipt.get("ended_at"),
        "report": rep,
        "stderr_tail": (err or "")[-400:],
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
