from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w05-runtime-routing-20261104')
p=root/'ops/ci/runtime_v24.py'
s=p.read_text(encoding='utf-8')
s=s.replace('row.get("task_id") == task_id and row.get("check_id") == check_id, "runtime check binding"', 'row.get("key") == "test.runtime" and row.get("task_id") == task_id and row.get("check_id") == check_id and not row.get("case_id"), "runtime check binding"')
s=s.replace('row.get("task_id") == task_id and row.get("case_id") == case_id, "A04 formal binding"', 'row.get("key") == "test.runtime" and row.get("task_id") == task_id and row.get("case_id") == case_id and not row.get("check_id"), "A04 formal binding"')
s=s.replace('if (case.get("mode") != "LIVE_WINDOWS" or [row.get("id")', 'if (case.get("mode") != "LIVE_WINDOWS" or case.get("final_owner_task") != "W05" or case.get("command_keys") != ["test.runtime"] or [row.get("id")')
s=s.replace('"passed": False, "assertion_ids": [],', '"measurement_mode": "NOT_RUN", "passed": False, "assertion_ids": [],')
p.write_text(s,encoding='utf-8',newline='\n')
print('refined explicit NOT_RUN measurement and exact command/owner bindings')
