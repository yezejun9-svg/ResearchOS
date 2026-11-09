"""Narrow unsealed Source refinement: preserve refusal order and require actual settlement."""
import difflib,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
target=P/"candidate-root/internal/domain/client_protocol.go"
code=target.read_text(encoding="utf-8")
start=code.index('\tcase "session.attach":',code.index("func (s *ClientService) handleWrite("))
end=code.index('\tcase "session.control":',start)
before=code[start:end];after=before
policy='''		if s.Host.LeaseTTL <= 0 {
			return nil, fmt.Errorf("HOST_LEASE_POLICY_MISSING")
		}
'''
assert after.count(policy)==1
after=after.replace(policy,"",1)
needle='\t\t\tif parseErr == nil && nowT.Before(until) {\n'
after=after.replace(needle,needle+'''				if s.Host.LeaseTTL <= 0 {
					return nil, fmt.Errorf("HOST_LEASE_POLICY_MISSING")
				}
''',1)
needle='\t\t// Writer attribution moves with the epoch inside this same transaction, so the old\n'
after=after.replace(needle,'''		nowT = time.Now().UTC()
		if s.Host.LeaseTTL <= 0 {
			// A handoff must publish a real writer lease; the TTL comes from host config,
			// and the service refuses to invent one.
			return nil, fmt.Errorf("HOST_LEASE_POLICY_MISSING")
		}
'''+needle,1)
assert after.count("status, settled, err := runState")==1
after=after.replace("status, settled, err := runState","_, settled, err := runState",1)
assert after.count("if liveRunStatuses[status] && !settled {")==1
after=after.replace("if liveRunStatuses[status] && !settled {","if !settled {",1)
changes=json.loads((P/"production-replacements.json").read_bytes())
changes.append({"position":start,"before":before,"after":after})
updated=code[:start]+after+code[end:]
original=Path(json.loads((P/"static-evidence.json").read_bytes())["production_baseline_ref"]["path"]).read_bytes()
inverse=updated
for c in reversed(changes):
 p=c["position"];assert inverse[p:p+len(c["after"])]==c["after"]
 inverse=inverse[:p]+c["before"]+inverse[p+len(c["after"]):]
assert inverse.encode()==original
target.write_bytes(updated.encode())
(P/"production-replacements.json").write_text(json.dumps(changes,ensure_ascii=True,indent=2)+"\n",encoding="utf-8",newline="\n")
(P/"client-protocol-attach.patch").write_text("".join(difflib.unified_diff(original.decode().splitlines(True),updated.splitlines(True),fromfile="T6/internal/domain/client_protocol.go",tofile="candidate-root/internal/domain/client_protocol.go")),encoding="utf-8",newline="\n")
e=json.loads((P/"static-evidence.json").read_bytes())
e["production_candidate_ref"]={"path":str(target),"sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"bytes":len(target.read_bytes())}
e["all_original_production_bytes_recovered_by_inverse"]=True
e["existing_settlement_rejection_and_transfer_journal_preserved"]=False
e["settlement_gate_strengthened_to_reject_unconfirmed_children_or_queue_even_for_terminal_run"]=True
e["old_transfer_host_policy_validation_order_preserved"]=True
e["transfer_journal_body_unchanged"]=True
(P/"static-evidence.json").write_text(json.dumps(e,ensure_ascii=True,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"production":e["production_candidate_ref"],"inverse_raw_equal":True},ensure_ascii=True))

