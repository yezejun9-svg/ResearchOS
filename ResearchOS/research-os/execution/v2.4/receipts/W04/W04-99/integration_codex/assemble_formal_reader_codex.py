"""Promote frozen reviewed integrity primitives into fixed repository source."""
from pathlib import Path
import hashlib, json, re
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]
SOURCE=HERE.parent/'formal_validator_codex/validate.py'; TARGET=ROOT/'execution/v2.4/formal_case_index.py'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='5add6b0044da783d009b52cdaac3402be053303006691ec337eac767d247e894'
assert not TARGET.exists()
raw=SOURCE.read_text(encoding='utf8').split('\ndef main(argv=None):',1)[0]
raw=raw.replace('def _check(', 'def _check_w04_profile_impl(').replace('def check(', 'def _check_w04_profile(').replace('return _check(', 'return _check_w04_profile_impl(')
raw,count=re.subn(r'(?m)^( +)reader.finish\(\)\n\1return result',r'\1reader.finish()\n\1result["input_hashes"] = {str(path): digest for path, digest in reader.read_hashes.items()}\n\1return result',raw)
assert count==2
start=raw.index('    registry = reader.document(context["registry_ref"])')
end=raw.index('    runs = {}',start)
raw=raw[:start]+'''    registry = None
    if "registry_ref" in context:
        canonical_path = reader.path("execution/v2.4/commands.json")
        require(context["registry_ref"]["path"] == "execution/v2.4/commands.json", "CANONICAL_REGISTRY", "registry")
        current_registry = reader.read(canonical_path)
        if "registry_snapshot_ref" in context:
            registry = reader.document(context["registry_snapshot_ref"], ROOT_INPUT_PREFIX)
            require(context["registry_snapshot_ref"]["sha256"] == context["registry_ref"]["sha256"], "REGISTRY_SNAPSHOT", "execution snapshot SHA")
            # Unrelated bindings may be added later. Every actually used entry
            # still has to match the retained execution-time full registry.
            for used_key in {b["key"] for b in formal_bindings + gate_bindings}:
                require(registry.get("commands", {}).get(used_key) == current_registry.get("commands", {}).get(used_key),
                        "NEEDS_REVALIDATION", "used registered binding changed: " + used_key)
        else:
            registry = reader.document(context["registry_ref"])
        require(type(registry.get("revision")) is int and registry["revision"] > 0, "COMMAND_REVISION", "registry")
''' +raw[end:]
first_end=raw.index('"""',3)+3
header='''"""Derive current formal case validity from canonical independent registration.

This stdlib reader executes no products, receipt code, drivers or external calls.
The explicit W04 v1 compatibility profile is based on frozen strict primitives
at SHA5add6b0044da783d009b52cdaac3402be053303006691ec337eac767d247e894.
The generic catalog/aggregation layer covers all42 frozen cases; other evidence
profiles fail closed until separately implemented. Distinct strings alone do
not authenticate actors: root-observed issuance is the process trust boundary.
"""'''
raw=header+raw[first_end:]
TARGET.write_text(raw+'\n'+(HERE/'formal_accounting_body_codex.py').read_text(encoding='utf8'),encoding='utf8')
compile(TARGET.read_text(encoding='utf8'),str(TARGET),'exec')
record={'schema':'researchos.formal-reader-source-provenance.v1','frozen_primitive_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'construction_body_sha256':hashlib.sha256((HERE/'formal_accounting_body_codex.py').read_bytes()).hexdigest(),
    'target_path':TARGET.relative_to(ROOT).as_posix(),'target_sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),
    'scope':'Fixed repository source, no runtime import of construction validator/driver; independently reviewed current read-only aggregation still pending.',
    'formal_case_count_delta':0}
with (HERE/'formal_reader_source_provenance_codex.json').open('x',encoding='utf8') as f: json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':'SOURCE_COMPILED_NOT_ACCEPTED','target_sha256':record['target_sha256']}))
