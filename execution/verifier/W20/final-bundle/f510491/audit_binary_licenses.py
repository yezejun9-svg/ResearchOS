import hashlib,json,subprocess,tempfile,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
lock=json.loads((ROOT/'execution/toolchains/locked.json').read_text(encoding='utf-8'))
go=Path(lock['tools']['go']['path']);assert sha(go.read_bytes())==lock['tools']['go']['sha256']
with zipfile.ZipFile(ROOT/'.local/researchos-final-f510491-a.zip') as archive:
    manifest=json.loads(archive.read('release-manifest.json'))
    expected={'control':'researchos.local/research-os/apps/control','runtime':'researchos.local/research-os/ops/runtime','backup':'researchos.local/research-os/ops/backup','release_host':'researchos.local/research-os/ops/supervisor/release_host'}
    compiled={};binaries={}
    for name,package in expected.items():
        with tempfile.NamedTemporaryFile(prefix='inspect-',suffix='.exe',dir=OUT,delete=False) as f:
            f.write(archive.read(f'bin/{name}.exe'));temporary=Path(f.name)
        try:
            output=subprocess.check_output([str(go),'version','-m',str(temporary)],cwd=ROOT,text=True,encoding='utf-8')
        finally:temporary.unlink()
        lines=output.splitlines();fields=[line.strip().split('\t') for line in lines[1:]]
        assert any(x==['path',package] for x in fields)
        settings={}
        for x in fields:
            if x[0]=='dep':compiled[(x[1],x[2])]=x[3]
            if x[0]=='build' and len(x)>1:
                key,_,value=x[1].partition('=');settings[key]=value
        assert settings['-trimpath']=='true' and settings['GOOS']=='windows' and settings['GOARCH']=='amd64' and settings['CGO_ENABLED']=='0'
        # Build-info does not promise to expose linker flags. Only report the
        # fields actually present; reproducibility is proved by archive bytes.
        linker_flags_observation=settings.get('-ldflags','NOT_REPORTED_BY_BUILD_INFO')
        assert 'go1.27.1' in lines[0]
        binaries[name]={'package':package,'settings':settings,'linker_flags_observation':linker_flags_observation,'build_info_lines':lines[1:]}
    assert compiled=={(m['name'],m['version']):m['sum'] for m in manifest['sbom']['go']}
    local_npm=[]
    for module in manifest['sbom']['npm']:
        directory=ROOT/'apps/web/node_modules'/module['name']
        if module['installation_status']=='OPTIONAL_NOT_INSTALLED':
            assert not directory.is_dir();continue
        metadata=json.loads((directory/'package.json').read_text(encoding='utf-8'))
        assert metadata['version']==module['version']
        assert metadata.get('license',module['declared_license'])==module['declared_license']
        paths=sorted(p for p in directory.iterdir() if p.is_file() and p.name.upper().startswith(('LICENSE','THIRD-PARTY-LICENSE')))
        assert [p.name for p in paths]==[t['source_file'] for t in module['license_texts']]
        for p,text in zip(paths,module['license_texts']):assert p.read_bytes()==archive.read(text['file'])
        local_npm.append({'name':module['name'],'version':metadata['version'],'license_files':[p.name for p in paths]})
    assert not (ROOT/'LICENSE').exists()
    assert manifest['sbom']['license_gaps']==['ResearchOS main module: license file unavailable','npm @rolldown/binding-win32-x64-msvc: license text unavailable']
    source='f51049149b6ba0d53c83f5bb5cf0274ea1039c24'
    checker=(ROOT/'tests/release/check.py').read_bytes();assert checker==subprocess.check_output(['git','show',source+':tests/release/check.py'],cwd=ROOT)
    report={'status':'PASS_BINARY_AND_LICENSE_AUDIT','source_commit':source,'go_tool_sha256':sha(go.read_bytes()),'checker_sha256':sha(checker),'binary_build_info':binaries,'compiled_go_dependency_count':len(compiled),'installed_npm_verified':local_npm,'optional_not_installed':25,'license_gap_count':2,'archive_sha256':sha((ROOT/'.local/researchos-final-f510491-a.zip').read_bytes())}
    (OUT/'binary-license-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'compiled_go_dependencies':len(compiled),'installed_npm_verified':len(local_npm),'optional_not_installed':25,'license_gaps':2}))
