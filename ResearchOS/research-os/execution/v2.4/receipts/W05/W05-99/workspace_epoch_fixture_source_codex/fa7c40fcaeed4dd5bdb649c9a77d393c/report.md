# Workspace writer epoch fixture Source

结论：只修原FULL的WORKSPACE_WRITER_EPOCH单叶；Source候选已封存，authority=NONE / formal_acceptance=false，等待独立复核及Root实际。
目标：TestClientWorkspaceImportExactBytesReplayAndEpoch；原actual FULL raw2800–2804是唯一该叶run/terminal fail，2802报MISSING_FIELD:writer_epoch，原FAILED事实保留。
输入cause包用manifest.json（原包没有HDF/MF命名）；11成员指纹已核对。源report、source-pins、actualFULL完整raw与目标原事件均绑定epoch-input-facts。

## 最小夹具修订

原revPtr(0)会返回nil，DecodeEnvelope164–169在Execute前拒绝缺字段；不是一次到达STALE_WRITER_EPOCH gate的有效请求。
clientWorkspaceFixtureFor保持defaultepoch1，转入同体参数化clientWorkspaceFixtureForEpoch；原其他4Test及envelope/execute/defaultfixture helper字节不变。
只目标case通过生产MapClientSession实际映射currentepoch2/revision1。writer_client_id仍workspace-client，project/workspace仍原绑定，LeaseExpiresAt为同Session row的now+1hour，Protocol仍V2。
MapClientSession78–111验证epoch/revision>=1和writer/project等并将epoch/writer/lease一起insert；没有生产规则要求此合成currentstate中epoch<=revision。
新增Rootactual时执行的query/readback断言：同sid的epoch2、revision1、writer=b.ClientID、project=f.project、workspace=b.AuthorizedRef及futureRFC3339NanoLease。
原CONTENT_CONFLICT输入和最终正常import完整envelope明确writer_epoch=current2，negative完整envelopewriter_epoch=old1（非零且1<2），CommandID/project/session/revision仍原helper提供。
Execute931–959从同Session加载revision/epoch/client，epoch mismatch在nativeIO前拒绝；workspaceBinding73–90检查同sid/workspace及同row有效lease，未弱化任何gate。
此为synthetic当前epoch比较夹具，不是已接受的真实handoff历史。没有直接UPDATE epoch、绕过生产Map或伪造授权；不执行公共handoff。

## 原断言与范围

全文件16个原t.Fatal/Error/Skip调用、17个原assertion_or_error_if、5个Test名称及顺序完整保留；目标原7calls/7if全保留。
STALE_WRITER_EPOCH/noIO、CONTENT_CONFLICT/failed-uploadcount0、COMPLETED且nonreplay/revision2、精确storedbytes、同命令replay结果bytes与noIO、ARTIFACT journalcount1全部原字节断言保留。
默认helper其他case仍epoch1及原完整mapping体；只增加目标case前置coherence断言和正/负epoch字段。没有并吞其他FULL失败、skip、Q3/native、ledger、历史、W16或生产分支。

## 验证与交接

本轮固定Python短script指纹、PythonAST提取已pin纯词法工具、Go文本/分隔符检查；没有GoAST/compiler/gofmt/native/SQL/model/provider/private/sign/canonical执行。
Main/T4/T5/旧cause包/原FULL/Q3均只读，Root当前全局状态由Root维护，本包不复算成正式接受。原FULL计数：{"pass": 1261, "fail": 25, "skip": 4}。
source-refs、base-refs、static-checks、最小client_workspace_test.patch、完整工具IO随HDF/MF封存；新机械错误0，不reset历史failure。
实际候选行号：{"59": "return clientWorkspaceFixtureForEpoch(t, f, 1)", "64": "func clientWorkspaceFixtureForEpoch(t *testing.T, f *fixture, writerEpoch int64) (*fixture, *ClientService, *clientWorkspacePort, *WorkspaceBinding, string) {", "187": "const currentEpoch int64 = 2", "188": "const oldEpoch int64 = 1", "189": "f, svc, port, b, sid := clientWorkspaceFixtureForEpoch(t, contextFixture(t), currentEpoch)", "192": "if err := f.db.QueryRow(\"SELECT writer_epoch,revision,writer_client_id,project_id,workspace_ref,lease_expires_at FROM client_sessions WHERE id=?\", sid).Scan(&mappedEpoch, &mappedRevision, &mappedWriter, &mappedProject, &mappedWorkspace, &mappedLease); err != nil {", "197": "t.Fatalf(\"mapped current writer fixture is not coherent: epoch=%d revision=%d writer=%q project=%q workspace=%q lease_error=%v\", mappedEpoch, mappedRevision, mappedWriter, mappedProject, mappedWorkspace, leaseErr)", "201": "env.WriterEpoch = revPtr(currentEpoch)", "213": "env.WriterEpoch = revPtr(oldEpoch)", "220": "env.WriterEpoch = revPtr(currentEpoch)"}
下一步Root独立Sourcereview→fresh isolatedcomposition→actual目标叶及必要默认fixture回归→independent actualreview；未执行不得PASS。
作者完成Source封存后STOP。
