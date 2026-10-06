"""Which registry keys are not BOUND, and what each one would actually take to bind.

The v2.4 dispatcher refuses every key whose state is not BOUND with NOT_IMPLEMENTED and exit 3, so those keys are
not "untested" - they cannot produce evidence at all until someone binds a real handler. That makes this a
gate-level list: the CLI/Desktop deliverables and much of the 30-case selector debt sit behind it.

For each non-bound key the table records what can be established statically, and what cannot be established
without a decision:
  - owner_card, and whether that card is ACCEPTED in step_state (a not-started owner means nobody has agreed to
    bind it yet);
  - whether the argv the entry names resolves to a real file, a real directory with a manifest, or nothing;
  - whether the executable_tool is present in execution/toolchains/locked.json, because the dispatcher launches
    tools from the pinned table and an unpinned tool cannot be run at all;
  - a readiness verdict that is deliberately coarse: BINDABLE (handler exists and the tool is pinned),
    NEEDS_HANDLER (the named path does not exist or would not run), NEEDS_OWNER (the owning card is not accepted),
    NEEDS_TOOL (the tool is not in the locked table).

Read-only: it executes nothing, so it is safe while an independent review holds the tree.
"""
import io, json, os

NL = chr(10)


def _find_repo(start):
    d = start
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "execution", "v2.4")) and os.path.isdir(os.path.join(d, "internal", "domain")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("repository root not found from %s" % start)


REPO = _find_repo(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
V24 = "execution/v2.4"


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


reg = load(os.path.join(V24, "commands.json"))
st = load(os.path.join(V24, "step_state.json"))
locked = load(os.path.join(V24, "..", "execution", "toolchains", "locked.json")) if False else load(
    os.path.join("execution", "toolchains", "locked.json"))
recs = st["steps"] if isinstance(st["steps"], list) else list(st["steps"].values())
status = {r.get("id"): r.get("status") for r in recs if isinstance(r, dict) and r.get("id")}
tools = set((locked.get("tools") or {}).keys())

rows = []
for key, entry in sorted((reg.get("commands") or {}).items()):
    if entry.get("state") == "BOUND":
        continue
    owner = str(entry.get("owner_card") or "")
    owner_card = owner.split(" ")[0] if owner else ""
    owner_status = status.get(owner_card, "not_started" if owner_card else "no_owner_recorded")
    argv = entry.get("argv") or []
    cwd = entry.get("cwd") or "."
    first = argv[0] if argv else ""
    target = os.path.normpath(os.path.join(cwd if cwd != "." else "", first)) if first else ""
    exists_file = bool(first) and os.path.isfile(target)
    exists_dir = bool(first) and os.path.isdir(target)
    manifest = bool(exists_dir) and os.path.isfile(os.path.join(target, "package.json"))
    tool = entry.get("executable_tool") or ""
    tool_pinned = tool in tools
    if not owner_card:
        readiness = "NEEDS_OWNER"
    elif owner_status != "ACCEPTED":
        readiness = "NEEDS_OWNER"
    elif not tool_pinned:
        readiness = "NEEDS_TOOL"
    elif not (exists_file or exists_dir):
        readiness = "NEEDS_HANDLER"
    else:
        readiness = "BINDABLE"
    rows.append({"key": key, "state": entry.get("state"), "owner_card": owner, "owner_status": owner_status,
                 "argv": argv, "cwd": cwd, "executable_tool": tool, "tool_in_locked_table": tool_pinned,
                 "argv_first_resolves_to": (target if (exists_file or exists_dir) else None),
                 "resolves_as_file": exists_file, "resolves_as_directory": exists_dir,
                 "directory_has_package_manifest": manifest,
                 "platforms": entry.get("platforms"), "timeout_seconds": entry.get("timeout_seconds"),
                 "readiness": readiness,
                 "note": (entry.get("note") or "")[:200]})

rows.sort(key=lambda r: (r["readiness"], r["key"]))
summary = {"record": "non-bound v2.4 registry keys and what each one needs before it can produce evidence",
           "generated_by": "execution/v2.4/registry_binding_readiness.py (read-only; nothing executed)",
           "registry_revision": reg.get("revision"),
           "bound_keys": sum(1 for e in (reg.get("commands") or {}).values() if e.get("state") == "BOUND"),
           "non_bound_keys": len(rows),
           "readiness_counts": {k: sum(1 for r in rows if r["readiness"] == k) for k in
                                sorted({r["readiness"] for r in rows})},
           "tools_in_locked_table": sorted(tools),
           "meaning": "NOT_IMPLEMENTED on these keys is not an untested path, it is an unbindable one: the "
                      "dispatcher refuses any entry whose state is not BOUND, so no card work can produce "
                      "evidence through them until a real handler is bound with a pinned tool",
           "keys": rows}
io.open(os.path.join(V24, "registry_binding_readiness.json"), "w", encoding="utf-8", newline=NL).write(
    json.dumps(summary, indent=1, ensure_ascii=False))
print(json.dumps({k: summary[k] for k in ("registry_revision", "bound_keys", "non_bound_keys",
                                          "readiness_counts", "tools_in_locked_table")}, indent=1, ensure_ascii=False))
for r in rows:
    print("%-26s %-12s owner=%-14s tool=%-8s pinned=%s argv=%s"
          % (r["key"], r["readiness"], r["owner_status"], r["executable_tool"], r["tool_in_locked_table"],
             " ".join(r["argv"])[:40]))
