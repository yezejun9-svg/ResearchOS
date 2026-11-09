from review_driver import *
git('014-sparse-ops',['sparse-checkout','add','/ops/experiment_sandbox/','/ops/supervisor/'])
run('015-core-build',[str(MAIN/'.local/tools/go1.27.1/go/bin/go.exe'),'build','-o',str(ASCII/'control.exe'),'./apps/control'],env={'GOMODCACHE':str(MAIN/'.local/tools/gopath/pkg/mod'),'GOTOOLCHAIN':'local','GOPROXY':'off'})
print('Core built')
