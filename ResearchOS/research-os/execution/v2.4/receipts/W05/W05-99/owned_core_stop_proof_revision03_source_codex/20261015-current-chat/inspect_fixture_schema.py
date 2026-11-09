import sqlite3
import sys

db = sqlite3.connect(sys.argv[1])
for name, sql in db.execute("SELECT name,sql FROM sqlite_master WHERE name IN ('resource_effects','runtime_dispatches','domain_objects','client_command_queue','client_control_requests') ORDER BY name"):
    print(name, sql)
