"""Reviewer measurement: prove that the W07-01 append to execution/v2.4/commands.json changed exactly one key
and left every other key's PARSED value byte-identical, and record the current argv semantics."""
import json
import subprocess
import sys

REPO = r"D:/作品集/ResearchOS/research-os"
BIND = "4ed2714a"          # the commit that applied the binding + repair
KEY = "test.sources.live"


def blob(rev):
    out = subprocess.run(["git", "-C", REPO, "show", "%s:execution/v2.4/commands.json" % rev],
                         capture_output=True, check=True).stdout
    return json.loads(out.decode("utf-8-sig"))


def main():
    before = blob(BIND + "^")
    after = blob(BIND)
    head = blob("HEAD")

    def keys(d):
        return list(d["commands"].keys())

    result = {
        "before_key_count": len(before["commands"]),
        "after_key_count": len(after["commands"]),
        "head_key_count": len(head["commands"]),
        "append_only_in_order": keys(after) == keys(before) + [KEY],
        "head_order_matches_after": keys(head) == keys(after),
        "added_keys": sorted(set(after["commands"]) - set(before["commands"])),
        "removed_keys": sorted(set(before["commands"]) - set(after["commands"])),
    }
    changed = []
    for k in before["commands"]:
        if json.dumps(before["commands"][k], sort_keys=True) != json.dumps(after["commands"][k], sort_keys=True):
            changed.append(k)
    result["pre_existing_keys_whose_parsed_value_changed"] = changed

    # the same comparison against the CURRENT registry, so a later concurrent write is visible too
    changed_now = []
    for k in before["commands"]:
        if k not in head["commands"]:
            changed_now.append(k + " (REMOVED since the binding)")
        elif json.dumps(before["commands"][k], sort_keys=True) != json.dumps(head["commands"][k], sort_keys=True):
            changed_now.append(k)
    result["pre_existing_keys_changed_in_head_vs_binding"] = changed_now
    result["head_keys_not_in_before"] = sorted(set(head["commands"]) - set(before["commands"]))

    cur = head["commands"][KEY]
    argv = cur["argv"]
    script_elems = [a for a in argv if a.endswith(".py") or a.endswith(".go") or a.endswith(".js")]
    result["current_argv"] = argv
    result["current_argv_script_element_count"] = len(script_elems)
    result["current_argv_scripts"] = script_elems
    result["current_argv_equals_intended_single_script"] = argv == ["-X", "utf8", "tests/sources/check/main.py"]
    result["any_backslash_in_argv"] = any("\\" in a for a in argv)
    result["current_selectors"] = cur["selectors"]
    result["state"] = cur["state"]
    result["registry_revision_at_binding"] = after.get("revision")
    result["registry_revision_at_head"] = head.get("revision")
    # does any OTHER key also claim task W07 / check W07-01 / case A05?
    clash = {}
    for k, v in head["commands"].items():
        s = v.get("selectors") or {}
        if k == KEY:
            continue
        if ("W07" in (s.get("task_id") or [])) or ("W07-01" in (s.get("check_id") or [])) \
           or ("A05" in (s.get("case_id") or [])):
            clash[k] = s
    result["other_keys_claiming_w07_rows"] = clash

    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
