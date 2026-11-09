"""Prepare new immutable r330 staging source from actual r329 controller, pure IO/AST only."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,ast
ROOT=Path(r"D:\作品集\ResearchOS\research-os")
OUT=Path(__file__).absolute().parent
OLD=OUT.parent/"cli43-fresh-held2-r328-bf943a8137c74df09e010347615b0eec"/"stage-r329-http-owned-bytes.py"
EDITS=json.loads(r'''[["UID = '246c20b781664b0e80fae7fd29b9b2b4'","UID = 'b802270f725f47dc86f9ec829a60931a'"],["('cli43-fresh-held2-r329-' + UID)","('cli43-fresh-held2-r330-' + UID)"],["cli43_failed_execution_independent_review_codex/684f0c8b739541fe8da3b2f06ca78d09/review.json","cli43_failed_execution_independent_review_codex/0edb17f805c146b0b1ac47ea19e43c24/review.json"],["cli43_current_bound_scope_independent_review_codex/2770189c101441f39fcbe8fd83d98ffd/review.json","cli43_current_bound_scope_independent_review_codex/e786d3810e6448de98e43860b1cd175b/review.json"],["2685967ed7728d44182d671093cfee220b84bb438ea5d6524253573876750203","25b6b8d419a2006a521905066de6d8ec942303856c9e2bf4bd9e2a3106350021"],["need([cp['revision'], ow['revision'], len(cp['failure_counters'])] == [328, 156, 469], 'Actual before tuple')","need([cp['revision'], ow['revision'], len(cp['failure_counters'])] == [329, 157, 481], 'Actual before tuple')"],["'Actual current canonical equals r328 desired'","'Actual current canonical equals r329 desired'"],["late-origins.capture.for-r329.json","late-origins.capture.for-r330.json"],["34f37419ecc6715ffe7e28cb80f3b716fdffc746db0126bc86b5fa6d77e57416","df747951b37f06abcd0ad4b2a56ab615be31eedad4ae3908104903d525983892"],["'Fixed twelve-origin cut retained verbatim'","'Fixed twenty-one-origin cut retained verbatim'"],["late['before'] == [328,156,469] and late['after'] == [329,157,481] and len(late['origins']) == 12","late['before'] == [329,157,481] and late['after'] == [330,158,502] and len(late['origins']) == 21"],["len({r['evidence_ref']['sha256'] for r in origins}) == 12","len({r['evidence_ref']['sha256'] for r in origins}) == 21"],["inputs['before'] = [328, 156, 469]","inputs['before'] = [329, 157, 481]"],["inputs['after'] = [329, 157, 481]","inputs['after'] = [330, 158, 502]"],["cli43_http_bytes_ownership_preparation_codex/310e0bf842a34df6813dad1126e2970a","cli43_transport_binding_preparation_codex/2c271a22fbb34123a65d799e854b9d24"],["cli43_http_bytes_ownership_independent_review_codex/2c1fd6a5825447b99c8f7a9d6ceaa483/review.json","cli43_transport_binding_independent_review_codex/db438ad9e85f4cdc925a222cc31c3f01/review.json"],["2f8804bade77ee6bdf5c838055709167551ce76eab5f14acfd858e19d53ed56b","32e24ea665279ab628710f09eb9323e882cc475b034cf78d9bd7114de939ff9c"],["f6901f7c442c9e7aff7ebc36d47739f3316eb2f1cb3b5ba7316116d5e16b9789","8670727877b80f3cfe05a25ae563424952bb302660c2722ae291b00dea905728"],["a6262abc7510fc7974b5bebe71cc46a237d568729268e1686991024e6f8bf253","a3cc0c799dc51c584f51cf54f76931b337a6266933617fb7f9437f1297724352"],["37a3a61abe8fe81718021b17c7243fb3410c066a107cf346ec636b04bae176d9","9d021333686cb9405e68105c6c7725ccf18d58120643148c1f36e55d66a36664"],["need(template['instrumented_source_ref']['sha256'] == fix['unchanged_instrumented_test_ref']['sha256'], 'Business tests unchanged')","template['instrumented_source_ref'] = pin(fix['instrumented_source_ref']['path'])\nneed(template['instrumented_source_ref']['sha256'] == '6dbcdcc0fc12b2bd00a69f724cbe1f9598761fe467157273c6709344b1a1f29e' and fix['business_assertions_changed'] is False, 'Reviewed transport-only test additions; business assertions unchanged')"],["prior.name.replace('bf943a8137c74df09e010347615b0eec', UID)","prior.name.replace('246c20b781664b0e80fae7fd29b9b2b4', UID)"],["inputs['r329_changed_input_provenance']","inputs['r330_changed_input_provenance']"],["Export-only cli43Bytes immediately bytes.Clone before raw/len/SHA; no business or validator change.","Export-only strict transport facts distinguish POST commands and GET Goal/Task entities with completed-send links; immediate Clone, original business and Python validator unchanged."],["'runner_and_debug_helper_unchanged_from_r328'","'runner_and_debug_helper_unchanged_from_r329'"],["edec4df6c5f4fcce632008517adff4c4b2a82f64bc4715d87c8a53e7fd3e19c3","90aec754f429ee9f946ac6943685848b358a33e28ea2f4e7484b03235c6673e0"],["'Original r328 namespace byte prefix preserved'","'Original r329 namespace byte prefix preserved'"]]''')
raw=OLD.read_bytes();assert hashlib.sha256(raw).hexdigest()=="34c9ccedb8584dba76541b3aba60e652d3ee5646ae4f35c3e2b2c176fa910832"
text=raw.decode();facts=[]
for a,b in EDITS:
 count=text.count(a);assert count>=1,(a,count)
 facts.append({"old":a,"new":b,"actual_count":count});text=text.replace(a,b)
inverse=text
for row in reversed(facts):
 assert inverse.count(row["new"])==row["actual_count"],row["new"]
 inverse=inverse.replace(row["new"],row["old"])
assert inverse.encode()==raw
ast.parse(text)
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(name,v):
 with (OUT/name).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
new=OUT/"stage-r330-transport-binding.py"
with new.open("xb") as f:f.write(text.encode())
save("stage-r330-source-preparation.json",{"old_ref":pin(OLD),"new_ref":pin(new),"edits":facts,"whole_byte_inverse":True,"Python_AST_only":True,"target_Go_SQL_HTTP_SDK_MODEL":0,"canonical_writes":0,"formal_increment":0,"counter_reset":False})
print(json.dumps({"new_stage_ref":pin(new),"preparation_ref":pin(OUT/"stage-r330-source-preparation.json"),"target_calls":0},ensure_ascii=False))
