from pathlib import Path
import hashlib,subprocess,sys
wt=Path(sys.argv[1]).resolve(); rec=Path(sys.argv[2]).resolve()
paths=[
'internal/domain/backup_prepared_abandonment_handoff.go',
'internal/domain/backup_prepared_abandonment_upgrade.go',
'internal/domain/backup_prepared_abandonment_upgrade_windows.go',
]
patch=subprocess.check_output(['git','-C',str(wt),'diff','--binary','--',*paths])
(rec/'012-before-reconstruct.patch.raw').write_bytes(patch)
def rep(s,a,b):
    n=s.count(a)
    assert n==1,(n,a[:80])
    return s.replace(a,b,1)
def base(p): return subprocess.check_output(['git','-C',str(wt),'show','HEAD:'+p]).decode('utf-8')
a=base(paths[0])
a=rep(a,'return upgradePreparedAbandonmentBackup(ctx, handoff, preparedUpgradeConcreteVerifier())','return RestoreReport{Status: "FAILED"}, fmt.Errorf("UPGRADE_SOURCE_LEASE_REQUIRED")')
a=rep(a,'    lease, err := acquirePreparedUpgradeRootLease(filepath.Dir(opt.Source))','    if opt.sourceLease != nil {\n        if err := opt.sourceLease.Check(filepath.Dir(opt.Source), opt.Source); err != nil { return report, err }\n    }\n    lease, err := acquirePreparedUpgradeRootLease(filepath.Dir(opt.Source), opt.Source, opt.sourceLease)')
b=base(paths[1]); b=rep(b,'lease, err := acquirePreparedUpgradeRootLease(filepath.Dir(opt.Source))','lease, err := acquirePreparedUpgradeRootLease(filepath.Dir(opt.Source), opt.Source, opt.sourceLease)')
c=base(paths[2])
old='''type preparedUpgradeRootLease struct { native *runtimeadapter.DataRootLease }

func acquirePreparedUpgradeRootLease(root string) (*preparedUpgradeRootLease, error) {
    lease, err := runtimeadapter.AcquireDataRootLease(root)
    if err != nil { return nil, err }
    return &preparedUpgradeRootLease{native: lease}, nil
}
func (l *preparedUpgradeRootLease) Check() error {
    if l == nil || l.native == nil || !l.native.Held() {
        return fmt.Errorf("PREPARED_UPGRADE_DATA_ROOT_LEASE_REQUIRED")
    }
    return nil
}
func (l *preparedUpgradeRootLease) Close() error {
    if l == nil { return nil }
    return l.native.Close()
}'''
new='''type preparedUpgradeRootLease struct {
    native *runtimeadapter.DataRootLease
    inherited *backupSourceLease
    root, source string
    closed bool
}

func acquirePreparedUpgradeRootLease(root, source string, inherited *backupSourceLease) (*preparedUpgradeRootLease, error) {
    if inherited != nil {
        if err := inherited.Check(root, source); err != nil { return nil, err }
        return &preparedUpgradeRootLease{inherited: inherited, root: root, source: source}, nil
    }
    lease, err := runtimeadapter.AcquireDataRootLease(root)
    if err != nil { return nil, err }
    return &preparedUpgradeRootLease{native: lease}, nil
}
func (l *preparedUpgradeRootLease) Check() error {
    if l == nil || l.closed { return fmt.Errorf("PREPARED_UPGRADE_DATA_ROOT_LEASE_REQUIRED") }
    if l.inherited != nil { return l.inherited.Check(l.root, l.source) }
    if l.native == nil || !l.native.Held() { return fmt.Errorf("PREPARED_UPGRADE_DATA_ROOT_LEASE_REQUIRED") }
    return nil
}
func (l *preparedUpgradeRootLease) Close() error {
    if l == nil || l.closed { return nil }
    l.closed = true
    if l.inherited != nil { return nil }
    if l.native == nil { return fmt.Errorf("PREPARED_UPGRADE_DATA_ROOT_LEASE_REQUIRED") }
    return l.native.Close()
}'''
c=rep(c,old,new)
for p,s in zip(paths,(a,b,c)):
    target=wt/p; target.write_bytes(s.encode('utf-8'))
    print(p,hashlib.sha256(target.read_bytes()).hexdigest())
