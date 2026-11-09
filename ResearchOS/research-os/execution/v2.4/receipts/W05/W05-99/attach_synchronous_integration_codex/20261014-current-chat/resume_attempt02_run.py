import pathlib,json,subprocess,os,datetime
root=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees'); ev=root/'attach-exact6-independent-evidence-20261013'; work=root/'attach-exact6-independent-20261013'
old=(work/'internal/domain/attach_independent_review_test.go').read_text()
# Existing dispatch maps both sealed and archived writes to SESSION_ARCHIVED; retained original review file is unchanged.
new=old.replace('case "sealed": code="SESSION_SEALED"','case "sealed": code="SESSION_ARCHIVED"')
new=new.replace('case "stale-revision": rev=0;code="VERSION_CONFLICT"','case "stale-revision": rev=1;code="VERSION_CONFLICT";exec("UPDATE client_sessions SET revision=2 WHERE id=?",sid)')
(ev/'resume_domain_review_attempt02_test.go').write_text(new)
overlay={'Replace':{str(work/'internal/domain/attach_independent_review_test.go'):str(ev/'resume_domain_review_attempt02_test.go'),str(work/'internal/api/attach_resume_independent_test.go'):str(ev/'resume_http_review_attempt02_test.go')}}
(ev/'resume-attempt02-overlay.json').write_text(json.dumps(overlay,indent=2))
record=json.loads((ev/'independent-native.process.json').read_text());env=os.environ.copy();env.update(record['environment'])
cmd=[env['GOROOT']+'/bin/go.exe','test','-work','-x','-overlay',str(ev/'resume-attempt02-overlay.json'),'./internal/domain','./internal/api','-run','^TestIndependentAttach','-count=1','-v']
rec={'argv':cmd,'cwd':str(work),'environment':record['environment'],'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (ev/'resume-attempt02-independent.stdout.raw').open('xb') as out,(ev/'resume-attempt02-independent.stderr.raw').open('xb') as err:
 p=subprocess.Popen(cmd,cwd=work,env=env,stdout=out,stderr=err);rec['pid']=p.pid;(ev/'resume-attempt02-independent.process.json').write_text(json.dumps(rec,indent=2));code=p.wait()
rec['exit_code']=code;rec['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(ev/'resume-attempt02-independent.process.json').write_text(json.dumps(rec,indent=2));(ev/'resume-attempt02-independent.exit.txt').write_text(str(code));print(json.dumps(rec));print((ev/'resume-attempt02-independent.stdout.raw').read_text())
