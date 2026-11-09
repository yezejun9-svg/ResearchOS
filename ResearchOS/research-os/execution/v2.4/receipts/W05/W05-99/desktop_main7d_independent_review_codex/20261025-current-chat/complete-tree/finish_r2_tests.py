import hashlib,json,pathlib,shutil,stat
E=pathlib.Path(__file__).parent.resolve()
temp=E/'r2-test-temp'
assert temp.resolve().is_relative_to(E) and temp.name=='r2-test-temp'
rows=[]
for child in temp.iterdir():
    assert child.name.startswith('ros-desktop-development-mock-') and child.resolve().is_relative_to(temp)
    for path in child.rglob('*'):
        assert path.resolve().is_relative_to(temp)
        if path.is_file():
            rows.append({'path':path.relative_to(temp).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
(E/'R2-test-temp-retained-inventory.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
# Only our fresh synthetic fixture tree is removed; raw test results stay immutable.
shutil.rmtree(temp)
assert not temp.exists()
freeze=json.loads((E/'r2-fixed-inputs/source-freeze-02.json').read_bytes())
for name,row in freeze['seven_file_hashes'].items():
    assert hashlib.sha256((E/'source-r2'/name).read_bytes()).hexdigest()==row['sha256']
results={label:json.loads((E/('r2-'+label)/'result.json').read_bytes()) for label in ['node-focused','python-focused']}
assert all(row['native_exit']==0 for row in results.values())
summary={'results':results,'node_tests':{'pass':6,'fail':0,'skip':0},'python_tests':{'pass':3,'fail':0,'skip':2,'skip_reasons':['actual built bundle not supplied yet','Windows file symlink privilege unavailable']},'source_stable':True,'native_gui_or_core_starts':0,'review_harness_failure':{'ordinal':'011','native_exit':1,'cause':'Post-test fixture cleanup assertion: Node rmSync returned without removing four deeply nested mock directories; test processes both exit zero','preserved':True,'fixture_file_count':len(rows),'cleanup':'Own fresh synthetic fixtures recorded by hash then removed using Python shutil within verified evidence root; no test rerun'}}
(E/'R2-focused-test-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
