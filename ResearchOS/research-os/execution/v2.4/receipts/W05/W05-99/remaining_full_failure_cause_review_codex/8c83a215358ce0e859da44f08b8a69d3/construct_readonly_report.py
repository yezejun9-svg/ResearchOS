import sys
sys.dont_write_bytecode = True
import collections
import difflib
import hashlib
import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent
SPEC = json.loads((OUT / "cause-specs.json").read_text(encoding="utf-8"))
T3 = Path(SPEC["SourceRootT3"])
MAIN = Path(SPEC["Main"])
FULL = Path(SPEC["full_receipt_root"])

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def write_json(name, obj):
    with (OUT / name).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")

def write_text(name, text):
    with (OUT / name).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)

closed_ref = pin(FULL / "validation.closed.json")
assert closed_ref["sha256"] == "0ce4a6303446250249c5d8b2344e2ca3d298b3f2ac5618b71f5404976f40df34" and closed_ref["bytes"] == 236066
closed = json.loads((FULL / "validation.closed.json").read_text(encoding="utf-8"))
raw_ref = pin(FULL / "full-domain-and-native-authority-offline.stdout.raw")
assert raw_ref["sha256"] == "b4d15819134bd1d16c976828022c76aad741859967bbf0a3617986b0ca0308ae" and raw_ref["bytes"] == 2661892
compiler = json.loads((FULL / "actual-full-test-compiler-input-inventory.json").read_text(encoding="utf-8"))
compiler_ref = pin(FULL / "actual-full-test-compiler-input-inventory.json")
assert compiler_ref == closed["compiled_input_inventory_ref"]
compiled_refs = {}
for item in compiler["product_inventory"] + compiler["build_inputs"] + compiler["actual_embed_files"]:
    if isinstance(item, dict) and {"path", "sha256", "bytes"}.issubset(item):
        compiled_refs[str(Path(item["path"])).casefold()] = item

source_paths = sorted(set(SPEC["extra_source_refs"]) | {entry[0] for cause in SPEC["causes"] for entry in cause["evidence"]})
sources = {}
diffs = []
for rel in source_paths:
    t3_path, main_path = T3 / rel, MAIN / rel
    current = pin(t3_path)
    counterpart = pin(main_path) if main_path.is_file() else None
    actual = compiled_refs.get(str(t3_path).casefold())
    same_actual = actual is not None and all(current[k] == actual[k] for k in ["path", "sha256", "bytes"])
    sources[rel] = {"T3": current, "Main": counterpart, "byte_equal": counterpart is not None and current["sha256"] == counterpart["sha256"] and current["bytes"] == counterpart["bytes"], "actual_compiler_inventory_ref": actual, "matches_actual_compiler_inventory": same_actual}
    if counterpart is not None and not sources[rel]["byte_equal"]:
        diffs.append("".join(difflib.unified_diff(main_path.read_text(encoding="utf-8").splitlines(keepends=True), t3_path.read_text(encoding="utf-8").splitlines(keepends=True), fromfile="Main/" + rel, tofile="T3/" + rel)))
write_json("source-pins.json", sources)
write_text("Main-to-T3-deltas.patch", "\n".join(diffs))

outputs = collections.defaultdict(list)
terminal = []
for line_no, line in enumerate((FULL / "full-domain-and-native-authority-offline.stdout.raw").read_text(encoding="utf-8").splitlines(), 1):
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue
    test = event.get("Test")
    if test and event.get("Action") == "output":
        outputs[test].append({"raw_line": line_no, "output": event.get("Output", "").rstrip("\r\n")})
    if test and event.get("Action") in ["pass", "fail", "skip"]:
        terminal.append({"raw_line": line_no, **event})
counts = dict(collections.Counter(event["Action"] for event in terminal))
assert counts == {"pass": 1261, "fail": 25, "skip": 4}
excluded_names = set(SPEC["excluded_previously_diagnosed_failed_nodes"])
all_failed = [event for event in terminal if event["Action"] == "fail"]
remaining = [event for event in all_failed if event["Test"] not in excluded_names]
assert len(remaining) == 21
parent_nodes = [event["Test"] for event in remaining if any(other["Test"].startswith(event["Test"] + "/") for other in remaining)]
leaf_nodes = [event["Test"] for event in remaining if event["Test"] not in parent_nodes]
assert len(parent_nodes) == 4 and len(leaf_nodes) == 17
listed = [node for cause in SPEC["causes"] for node in cause["nodes"]]
assert len(listed) == len(set(listed)) == 21 and set(listed) == {event["Test"] for event in remaining}
remaining_events = []
for event in remaining:
    name = event["Test"]
    remaining_events.append({
        "test": name, "raw_terminal_line": event["raw_line"],
        "parent_repeat": name in parent_nodes,
        "failed_children": [other["Test"] for other in remaining if other["Test"].startswith(name + "/")],
        "failure_outputs": [entry for entry in outputs[name] if re.search(r"[.]go:\d+:", entry["output"])],
    })
skips = []
for event in terminal:
    if event["Action"] == "skip":
        skips.append({"test": event["Test"], "raw_terminal_line": event["raw_line"], "acceptance": "NOT_ACCEPTED", "outputs": outputs[event["Test"]][-2:]})
skip_gates = {
    "TestControlCurrentActualOwnerNoGain": {"variable": "W16_CURRENT_NATIVE", "required": "1", "source": "internal/domain/evolution_control_current_native_test.go", "line": 131, "recovery": "Root bounded current-control native harness with its actual owner/resource bindings and independent review; setting env alone is not acceptance."},
    "TestControlCurrentPreservedPreparation": {"variable": "W16_CURRENT_OFFLINE_WORK", "required": "explicit preserved diagnostic directory", "source": "internal/domain/evolution_control_current_offline_test.go", "line": 24, "recovery": "Root separately reviewed preserved setup-only diagnostic; it never grants qualified owner/evaluation or native acceptance."},
    "TestW06ContextContinuation": {"variable": "RESEARCHOS_C01_MODEL", "required": "1", "source": "internal/domain/orchestration_context_test.go", "line": 11, "recovery": "Root real model C01/G02 runner with approved resource wiring and closed actual evidence."},
    "TestW05Live": {"variable": "RESEARCHOS_RUNTIME_LIVE", "required": "1", "source": "internal/domain/runtime_test.go", "line": 277, "recovery": "Root separately authorized live executable/provider/resource harness. This report does not run it."},
}
for event in skips:
    event["gate"] = skip_gates[event["test"]]

inventory = {}
for label, root in [("Main", MAIN), ("T3", T3)]:
    files = sorted((root / "migrations/sqlite").glob("[0-9][0-9][0-9][0-9]_*.sql"))
    inventory[label] = {"root": str(root), "numbered_count": len(files), "files": [pin(path) for path in files]}
assert inventory["Main"]["numbered_count"] == 23 and inventory["T3"]["numbered_count"] == 24

causes = []
for original in SPEC["causes"]:
    cause = dict(original)
    refs = []
    for rel, start, stop in original["evidence"]:
        lines = (T3 / rel).read_text(encoding="utf-8").splitlines()
        refs.append({"source_file": rel, "path": str(T3 / rel), "start_line": start, "end_line": min(stop, len(lines)), "source_pin": sources[rel]["T3"], "Main_byte_equal": sources[rel]["byte_equal"], "matches_actual_compiler_inventory": sources[rel]["matches_actual_compiler_inventory"], "lines": [{"line": n, "text": lines[n - 1]} for n in range(start, min(stop, len(lines)) + 1)]})
    cause["evidence"] = refs
    cause["node_count"] = len(cause["nodes"])
    cause["leaf_count"] = len([name for name in cause["nodes"] if name in leaf_nodes])
    cause["acceptance"] = "NOT_ACCEPTED"
    causes.append(cause)

input_names = [
    "validation.closed.json",
    "full-domain-and-native-authority-offline.stdout.raw",
    "full-domain-and-native-authority-offline.stderr.raw",
    "full-domain-and-native-authority-offline.invocation.json",
    "actual-full-test-compiler-input-inventory.json",
    "failure-origin.796.json",
    "original-tool-io.json",
]
inputs = {name: pin(FULL / name) for name in input_names}
limitations = [
    "Read-only diagnosis of closed Root actual receipts and public Source/contract text; no Source construction or code mutation.",
    "Main has not been executed by this agent; Main attribution is based on exact bytes and focused deltas, not a claimed Main runtime result.",
    "No cause classification grants acceptance or removes an original failed node. All25 fail and all4 skip remain in the original closed result.",
    "No proof of schema24-introduced production regression is established by these17 remaining leaves; existing legacy creation/first-turn compatibility and error ordering remain explicit decisions.",
    "No Go/SQL/native/Git/provider execution; no private key/credential, original database or product holdout reads. Public Source and closed receipt metadata were read.",
    "No failure counter is reset and no existing sealed Source package is modified.",
]
data = {
    "schema": "researchos.remaining-full-failure-causes-readonly.v1",
    "status": "READONLY_DIAGNOSIS_COMPLETE_PENDING_ROOT_DECISION",
    "authority": "NONE", "formal_acceptance": False,
    "input_refs": inputs,
    "closed_state": {key: closed.get(key) for key in ["status", "current_source_root", "all_owned_jobs_closed", "native_authority_positive", "external_model_provider_requests", "production_db_writes", "Main_adopted", "main_canonical_unchanged", "formal_acceptance"]},
    "observed_test_counts": counts, "observed_terminal_count": len(terminal),
    "excluded_previously_diagnosed_failed_nodes": sorted(excluded_names),
    "remaining_failed_node_count": 21, "remaining_leaf_failed_node_count": 17,
    "parent_repeat_count": 4, "parent_repeat_nodes": parent_nodes,
    "remaining_failed_nodes": remaining_events,
    "cause_count": len(causes), "causes": causes,
    "skipped_nodes": skips,
    "source_pins_ref": pin(OUT / "source-pins.json"),
    "source_pair_count": len(sources),
    "source_Main_byte_equal_count": sum(entry["byte_equal"] for entry in sources.values()),
    "source_Main_diff_count": sum(not entry["byte_equal"] for entry in sources.values()),
    "source_actual_compiler_match_count": sum(entry["matches_actual_compiler_inventory"] for entry in sources.values()),
    "Main_to_T3_delta_ref": pin(OUT / "Main-to-T3-deltas.patch"),
    "numbered_SQL_inventory": inventory,
    "author_actual_execution": {"python_metadata_readonly_receipt_writes": True, "Go": False, "SQL": False, "native": False, "Git": False, "provider": False, "private_resources": False, "original_database": False, "product_holdout": False, "Source_Main_T3_canonical_writes": False},
    "new_failure_origins": [pin(OUT / "failure-origin.801.json")], "failure_counter_reset": False,
    "limitations": limitations,
}
write_json("report.json", data)

def source_link(rel, line):
    return "[" + rel + ":" + str(line) + "](" + str(T3 / rel).replace("\\", "/") + ":" + str(line) + ")"

md = [
    "# FULL 其余失败节点只读分类",
    "",
    "状态 READONLY_DIAGNOSIS_COMPLETE_PENDING_ROOT_DECISION；authority NONE；不构成接受。",
    "",
    "已关闭 FULL 共1290个测试终态：1261 pass、25 fail、4 skip。扣除已单独处理三当前fixture对应的4个failed事件，本报告精确覆盖21个事件：17个失败叶节点及4个父重复。它们归入8个原因组。原25 fail与4 skip保持原样，不因分类而减计数。",
    "",
    "这17叶尚不能建立schema24新增生产回归：相关旧测试与模型来源代码同Main；三生产文件差异仅inventory最大23→24、Service添加prepared authority字段及upgradeLocal添加24计划dispatch，未改此次拒绝条件。但Main未在本任务执行，因此这只是源码归因，且fresh legacy创建成功/首轮拒绝及lease错误顺序保留为Root待决策，不能据此声明无产品bug。",
    "",
    "闭合输入 validation.closed.json SHA256 " + closed_ref["sha256"] + " / " + str(closed_ref["bytes"]) + " bytes；raw SHA256 " + raw_ref["sha256"] + " / " + str(raw_ref["bytes"]) + " bytes。report.json保留21事件的原始失败输出、terminal raw行、Source/合同证据全文行与精确pins；source-pins.json同时标明Main和实际compiler inventory匹配。",
    "",
    "| 原因组 | failed事件/真实叶 | 分类 |",
    "|---|---:|---|",
]
for cause in causes:
    md.append("| " + cause["id"] + " | " + str(cause["node_count"]) + "/" + str(cause["leaf_count"]) + " | " + cause["classification"] + " |")
md += ["", "父重复仅为 " + "、".join("`" + name + "`" for name in parent_nodes) + "。", ""]
for cause in causes:
    md += ["## " + cause["id"], "", cause["finding"], "", cause["novelty"], "", "恢复条件：" + cause["recovery"], "", "最低待决策Source范围：" + "；".join(cause["minimal_source_scope"]) + "。", "", "对应事件：" + "、".join("`" + name + "`" for name in cause["nodes"]) + "。", "", "证据：" + "；".join(source_link(ref["source_file"], ref["start_line"]) for ref in cause["evidence"]) + "。", ""]
    if cause["open_question"]:
        md += ["未关闭：" + cause["open_question"], ""]
md += [
    "## 四个显式skip",
    "",
    "全部为NOT_ACCEPTED；只打开环境变量不能代替真实资源、执行及独立审查。",
    "",
    "| 用例 | 未打开的入口 | 恢复边界 |",
    "|---|---|---|",
]
for item in skips:
    gate = item["gate"]
    md.append("| `" + item["test"] + "` | `" + gate["variable"] + "`: " + gate["required"] + " | " + gate["recovery"] + " " + source_link(gate["source"], gate["line"]) + " |")
md += ["", "## Source归因与边界", "", "共" + str(len(sources)) + "个参与证据的Source/contract配对：" + str(sum(v["byte_equal"] for v in sources.values())) + "个Main字节相同、" + str(sum(not v["byte_equal"] for v in sources.values())) + "个有差异。逐文件SHA/bytes及actual compiler出处见source-pins.json，完整差异见Main-to-T3-deltas.patch。Main编号库存23份、T3为24份；都不是W16要求的20份。", ""]
md += ["- " + item for item in limitations]
md.append("")
write_text("report.md", "\n".join(md))
print(json.dumps({"namespace": str(OUT), "remaining_failed_nodes": len(remaining), "leaf_nodes": len(leaf_nodes), "parent_repeats": len(parent_nodes), "causes": len(causes), "skip_NOT_ACCEPTED": len(skips), "source_pair_count": len(sources), "Main_byte_equal": sum(v["byte_equal"] for v in sources.values()), "Main_diff": sum(not v["byte_equal"] for v in sources.values()), "compiler_matches": sum(v["matches_actual_compiler_inventory"] for v in sources.values()), "authority": "NONE", "report": pin(OUT / "report.json"), "report_md": pin(OUT / "report.md"), "source_pins": pin(OUT / "source-pins.json")}, ensure_ascii=False))

