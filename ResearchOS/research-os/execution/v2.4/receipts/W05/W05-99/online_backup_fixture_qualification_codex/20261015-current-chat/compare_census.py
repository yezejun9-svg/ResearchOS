"""Summarize task-owned census receipts; never emits table rows or file bytes."""
import json
import sys
from pathlib import Path

evidence = Path(__file__).resolve().parent
prefix = sys.argv[1]
def read(part):
    return json.loads((evidence / f"{prefix}-{part}.stdout.raw").read_text(encoding="utf-8"))
before, after, restored = read("db-before"), read("db-after"), read("db-restored")
files_before, files_after = read("files-before"), read("files-after")
name_union = sorted(set(before["tables"]) | set(after["tables"]))
source_diffs = {name:{"before":before["tables"].get(name),"after":after["tables"].get(name)} for name in name_union if before["tables"].get(name) != after["tables"].get(name)}
file_union = sorted(set(files_before["entries"]) | set(files_after["entries"]))
file_diffs = {name:{"before":files_before["entries"].get(name),"after":files_after["entries"].get(name)} for name in file_union if files_before["entries"].get(name) != files_after["entries"].get(name)}
restored_names = sorted(set(before["tables"]) | set(restored["tables"]))
restored_diffs = {name:{"source":before["tables"].get(name),"restored":restored["tables"].get(name)} for name in restored_names if before["tables"].get(name) != restored["tables"].get(name)}
out = {"case":prefix,"source_schema_equal":before["schema_sha256"] == after["schema_sha256"],
       "source_version_equal":before["user_version"] == after["user_version"],
       "source_integrity_before":before["integrity_check"],"source_integrity_after":after["integrity_check"],
       "source_table_count":len(before["tables"]),"source_all_tables_equal":not source_diffs,
       "source_table_differences":source_diffs,"source_file_differences":file_diffs,
       "restored_integrity":restored["integrity_check"],"restored_table_count":len(restored["tables"]),
       "restored_table_differences":restored_diffs}
print(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(",", ":")))
