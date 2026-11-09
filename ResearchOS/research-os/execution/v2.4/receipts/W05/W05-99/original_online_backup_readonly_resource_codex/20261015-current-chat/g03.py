from readonly import *
INTENT="Exact production active workspace selector plus selected public binding/project fields and queue/control aggregate counts."
h=scope["historical_subject_reference_only"]
SQL=[
 {"name":"active_workspace_count_exact_opsbackup","sql":"SELECT count(*) FROM domain_objects WHERE project='' AND kind=? AND json_extract(body,'$.status')=?","params":["WorkspaceBinding","ACTIVE"],"row_cap":1},
 {"name":"workspace_status_counts","sql":"SELECT json_extract(body,'$.status') AS status,count(*) AS count FROM domain_objects WHERE project='' AND kind='WorkspaceBinding' GROUP BY 1 ORDER BY 1 LIMIT 16","row_cap":16},
 {"name":"active_workspace_public_fields","sql":"SELECT id,revision,json_extract(body,'$.authorized_workspace_ref') AS authorized_workspace_ref,json_extract(body,'$.project_id') AS project_id,json_extract(body,'$.real_path') AS real_path,json_extract(body,'$.access') AS access,json_extract(body,'$.status') AS status,json_extract(body,'$.host_principal_ref') AS host_principal_ref FROM domain_objects WHERE project='' AND kind='WorkspaceBinding' AND json_extract(body,'$.status')='ACTIVE' ORDER BY id LIMIT 9","row_cap":9},
 {"name":"historical_subject_project_current_metadata","sql":"SELECT project,kind,id,revision,json_extract(body,'$.status') AS status,json_extract(body,'$.real_path') AS real_path FROM domain_objects WHERE kind='Project' AND id=? LIMIT 2","params":[h["project_id"]],"row_cap":2},
 {"name":"queue_state_counts","sql":"SELECT state,count(*) AS count FROM client_command_queue GROUP BY state ORDER BY state LIMIT 32","row_cap":32},
 {"name":"control_state_counts","sql":"SELECT state,count(*) AS count FROM client_control_requests GROUP BY state ORDER BY state LIMIT 32","row_cap":32},
 {"name":"table_counts","sql":"SELECT count(*) AS total_tables,sum(CASE WHEN name NOT LIKE 'sqlite_%' THEN 1 ELSE 0 END) AS non_sqlite_tables FROM sqlite_schema WHERE type='table'","row_cap":1},
 {"name":"restoration_barrier_count","sql":"SELECT count(*) AS barriers FROM backup_restore_barriers","row_cap":1},
 {"name":"restoration_trigger_presence","sql":"SELECT count(*) AS count FROM sqlite_schema WHERE type='trigger' AND name='backup_require_fresh_observation'","row_cap":1}
]
if __name__=="__main__":query_group("g03",SQL)

