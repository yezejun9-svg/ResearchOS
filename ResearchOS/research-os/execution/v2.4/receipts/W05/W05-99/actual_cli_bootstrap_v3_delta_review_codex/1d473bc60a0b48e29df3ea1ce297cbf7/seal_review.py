from pathlib import Path
import hashlib,json,ast,difflib
O=Path(__file__).resolve().parent
def pin(p,raw=None):
 b=p.read_bytes() if raw is None else raw
 return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,v):
 with (O/name).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode())
r=json.loads((O/"review.json").read_bytes());n=Path(r["source_ref"]["path"])
o=n.parent.parent/"actual-cli-bootstrap-v2-d873bd7f77ab4d0a927d93c28a636dac/bootstrap_actual_cli.v2.py"
a=o.read_bytes();b=n.read_bytes()
assert hashlib.sha256(a).hexdigest()==r["base_source_sha256"]
assert hashlib.sha256(b).hexdigest()==r["source_ref"]["sha256"] and len(b)==r["source_ref"]["bytes"]
fixed=lambda raw:ast.dump(next(x.value for x in ast.parse(raw).body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="FIXED" for t in x.targets)),include_attributes=False)
assert fixed(a)==fixed(b)
(O/"v2-source.snapshot.py").write_bytes(a);(O/"v3-source.snapshot.py").write_bytes(b)
(O/"source.delta.diff").write_bytes("".join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile=str(o),tofile=str(n))).encode())
contract=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_trusted_qualification_host_source_revision_codex/797a5659dec64d55a16915d1aea6e46c/prepare.go")
c=contract.read_bytes();(O/"prepare.contract.snapshot.go").write_bytes(c)
save("delta-integrity.json",dict(base_source_ref=pin(o,a),new_source_ref=pin(n,b),contract_ref=pin(contract,c),fixed_9_pins_AST_unchanged=True,candidate_execution=False))
(O/"HANDOFF.md").write_text("READY_SOURCE_DELTA：BOOT-V2-R01/R02/R03均已在v3闭合。\n\nWM_GETTEXT使用有界系统消息；两级ctypes回调内部记录错误并拒绝部分结果；真实只读WorkspaceBinding的唯一性/project/ref/ACTIVE/real_path检查通过后才发布picker确认。查询与既有trusted Host prepare.go61–65一致。\n\n复用固定9pins和旧714 cleanup证据，没有Native/GUI/provider/canonical执行或新增测试。本轮只读路径错误718完整原始IO单独封存：outer0/Python/native NULL，未抹去诊断。此次只签Source增量，不声明bootstrap实际成功、qualification或formal acceptance。封包后STOP。\n",encoding="utf-8")
save("manifest.json",dict(schema="researchos.source-delta-review-manifest.v1",members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json")],excluded=["manifest.json","handoff.json"]))
save("handoff.json",dict(schema="researchos.actual-cli-bootstrap-source-delta-review-handoff.v1",actor_id=r["actor_id"],decision=r["decision"],source_ref=r["source_ref"],review_ref=pin(O/"review.json"),manifest_ref=pin(O/"manifest.json"),delta_integrity_ref=pin(O/"delta-integrity.json"),original_tool_io_ref=pin(O/"original-tool-io.json"),failure718_origin_ref=pin(O/"failure-origin.718.json"),closed_finding_ids=[x["id"] for x in r["closures"]],remaining_findings=0,native_calls=0,gui_operations=0,provider_requests=0,canonical_writes=0,runtime_qualification=False,formal_acceptance=False,stop_all_review_namespace_writes=True))
print(json.dumps(dict(review=pin(O/"review.json"),manifest=pin(O/"manifest.json"),handoff=pin(O/"handoff.json"),failure718=pin(O/"failure-origin.718.json"),decision=r["decision"],stop=True),ensure_ascii=False))

