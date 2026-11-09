from pathlib import Path
import json,hashlib
own=Path("D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\schema22_public_fixture_bridge_source_codex\\3d7d237d23244950a6d9008753e3fde9")
r=Path(r'D:/作品集/ResearchOS/research-os')
prior=r/'execution/v2.4/receipts/W05/W05-99/prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6/candidate-root/internal/domain/backup_configuration_upgrade_test.go'
s=prior.read_bytes().decode('utf-8')
a=s.index('func TestConfigurationUpgradeActiveQueueRecovery(t *testing.T) {')
setup_a=s.index('\tctx := context.Background()',a)
setup_b=s.index('\tbefore, e := upgradeRows(f.db)',setup_a)
setup=s[setup_a:setup_b]
adapted=setup.replace('svc := &ClientService{Doc: configurationSchema(t),','svc = &ClientService{Doc: historical22ProtocolSchema(t, codeRoot),').replace('configurationUpgradePort{','historical22FixturePort{').replace('configurationPublicCommand(t, f, svc, ','publicCommand(')
assert adapted!=setup and 'configurationPublicCommand' not in adapted and 'configurationSchema(t)' not in adapted
child=(own/'bridge-header.txt').read_text(encoding='utf-8')+adapted+(own/'bridge-footer.txt').read_text(encoding='utf-8')
p=own/'historical22-overlay/internal/domain/configuration_historical22_bridge_test.go';p.write_text(child,encoding='utf-8',newline='\n')
replacement='''func TestConfigurationUpgradeActiveQueueRecovery(t *testing.T) {
\topt, f, historical := configurationHistorical22UpgradeFixture(t)
\tctx := context.Background()
\tstart := historical.Commands[0].Response
\tif deref(start.Status) != "COMPLETED" {
\t\tt.Fatal(string(Bytes(start)))
\t}
\tfor _, command := range historical.Commands[1:8] {
\t\treply := command.Response
\t\tif deref(reply.Status) != "COMPLETED" {
\t\t\tt.Fatal(string(Bytes(reply)))
\t\t}
\t}
\tcancel := historical.Commands[8].Response
\tif deref(cancel.Status) != "ACKNOWLEDGED" {
\t\tt.Fatal(string(Bytes(cancel)))
\t}
'''
out=s[:a]+replacement+s[setup_b:]
next_func=out.index('\nfunc ',a+len(replacement))
part=out[a:next_func]
assert part.count('run.run["id"]')==1 and part.count('run.run["lease_epoch"]')==1
part=part.replace('run.run["id"]','historical.RunID').replace('run.run["lease_epoch"]','historical.RunEpoch')
out=out[:a]+part+out[next_func:]
q=own/'candidate-root/internal/domain/backup_configuration_upgrade_test.go';q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(out.encode('utf-8'))
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
proof={'prior_test_source':ref(prior),'setup_original_sha256':hashlib.sha256(setup.encode()).hexdigest(),'setup_adapted_sha256':hashlib.sha256(adapted.encode()).hexdigest(),'setup_inverse_exact':adapted.replace('svc = &ClientService{Doc: historical22ProtocolSchema(t, codeRoot),','svc := &ClientService{Doc: configurationSchema(t),').replace('historical22FixturePort{','configurationUpgradePort{').replace('publicCommand(','configurationPublicCommand(t, f, svc, ')==setup,'original_setup_moved_not_protocol_copied':True,'existing_FIXTURE_PHASE_injection_count':setup.count('FIXTURE_PHASE'),'source_files':[ref(p),ref(q)]}
assert proof['setup_inverse_exact']
(own/'fixture-setup-provenance.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2))

