from pathlib import Path
import ast,hashlib,json
out=Path(__file__).parent
source=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/desktop58_windows_runtime_static_candidate_codex/1d68f5262a334f82b63d21abd4a350ca/capture_pe_static.py")
raw=source.read_bytes();text=raw.decode();tree=ast.parse(text)
names=("u16","u32","u64","cstr","parse_pe")
parts=[ast.get_source_segment(text,next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)) for name in names]
new="import struct\n\n"+"\n\n".join(parts)+"\n"
with (out/"pe_reader.py").open("xb") as f:f.write(new.encode())
with (out/"parser-provenance.json").open("xb") as f:f.write((json.dumps({"source_ref":{"path":str(source),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)},"copied_definitions":list(names),"exact_source_segments":True,"top_level_original_not_executed":True},indent=2)+"\n").encode())
print("Copied five pure byte parser definitions; original module not imported or executed.")

