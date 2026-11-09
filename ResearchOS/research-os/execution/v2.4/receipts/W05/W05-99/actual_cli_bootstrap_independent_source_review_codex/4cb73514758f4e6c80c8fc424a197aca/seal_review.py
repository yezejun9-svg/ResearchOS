from pathlib import Path
import hashlib,json,ast
O=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
def pin(p,raw=None):
    raw=p.read_bytes() if raw is None else raw
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,obj):
    with (O/name).open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8"))
report=json.loads((O/"review.json").read_bytes())
root_source=Path(report["producer_source_ref"]["path"])
raw=root_source.read_bytes()
actual=pin(root_source,raw)
assert actual["sha256"]==report["producer_source_ref"]["sha256"] and actual["bytes"]==report["producer_source_ref"]["bytes"]
ast.parse(raw)
paths=[root_source]+[Path(x["path"]) for x in report["fixed_inputs_preflight"] if Path(x["path"]).suffix==".py"]
paths += [R/x for x in ("apps/control/main.go","apps/control/discovery.go","apps/cli/cli_stream.go","apps/cli/cli_stream_test.go","apps/cli/cli_native.go","apps/cli/cli_contract.go","migrations/sqlite/0011_resources.sql")]
snapshots=[]
for p in paths:
    b=p.read_bytes()
    dest=O/"input-snapshots"/p.relative_to(R)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("xb") as f:f.write(b)
    snapshots.append(dict(source_ref=pin(p,b),snapshot_path=str(dest.relative_to(O))))
save("input-snapshots.json",dict(schema="researchos.narrow-review-input-snapshots.v1",inputs=snapshots,binary_pins_without_duplicate_snapshot=report["fixed_inputs_preflight"]))
(O/"HANDOFF.md").write_text("独立结论：READY_SOURCE_ONLY。\n\n范围仅为 exact bootstrap producer 及固定 helper/v9 draft transition。没有发现阻止正常 zero-provider CLI init + goal --draft 的 API/schema/Job lifecycle 错误；9个固定pin匹配，当前CP346及web index前提满足。Host无runtime coordinator配置，CLI草稿分支不启动Task/Run；清理未确认会保留同一父进程和句柄。\n\n未执行producer、Native、WinAPI或provider，未改Root/canonical，也未新增测试。真实bootstrap结果仍由Root实际调用产生；本回执不代表qualification/formal acceptance。全部审查文件封包后STOP。\n",encoding="utf-8")
save("manifest.json",dict(schema="researchos.narrow-independent-source-review-manifest.v1",actor_id="codex:/root/w05_merge_review",members=[pin(p) for p in sorted(O.rglob("*")) if p.is_file() and p not in {O/"manifest.json",O/"handoff.json"}],excluded=["manifest.json","handoff.json"]))
save("handoff.json",dict(schema="researchos.actual-cli-bootstrap-independent-source-review-handoff.v1",decision="READY_SOURCE_ONLY",actor_id="codex:/root/w05_merge_review",producer_source_ref=actual,review_ref=pin(O/"review.json"),manifest_ref=pin(O/"manifest.json"),input_snapshots_ref=pin(O/"input-snapshots.json"),original_tool_io_ref=pin(O/"original-tool-io.json"),handoff_markdown_ref=pin(O/"HANDOFF.md"),blocking_findings=0,fixed_pins_matched=9,new_review_errors=0,candidate_executions=0,native_calls=0,provider_calls=0,canonical_mutations=0,runtime_qualification=False,formal_acceptance=False,execution_grant_issued=False,stop_all_review_namespace_writes=True))
print(json.dumps(dict(review=pin(O/"review.json"),manifest=pin(O/"manifest.json"),handoff=pin(O/"handoff.json"),decision="READY_SOURCE_ONLY",stop=True),ensure_ascii=False))

