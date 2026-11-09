M4 Source候选已构造，状态 SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING，authority=NONE。作者仍为 codex:/root/backup_regression_resources，实际thread 01a11cee-bf59-7a01-be0e-9f799f9b1084、parent Rootthread 01a11007-5233-7ca1-b71f-9e9e5ce84c98；builder作者仍是 codex:/root/native_temp_independent_review。本作者不签独立接受、不创建Root资格或执行授权。

输入为原M3 HDF/MF及Task58真实非作者CHANGES_REQUIRED决定。完整M3 Caller SHA c72ba84cde5cbbc6cc55cd25322d2faa49b34981f5fd88ce7b746275d2af336b/56282保持；新Caller SHA 85ec3da49ab65741d1f1a8a94996c55f22d3b2394959e641bb3f0bd4b694f75e/56626。exact-inverse记录三个精确原byte spans及其逆恢复SHA/bytes，全Source逆恢复等于原M3。三个span只涉及validate_peer_delivery与runtime_review_chain两逻辑函数；Root工具structured_documents和所有其他函数、身份/Source/resource/OwnedJob/TP/失败台账门逐字节不变。N仍为Path(__file__).resolve().parent，指向新包。

M3-TIME-01：wrapper投影仅新增排除wrapper-only created_utc；payload改用payload_created_utc，且该字段与所有其他payload/source/identity/resource字段仍精确绑定。时间检查为scope.created<=review.reviewed<=真实peer receipt<=payload_created_utc<=真实Root call<=真实Root output<=wrapper.created_utc<=验证时当前UTC。旧payload含created_utc、缺payload_created_utc、字段漂移、时序颠倒或future wrapper均拒绝。Root必须使用每个步骤真正产生的时间；不得为了旧M3门预填未来时间。M4没有构造任何qualification/payload/Scope/lease或Rootgrant。

M3-PEER-FINAL-02：仅在validate_peer_delivery里，先保留全部真实peer身份/metadata检查，再由已核canonical actor的removeprefix(codex:)生成固定前缀：
    Message Type: FINAL_ANSWER
    Task name: /root
    Sender: <validated actual backend author>
    Payload:
前缀必须锚定字符串开头，后续必须是一个完整strict JSON dictionary。完整plain JSON继续接受；错误前缀/任意附加文本/duplicate keys/trailing JSON及错误typed身份、operation、verdict、falsegrant、完整ref集合均拒绝。未修改Root工具stdout的structured_documents。

固定Python -I -S -B -X utf8构造revision实际exit0，37个有限新增Source检查实际exit0。时间反例仅执行从候选AST抽取的原表达式，明确为synthetic Source检查；没有模拟通过完整runtime资格或Issuer授权。60922与60970两个真实backend FINAL正文，均先按Task58原capture的完整bytes/hash/offset在固定Root原日志核对，再执行候选的peer正文解析与typed绑定表达式；两个完整plain JSON正文兼容路径亦通过。Task58 qualifying_root_binding=false原件保持，这些Source采样没有被改造成Root发行绑定。新check结果及原工具raw+binding供独立复核。

原22/45/真实身份6控件的固定receipts及原Source证据继续引用，不重跑无变化14782/14670输入。此次Python构造器因错用M3 HDF字段calling_contract_ref发生原1064：actualouter/Python1/1，其余退出NULL；candidate尚未生成。真实HDF字段为contract_ref/source_inputs_ref。旧脚本、完整IO及原header/call/output保留；新constructor revision只修该字段读取并实施已授权两逻辑修改。旧失败guard没有serialized close receipt，相关ref明确NULL；不补造，不重置失败计数。新成功构造与新增控件均保存真实closed0 receipt。

Source-inputs沿用冻结历史CP371/OW175/CM39 archive，原creation_baseline是历史来源，不是未来current4 grant。本作者未读取或持有liveCP/OW。未来Root必须基于当时实际四份current refs动态CAS，CP>=371/OW>=175；不固定372。Root后续应先取得新的非作者Source审查，再按M4精确caller/source pins重新绑定145资源review及同Rootthread Scope/资格，原M3runtime原件不改；实际注册、Go构建和产品行为仍属后续任务。

Main/Canon/旧Source/旧case/他人文件写入0，Go/Native/SQLite/TP/dispatcher/model调用0，private credential/key/owner读取0。唯一写入本M4新namespace。全有限Sourceguards closed0。封存后STOP，状态不等于独立接受或实际构建完成。

