from pathlib import Path
import hashlib,json,difflib,ast
O=Path(__file__).resolve().parent
def pin(p,raw=None):
 b=p.read_bytes() if raw is None else raw
 return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,obj):
 with (O/name).open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode())
r=json.loads((O/"review.json").read_bytes());newp=Path(r["source_ref"]["path"])
oldp=newp.parent.parent/"actual-cli-bootstrap-ef1d9bf73bea42d8972dfb12c6774093/bootstrap_actual_cli.py"
old=oldp.read_bytes();new=newp.read_bytes()
assert hashlib.sha256(old).hexdigest()==r["base_source_sha256"]
assert hashlib.sha256(new).hexdigest()==r["source_ref"]["sha256"] and len(new)==r["source_ref"]["bytes"]
a,b=ast.parse(old),ast.parse(new)
fixed=lambda t:ast.dump(next(n.value for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=="FIXED" for x in n.targets)),include_attributes=False)
assert fixed(a)==fixed(b)
(O/"base-source.snapshot.py").write_bytes(old);(O/"v2-source.snapshot.py").write_bytes(new)
(O/"source.delta.diff").write_bytes("".join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile=str(oldp),tofile=str(newp))).encode())
save("delta-integrity.json",dict(base_source_ref=pin(oldp,old),new_source_ref=pin(newp,new),fixed_9_refs_AST_unchanged=True,candidate_execution=False))
(O/"HANDOFF.md").write_text("BLOCKED_SOURCE_DELTA：仅3项最小修正。\n\nR01：跨进程Static正文应采用有界WM_GETTEXT，不能依赖GetWindowTextW。\nR02：ctypes两级枚举回调必须内部捕获异常并让外层拒绝部分枚举结果。\nR03：发布confirmed前核对init workspace_ref对应的实际Host根目录等于目标workspace；预选意图和关窗不等于实际binding证明。\n\n其余pointer-free BM_CLICK、发送完成/消息结果区分、Host身份与同父保留方向成立。固定9refs AST与旧版本相同，复用旧Source及714清理证据；未运行Native/GUI/provider，未改Root/canonical，未新增测试或工具错误。独立回执封包后STOP。\n",encoding="utf-8")
save("manifest.json",dict(schema="researchos.source-delta-review-manifest.v1",members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json")],excluded=["manifest.json","handoff.json"]))
save("handoff.json",dict(schema="researchos.actual-cli-bootstrap-source-delta-review-handoff.v1",actor_id=r["actor_id"],decision=r["decision"],source_ref=r["source_ref"],review_ref=pin(O/"review.json"),manifest_ref=pin(O/"manifest.json"),delta_integrity_ref=pin(O/"delta-integrity.json"),original_tool_io_ref=pin(O/"original-tool-io.json"),handoff_markdown_ref=pin(O/"HANDOFF.md"),blocking_findings=3,new_tool_errors=0,native_executions=0,gui_operations=0,provider_requests=0,canonical_writes=0,formal_acceptance=False,stop_all_review_namespace_writes=True))
print(json.dumps(dict(review=pin(O/"review.json"),manifest=pin(O/"manifest.json"),handoff=pin(O/"handoff.json"),decision=r["decision"],stop=True),ensure_ascii=False))

