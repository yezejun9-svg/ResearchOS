import sys,json,sqlite3,hashlib,shutil,os
from pathlib import Path
from urllib.parse import quote
from driver import E,R,W,A,T,run,save
def j(n):return json.loads((E/n).read_text(encoding="utf8"))
def con(p):
    d=sqlite3.connect("file:"+quote(str(p.resolve()).replace("\\","/"),safe="/:")+"?mode=ro",uri=True)
    d.execute("PRAGMA query_only=ON");return d
def compare():
    before=j("f04-db-before.stdout.raw");after=j("f09-db-after.stdout.raw");neg=j("f15-db-after-negative.stdout.raw");restored=j("f20-db-restored.stdout.raw")
    assert before==after==neg
    n=sum(not k.startswith("sqlite_") for k in before["tables"])
    assert n==88 and before["integrity_check"]==restored["integrity_check"]=="ok"
    changed={k:{"source":before["tables"][k],"restored":restored["tables"][k]} for k in before["tables"] if before["tables"][k]!=restored["tables"][k]}
    assert set(changed)=={"auth_credentials","domain_objects","domain_refs","domain_versions"},list(changed)
    f1=j("f05-files-before.stdout.raw")["entries"];f2=j("f10-files-after.stdout.raw")["entries"]
    fd={k:{"before":f1.get(k),"after":f2.get(k)} for k in f1.keys()|f2.keys() if f1.get(k)!=f2.get(k)}
    hash_changes=[k for k in f1.keys()|f2.keys() if f1.get(k,{}).get("sha256")!=f2.get(k,{}).get("sha256")]
    acl=(E/"f06-acl-before.stdout.raw").read_bytes()==(E/"f11-acl-after.stdout.raw").read_bytes()
    assert acl
    packagebefore=j("f12-package-before-negative.stdout.raw")
    packageafter=j("f14-package-after-negative.stdout.raw")
    assert packagebefore==packageafter
    src=con(T/"fixture/source-data/researchos.sqlite");dst=con(T/"fixture/restored-data/researchos.sqlite")
    def objects(db):return {(k,i):json.loads(b) for k,i,b in db.execute("SELECT kind,id,body FROM domain_objects")}
    a,b=objects(src),objects(dst)
    delta=[]
    for k in a:
        if a[k]!=b[k]:
            delta.append({"kind":k[0],"id":k[1],"fields":[f for f in set(a[k])|set(b[k]) if a[k].get(f)!=b[k].get(f)]})
    sb=[v for (k,i),v in a.items() if k=="WorkspaceBinding"][0]
    rb=[v for (k,i),v in b.items() if k=="WorkspaceBinding"][0]
    target=Path(rb["real_path"]).resolve()
    assert target.is_relative_to((T/"fixture/restored-data").resolve())
    assert sb["authorized_workspace_ref"]==rb["authorized_workspace_ref"] and sb["project_id"]==rb["project_id"]
    assert (target/"src/main.go").read_bytes()==b"package fixture\n"
    assert (target/"empty").is_dir()
    ac=src.execute("SELECT * FROM auth_credentials").fetchall()
    bc=dst.execute("SELECT * FROM auth_credentials").fetchall()
    assert ac!=bc
    out=dict(all88_source_logical_census_equal=True,schema_equal=before["schema_sha256"]==restored["schema_sha256"],table_count=n,
       source_native_file_deltas=fd,source_content_hash_changes=hash_changes,acl_equal=acl,package_unchanged_after_existing_destination=True,
       restored_changed_tables=changed,restored_object_field_deltas=delta,workspace_ref_and_project_equal=True,workspace_new_path=str(target),
       empty_directory_preserved=True,file_hash=hashlib.sha256((target/"src/main.go").read_bytes()).hexdigest(),credentials_changed=True,
       source_migration_max=src.execute("SELECT max(version) FROM schema_migrations").fetchone()[0])
    assert out["source_migration_max"]==24
    save("fresh-census-deltas.json",out)
    print(json.dumps(out,ensure_ascii=False))
def identity():
    c=T/"fixture";w=c/"chosen-workspace";old=c/"retired-workspace"
    assert w.is_dir() and not old.exists()
    pre={p.relative_to(w).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in w.rglob("*") if p.is_file()}
    w.rename(old);shutil.copytree(old,w)
    post={p.relative_to(w).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in w.rglob("*") if p.is_file()}
    assert pre==post
    save("native-workspace-identity-fixture-change.json",dict(visible_file_bytes_equal=True,before=pre,after=post,old_path=str(old),replacement_path=str(w),old_inode=old.stat().st_ino,new_inode=w.stat().st_ino))
    assert old.stat().st_ino!=w.stat().st_ino
    run("n01-native-workspace-id-refusal",[T/"build/backup.exe","create","--db",c/"source-data/researchos.sqlite","--out",c/"refused-package","--key-file",T/"private/recovery.key","--root",W],1)
    assert b"BACKUP_WORKSPACE_PIN_CHANGED" in (E/"n01-native-workspace-id-refusal.stderr.raw").read_bytes()
    assert not (c/"refused-package").exists()
    run("n02-db-after-native-refusal",[sys.executable,"-B","-Xutf8",E/"census.py","db",c/"source-data/researchos.sqlite"])
    assert j("f04-db-before.stdout.raw")==j("n02-db-after-native-refusal.stdout.raw")
    print("NATIVE_ID_CHANGED_SAME_BYTES_REFUSED_NO_PUBLISH_SOURCE_LOGICAL_EQUAL")
def q03():
    c=R/".local/online-backup-fixture-qualification-20261015-tmp/fixture/Q03"
    s=con(c/"current-data-r2/researchos.sqlite");d=con(c/"restored-data/researchos.sqlite")
    assert s.execute("SELECT max(version) FROM schema_migrations").fetchone()[0]==24
    def facts(db):
        return dict(
          runs=db.execute("SELECT json_extract(body,'$.status'),count(*) FROM domain_objects WHERE kind='Run' GROUP BY 1").fetchall(),
          effects=db.execute("SELECT json_extract(body,'$.state'),count(*) FROM resource_effects GROUP BY 1").fetchall(),
          queue=db.execute("SELECT state,count(*) FROM client_command_queue GROUP BY 1").fetchall(),
          controls=db.execute("SELECT state,count(*) FROM client_control_requests GROUP BY 1").fetchall(),
          workspaces=db.execute("SELECT json_extract(body,'$.status'),count(*) FROM domain_objects WHERE kind='WorkspaceBinding' GROUP BY 1").fetchall())
    a,b=facts(s),facts(d)
    assert a["runs"]==[("QUEUED",1)] and b["runs"]==[("RECONCILING",1)]
    assert a["queue"]==b["queue"]==[("UNKNOWN",1)]
    assert a["controls"]==[("REQUESTED",1)] and b["controls"]==[("RECONCILING",1)]
    assert a["workspaces"]==b["workspaces"]==[("REVOKED",1)]
    subset={}
    for t in ["resource_effects","client_control_receipts","uploaded_content"]:
        x=s.execute("SELECT * FROM "+t).fetchall();y=d.execute("SELECT * FROM "+t).fetchall()
        assert all(row in y for row in x),t
        subset[t]=dict(original_rows=len(x),restored_rows=len(y),original_rows_byte_value_equal_subset=True)
    assert subset["resource_effects"]["restored_rows"]==subset["resource_effects"]["original_rows"]+1
    assert subset["client_control_receipts"]["restored_rows"]==subset["client_control_receipts"]["original_rows"]+1
    import re
    source=(W/"internal/domain/backup_command_queue.go").read_text(encoding="utf8")
    section=source[source.index("func validateBackupQueue"):source.index("func fenceRestoredClientQueues")]
    checks=re.findall(chr(96)+r"(SELECT count\(\*\).*?)"+chr(96),section,re.S)
    checked=[]
    for query in checks:
        if "?" in query:continue
        x=s.execute(query).fetchone()[0];y=d.execute(query).fetchone()[0]
        assert x==y==0
        checked.append(hashlib.sha256(query.encode()).hexdigest())
    out=dict(current_migration=24,source=a,restored=b,immutable_history=subset,production_validator_readonly_sql_checks=checked,
      author_full_production_validator_and_cli_evidence_pinned=True,exact_actual_raw3_ack2_modelconfirmed_costunknown_qualified=False)
    save("q03-independent-history-review.json",out)
    print(json.dumps(out))
if __name__=="__main__":globals()[sys.argv[1]]()

