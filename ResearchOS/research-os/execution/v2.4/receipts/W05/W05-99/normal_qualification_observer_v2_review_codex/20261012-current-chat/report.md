# Normal qualification observer V2 independent review

**REQUEST_CHANGES**. 两个 P1 请求读取阻塞、一个 P2 Run 绑定缺口。

- OBSV2-R1 P1: Producer JSON BLOB is destroyed before request parsing. Go Bytes(request) is []byte and idempotency.body is BLOB. rows() replaces bytes with a digest object, then request path asserts str. C fixture with SQL BLOB fails at line73. The consume-body JSON path has the same issue. Suggested: Decode bounded UTF-8 JSON bytes specifically for known idempotency request/consume body columns before serialization redaction. Keep arbitrary binary values hashed; preserve raw byte digest separately.

- OBSV2-R2 P1: Observer compares incompatible request hash algorithms. Core Hash(request) is sha256: plus RFC8785 canonical JSON SHA256. Observer uses unprefixed SHA256(raw stored JSON). Go struct marshaling order differs from canonical order, so adding prefix alone is insufficient. A 17-field ASCII/integer fixture stored as TEXT reaches ORIGINAL_REQUEST_HASH_MISMATCH. Suggested: Validate stored request_hash with the same strict canonical JSON/digest contract; retain original_request_body_sha256 solely as raw-byte provenance. Do not require raw-byte digest equality to semantic request hash.

- OBSV2-R3 P2: Run evidence lookup does not complete the claimed exact Run binding. The unique consumption receipt and qualification marker are checked, but profile_hash is selected without comparison; run_ref entity_type is not validated and actual domain Run rows are returned without cardinality or body task/runtime/epoch checks. A missing or contradictory Run object can still be emitted as an apparently observed original_run_id. Suggested: Require one Run with body id/project/task/runtime/lease_epoch matching the original request and qualification marker; validate run_ref type/id and marker profile_hash against original request. Keep missing/mismatch explicit instead of a success result.

只读SQLite保护、exact17字段、唯一consume和预算祖先检查可在源码确认。Goal ACTIVE适用于正常预确认；暂停/取消后的回顾观察需另行处理。Electron wait只能测量Electron；launcher未执行。private stdout/verifier stderr/native wait仍missing。真实数据库、网络、模型和产品正式验收均未触及。
