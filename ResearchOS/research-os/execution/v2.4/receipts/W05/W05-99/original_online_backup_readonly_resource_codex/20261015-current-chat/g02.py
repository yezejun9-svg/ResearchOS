from readonly import *
INTENT="Original readonly schema metadata and filesystem sidefile metadata; no table payloads or content copy."
SQL=[
 {"name":"query_only","sql":"PRAGMA query_only","row_cap":1},
 {"name":"sqlite_version","sql":"SELECT sqlite_version() AS observer_sqlite_version","row_cap":1},
 {"name":"journal_mode","sql":"PRAGMA journal_mode","row_cap":1},
 {"name":"user_version","sql":"PRAGMA user_version","row_cap":1},
 {"name":"migration_versions","sql":"SELECT version FROM schema_migrations ORDER BY version LIMIT 64","row_cap":64},
 {"name":"schema_names","sql":"SELECT type,name FROM sqlite_schema WHERE type IN ('table','trigger') ORDER BY type,name LIMIT 128","row_cap":128},
]
for table in ["domain_objects","runtime_dispatches","resource_effects","resource_resolutions","client_command_queue","client_control_requests","runtime_observations","client_control_receipts"]:
 SQL.append({"name":"columns_"+table,"sql":"PRAGMA table_info("+table+")","row_cap":64})
if __name__=="__main__":query_group("g02",SQL)

