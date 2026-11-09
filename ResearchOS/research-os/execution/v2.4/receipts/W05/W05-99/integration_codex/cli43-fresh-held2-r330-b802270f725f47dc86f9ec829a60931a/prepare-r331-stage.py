"""Prepare a new r331 metadata-only stage from the immutable r330 source; no execution."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json
ROOT=Path(r"D:\作品集\ResearchOS\research-os")
OUT=Path(__file__).absolute().parent
OLD=ROOT/"execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r329-246c20b781664b0e80fae7fd29b9b2b4/stage-r330-transport-binding.py"
edits=json.loads(r'''[["r330","r331"],["b802270f725f47dc86f9ec829a60931a","c4f309c5528f5d42be5e7eeb146a20aa"],["0edb17f805c146b0b1ac47ea19e43c24","b33d80b428a247539130e8585e85f3c7"],["25b6b8d419a2006a521905066de6d8ec942303856c9e2bf4bd9e2a3106350021","526b392eca9f7e5b84d67537aac9d7d132e074b7e02868213bf73e6a4b01bf75"],["e786d3810e6448de98e43860b1cd175b","c4d60cc9f599670bde83623470696282"],["[330,158,502]","[331,159,509]"],["[330, 158, 502]","[331, 159, 509]"],["[329,157,481]","[330,158,502]"],["[329, 157, 481]","[330, 158, 502]"],["late-origins.capture.for-r331.json","late-origins.capture.for-r331.v2.json"],["df747951b37f06abcd0ad4b2a56ab615be31eedad4ae3908104903d525983892","d0357fc7dc726377ed6f9984f5865d6a51fadcba1f3fb9d3550aeca1acbea187"],["twenty-one-origin","seven-origin"],["len(late['origins']) == 21","len(late['origins']) == 7"],["== 21, 'Distinct","== 7, 'Distinct"],["cli43_transport_binding_preparation_codex/2c271a22fbb34123a65d799e854b9d24","cli43_legacy_entity_schema_preparation_codex/26c182c39c734501ac4f85cf6c978a86"],["cli43_transport_binding_independent_review_codex/db438ad9e85f4cdc925a222cc31c3f01","cli43_legacy_entity_schema_independent_review_codex/7dd9e18c009e45b4a6a205fb06ddfb70"],["32e24ea665279ab628710f09eb9323e882cc475b034cf78d9bd7114de939ff9c","10d3d482a47aaaf076e8d45b12d0d03f345468ecf24e88a35d4f15d950fa603b"],["8670727877b80f3cfe05a25ae563424952bb302660c2722ae291b00dea905728","d392aa0c2bd44786e1de60da4331752552a57d82d25caa86f6b36ab5eea342bf"],["a3cc0c799dc51c584f51cf54f76931b337a6266933617fb7f9437f1297724352","ef10204d2fe2d59af7b59e1bdb7d4a375f3880ce4bdae999ea10ec1b30ed40ca"],["9d021333686cb9405e68105c6c7725ccf18d58120643148c1f36e55d66a36664","091e045b1313f318191128b065b0486a81ced3991a3fcade73fe557d583e2ccc"],["246c20b781664b0e80fae7fd29b9b2b4","b802270f725f47dc86f9ec829a60931a"],["runner_and_debug_helper_unchanged_from_r329","runner_and_debug_helper_unchanged_from_r330"],["Original r329 namespace","Original r330 namespace"],["equals r329 desired","equals r330 desired"],["90aec754f429ee9f946ac6943685848b358a33e28ea2f4e7484b03235c6673e0","b9b29be36829a2f85fc666da222ca64d7654916062ef8504b7ef0f3a5ab89359"],["Export-only strict transport facts distinguish POST commands and GET Goal/Task entities with completed-send links; immediate Clone, original business and Python validator unchanged.","GET Goal/Task validation path and exact raw SHA now match unmodified fixture domain.New legacy schema b114; strict schema, transport, completed-send links, immediate Clone, original business and Python validator unchanged."]]''')
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,v):
 with (OUT/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
raw=OLD.read_bytes();assert hashlib.sha256(raw).hexdigest()=="625c033f2df07160e1ccbf94929bcc6de1800bc32f035ae6d3a9c34fedba50df"
text=raw.decode();records=[]
for old,new in edits:
 count=text.count(old);assert count>0,(old,count)
 text=text.replace(old,new);records.append({"old":old,"new":new,"occurrences":count})
inverse=text
for r in reversed(records):
 assert inverse.count(r["new"])==r["occurrences"],r
 inverse=inverse.replace(r["new"],r["old"])
assert inverse.encode()==raw
dest=OUT/"stage-r331-legacy-schema-binding.py"
with dest.open("xb") as f:f.write(text.encode())
compile(text,str(dest),"exec")
save("stage-r331.source-preparation.json",{"source_ref":pin(OLD),"stage_ref":pin(dest),"edits":records,"whole_byte_inverse":True,"compile_AST_only":True,"new_execution_uuid":"c4f309c5528f5d42be5e7eeb146a20aa","new_bound_review_uuid":"c4d60cc9f599670bde83623470696282","before":[330,158,502],"after":[331,159,509],"canonical_writes":0,"target_calls":0,"formal_increment":0,"counter_reset":False})
print(json.dumps({"stage_ref":pin(dest),"preparation_ref":pin(OUT/"stage-r331.source-preparation.json"),"new_execution_uuid":"c4f309c5528f5d42be5e7eeb146a20aa","new_bound_review_uuid":"c4d60cc9f599670bde83623470696282","target_calls":0},ensure_ascii=False))
