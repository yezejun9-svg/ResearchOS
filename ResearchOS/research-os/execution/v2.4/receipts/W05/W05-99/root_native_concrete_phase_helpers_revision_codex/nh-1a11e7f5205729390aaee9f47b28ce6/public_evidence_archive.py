"""Copy explicitly pinned public digest evidence only. No recursive archive."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
import types
from pathlib import Path

def main():
    if len(sys.argv) != 4:
        raise ValueError("REQUEST_PATH REQUEST_SHA256 REQUEST_BYTES")
    p = Path(sys.argv[1]).resolve(); raw = p.read_bytes()
    if "sha256:" + hashlib.sha256(raw).hexdigest() != sys.argv[2] or len(raw) != int(sys.argv[3]):
        raise ValueError("archive request pin")
    request = json.loads(raw)
    ref = request["HelperSource"]
    hp = Path(ref["path"]).resolve(); hraw = hp.read_bytes()
    if "sha256:" + hashlib.sha256(hraw).hexdigest() != ref["sha256"] or len(hraw) != ref["bytes"]:
        raise ValueError("helper Source pin")
    m = types.ModuleType("public_archive_source"); m.__file__ = str(hp)
    exec(compile(hraw, str(hp), "exec"), m.__dict__)
    request = m.decode(raw)
    m.require(set(request) == {"Schema", "HelperSource", "OutputDirectory", "Entries"}, "archive exact schema")
    m.require(request["Schema"] == "researchos.public-digest-evidence-archive-request.v1", "archive schema")
    out = m.canonical(request["OutputDirectory"])
    m.require(not out.exists() and out.parent.is_dir(), "fresh explicit archive directory")
    inputs = m.Inputs(); inputs.read(ref)
    items = []
    for entry in request["Entries"]:
        m.require(set(entry) == {"Kind", "Source", "Name"}, "archive explicit item")
        name = entry["Name"]
        m.require(type(name) is str and name.endswith(".json") and Path(name).name == name and "/" not in name and "\\" not in name, "one safe JSON name")
        m.require(name.casefold() != "archive.public.manifest.json", "reserved archive manifest name")
        m.require(all(name.casefold() != x[0].casefold() for x in items), "duplicate archive destination")
        data = inputs.read(entry["Source"]); value = m.decode(data)
        if entry["Kind"] == "typed-row-digests":
            m.public_rows(value)
        elif entry["Kind"] == "fixture-summary":
            expected = {"case", "credential_output", "database", "formal", "owner_root", "production_db_writes", "project_id", "provider_requests", "root", "run_id", "schema", "schema_sha256", "synthetic", "typed_rows_sha256"}
            m.require(set(value) == expected and value["schema"] == "researchos.synthetic-native-fixture.v1", "public fixture schema")
            m.require(value["synthetic"] is True and value["formal"] is False and value["credential_output"] is False and type(value["provider_requests"]) is int and value["provider_requests"] == 0 and type(value["production_db_writes"]) is int and value["production_db_writes"] == 0, "public fixture only")
            m.require(value["case"] == "positive-replay" and value["owner_root"] == "queue-upgrade-owner", "known fixture scalars")
            for key in ("project_id", "run_id"):
                m.require(type(value[key]) is str and m.re.fullmatch("[0-9a-f]{32}", value[key]), "public ID")
            for key in ("schema_sha256", "typed_rows_sha256"):
                m.require(type(value[key]) is str and m.re.fullmatch("sha256:[0-9a-f]{64}", value[key]), "public digest")
            m.canonical(value["database"]); m.canonical(value["root"])
        else:
            raise ValueError("unsupported archive kind; private resources, raw receipts, SQL and arbitrary JSON are forbidden")
        # Never follow references or source paths contained inside public JSON.
        items.append((name, data, entry["Source"], entry["Kind"]))
    m.require(items, "nonempty explicit public evidence selection")
    inputs.close_check()
    out.mkdir()
    manifest = []
    for name, data, source, kind in items:
        dest = out / name
        with dest.open("xb") as stream:
            stream.write(data)
        m.require(dest.read_bytes() == data, "exact public archive copy")
        manifest.append(dict(kind=kind, source_ref=source, archived_ref=dict(path=str(dest), sha256=m.digest(data), bytes=len(data))))
    inputs.close_check()
    with (out / "archive.public.manifest.json").open("xb") as stream:
        stream.write((json.dumps(dict(schema="researchos.public-digest-evidence-archive.v1", members=manifest,
            no_private_resource_followed=True, no_raw_rows_or_credentials_copied=True,
            byte_exact_public_copies=True, native_SQL_model=False, formal_acceptance=False), ensure_ascii=True, indent=2)+"\n").encode())
    print(json.dumps(dict(archive_directory=str(out),public_files=len(items),formal_acceptance=False)))

if __name__ == "__main__":
    main()

