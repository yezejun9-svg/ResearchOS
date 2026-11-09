"""Create a review-only purpose-specific controller from the pinned prior helper."""
import ast,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
SOURCE=R/'execution/v2.4/receipts/W05/W05-99/native_migration_controller_temp_env_revision_codex/e6a4d23ff0a84a6d9c2905181d97c2e4/root_native_migration_controller.py'
TARGET=O/'root_native_pause_migration_controller.py'
raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()=='a1f53e223f47c5d8ecdb7edc5f94fec0bcc36beae9774d16ad9d0002b6ef638a'
code=raw.decode('utf8');changes=[]
def change(before,after,count=1):
 global code
 assert code.count(before)==count,(before,code.count(before),count)
 code=code.replace(before,after);changes.append({'before':before,'after':after,'occurrences':count})
change('Root-only migration controller.','Root-only schema24-to25 pause migration controller.')
change('current-schema23-to24-grant.json','current-schema24-to25-grant.json',2)
change('consumed-schema23-to24-grants','consumed-schema24-to25-grants')
change('researchos.root-native-migration-controller.v1','researchos.root-native-pause-migration-controller.v1')
change('researchos.synthetic-native-migration-config.v1','researchos.synthetic-native-pause-migration-config.v1')
change('for key in ("RootProgram", "ControlProgram", "BackupProgram", "EnrollmentProgram",','for key in ("SourceBackupProgram", "RootProgram", "ControlProgram", "BackupProgram", "EnrollmentProgram",')
change('"-tags=researchos_native_recovery_harness" not in build_argv or','any(arg.startswith("-tags") for arg in build_argv) or\n        "./internal/domain" not in build_argv or')
change('inventory["build_tag"] != "researchos_native_recovery_harness"','inventory["build_tag"] != ""')
change('raise ValueError("tagged compiler inventory required")','raise ValueError("untagged Windows test compiler inventory required")')
change('if "RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT" in env:\n        _require_isolated_temp_environment(env)','_require_isolated_temp_environment(env)')
change('env["RESEARCHOS_NATIVE_MIGRATION_HARNESS_CONFIG"]','env["RESEARCHOS_NATIVE_PAUSE_MIGRATION_HARNESS_CONFIG"]')
change('^TestNativeMigrationAuthorityHarness$','^TestNativePauseMigrationAuthorityHarness$')
change('else "migration-grant"','else "pause-migration-grant"',2)
change('''        if c["hc"]["Case"] == "expired-grant":
            if not expires < now:
                raise ValueError("expired negative no longer describes an expired grant")
        elif not issued <= now < expires:
            raise ValueError("grant absolute validity elapsed; no extension or retry")''','''        # The pause harness signs an initially valid short grant, then waits
        # past expiry before Native invocation. Never sign an expired payload.
        if c["hc"]["Case"] == "expired-grant" and (expires-issued).total_seconds() > 90:
            raise ValueError("expired negative requires at most ninety seconds")
        if not issued <= now < expires:
            raise ValueError("grant absolute validity elapsed; no extension or retry")''')
ast.parse(code)
with TARGET.open('x',encoding='utf8',newline='\n') as f:f.write(code)
with (O/'adaptation.json').open('x',encoding='utf8') as f:json.dump({'schema':'researchos.native25-controller-adaptation/1','status':'DRAFT_NOT_AUTHORIZED_TO_RUN_PENDING_INDEPENDENT_REVIEW','base':{'path':str(SOURCE),'sha256':hashlib.sha256(raw).hexdigest()},'target':{'path':str(TARGET),'sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest()},'changes':changes,'children_started':0,'private_keys_read':0,'signatures_created':0,'formal_increment':0},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':'DRAFT_ONLY','sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),'changes':len(changes)}))
