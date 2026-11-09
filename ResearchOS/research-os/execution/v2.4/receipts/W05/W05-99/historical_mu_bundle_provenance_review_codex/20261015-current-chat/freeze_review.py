import hashlib,json
from pathlib import Path

OUT=Path(__file__).resolve().parent
MAIN=Path('D:/作品集/ResearchOS/research-os')
E=MAIN/'execution/v2.4/receipts/W05/W05-99'
ROOT=E/'historical_qualification_public_provenance_codex/20261015-current-chat/attempt02'
def ref(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(name,value):
 with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
source=load(OUT/'01-source-and-build-link.json');vendor=load(OUT/'02-vendor-toolchain-boundary.json');chain=load(OUT/'03-existing-package-copy-chain.json')
original_probe=ROOT/'05-mu-source-commit-probe.json'
diagnostics=[json.loads(x) for x in (OUT/'diagnostics.jsonl').read_text(encoding='utf-8').splitlines()]
save('diagnostic-ledger.json',{'entries':diagnostics,'new_history_walk_failure_count':1,'new_failed_source_blob_reads':0,'root_original_wrong_repository_probe':ref(original_probe),'root_original_failure_preserved':True,'original_build_warning':'ignored-bare-import: third_party/mu/packages/ai/src/providers/images/register-builtins.ts excluded by sideEffects','warning_ref':source['historical_stderr_warning'],'counter_reset':False})
result={'schema':'researchos.historical-mu-bundle-provenance-review.v1','reviewer':'codex:/root/historical22_fixture_review','status':'HISTORICAL_WRAPPER_AND_ASSET_CHAIN_VERIFIED_WITH_TRANSITIVE_INPUT_CLOSURE_LIMIT','F01_overall_acceptance':'ROOT_AGGREGATION_REQUIRED','researchos_wrapper_source_commit':'292ad860f9e76cf2795d5a3010da1d114d01ff56','wrapper_sha256':'0d50cea351f325f28ca5ee377eac36833768a28be42cf48ec0e50834c0ff6517','build_script_sha256':'9411e13e59a227abf0a4c497253ccf006c4d5962a5374c1f254c05d18cd0f575','sdk_commit':'8dfebe36508ac0c2508735bb866756dab9283e74','sdk_commit_namespace':'qybaihe/mu upstream vendor; not ResearchOS source HEAD','bundle_sha256':'2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441','metadata_sha256':'ce85112575850403492a0d00a26100ff678d64f21e852af2f7530bb7a6b7613a','verified':['CP408 frozen reference -> original runtime asset manifest -> historical invocation argv/cwd/native0 -> exact Git ResearchOS wrapper and build script bytes.','Original stdout, receipt build metadata, original asset metadata and actual bundle bytes all match.','The historical build script verifies 5083 vendor files before esbuild, fixes SDK/AI 0.87.1 and esbuild 0.28.2, and records wrapper/source hash independently from SDK commit.','Historical Git vendor manifest equals current manifest; all5083 current entries match historical size/hash.','Seven existing package bundle/metadata copies, including installed normal-verifier-replacement-4f4023-20261015, match original asset hashes. Attach-to-readlane composition edge is verified through assemble-attach.py OLD_COMP; readlane-to-combined edge is verified through assemble-readlane.py OLD_HERE.','Two later chain-linked ResearchOS source worktrees retain exact old wrapper bytes. Current Main wrapper differs; current source is not substituted as the old source.'],'not_provable_from_reviewed_receipts':vendor['not_provable'],'important_boundaries':['Current rehash of vendor files proves those retained files, not historical unrecorded node_modules/esbuild binary/generated dist content.','Original runtime-assets receipt has no full transitive compilation input vector/metafile. No rebuild was performed; no fresh build is substituted for historical identity.','Native build success and exact historical artifact identity do not by themselves accept model qualification, live worker semantics, STOP safety, C migration, or formal cases.','Root COLLECTION gaps entry MU_SOURCE_COMMIT_NOT_MATCHING_BUILD_METADATA was based on querying the SDK commit in the ResearchOS repo. Preserve the native128 diagnostic, but do not treat it as missing ResearchOS wrapper source.'],'actions_for_root':['Replace the F01 wrapper-source UNKNOWN with the exact292ad wrapper/build/hash chain in this review; retain the original wrong-namespace lookup failure.','Keep full transitive build-input closure explicitly NOT_PROVABLE from these bounded receipts, unless an existing separately pinned dependency/dist/esbuild input vector is located.','Combine this source/asset identity evidence with the separately collected Core and actual staged-binding evidence before deciding F01 scope acceptance.'],'evidence':{name:ref(OUT/name) for name in ['01-source-and-build-link.json','02-vendor-toolchain-boundary.json','03-existing-package-copy-chain.json','04-exact-source-semantic-anchors.json','05-readonly-input-guards.json','diagnostic-ledger.json','diagnostics.jsonl']},'no_source_changes':True,'no_actual_db_access':True,'no_core_or_model_execution':True,'no_network_or_private_configuration':True,'formal_increment':0}
save('review.json',result)
md='''# Historical Mu bundle 来源独立复核

已找到并验证具体 ResearchOS wrapper 来源：`292ad860f9e76cf2795d5a3010da1d114d01ff56:adapters/runtime/mu/worker.mjs`。Git 原始对象为 48,557 字节，SHA256 `0d50cea351f325f28ca5ee377eac36833768a28be42cf48ec0e50834c0ff6517`，与原构建回执、build metadata 完全一致，无换行转换。同一 ResearchOS commit 的 `build.mjs` 为 4,286 字节，SHA256 `9411e13e59a227abf0a4c497253ccf006c4d5962a5374c1f254c05d18cd0f575`，也精确匹配。

原始回执位于 `runtime_assets_resource_codex/20261012-current-chat`，由 CP408 的 SHA 固定引用。历史命令使用 `C:/nvm4w/nodejs/node.exe`，从 ResearchOS 根运行 `adapters/runtime/mu/build.mjs`，在 2026-10-12 07:34:38–07:34:54 UTC 完成，native exit0。stdout、原始 build metadata、原资产文件以及七个后续包中的 bundle/metadata 均一致：bundle SHA256 `2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441`；metadata SHA256 `ce85112575850403492a0d00a26100ff678d64f21e852af2f7530bb7a6b7613a`。

`8dfebe36508ac0c2508735bb866756dab9283e74` 是 `third_party/mu` 的上游 SDK commit，不是 ResearchOS wrapper 的 commit。`build.mjs` 明确从本仓库 `worker.mjs` 取得 entryPoint/source_sha256，另从常量和 component lock 取得 mu_commit。Root 在 ResearchOS 仓库查询该 SDK commit 的 native128 失败保留，但不再作为 wrapper 来源缺失的依据。

已逐项重新核对历史 Git 中的 vendor manifest 与当前清单字节一致，5083 个文件大小/hash 全部匹配。历史 builder 在打包前检查这些文件、SDK/AI `0.87.1` 和 esbuild `0.28.2`。两个链内的后续构建 worktree 也保留了相同 wrapper 字节。包复制链中 attach composition 缺少 `old_composition` 字段，但 `assemble-attach.py` 的 `OLD_COMP` 明确指向 readlane；readlane 的 `OLD_HERE` 明确指向 combined；combined 从原 runtime-assets 目录复制固定三文件。七个现存包中包括当前 installed `normal-verifier-replacement-4f4023-20261015`。

仍为 **NOT_PROVABLE_FROM_REVIEWED_RECEIPTS** 的部分：原 runtime asset receipt 未记录完整 node_modules、esbuild 二进制及生成 dist 的历史输入闭包，也未保存 esbuild metafile。5083 清单只包含三个上游跟踪的 dist 文件，包含零个 node_modules 文件。当前版本与 vendor 文件匹配不能倒推出这些未记录依赖在历史构建时的全部字节，故不能宣称整个 bundle 已获可逐字节重建证明。本次没有重新构建 bundle。

历史构建 stderr 的 ignored-bare-import 警告保留；本审查一次 `git log` 遍历因缺失旧 tree 失败也保留。已知292ad的五个精确 Git blob读取均成功，没有恢复 Git 对象。没有修改源码、共享续跑文件、实际 DB，没有运行 Core/model、网络请求或读取私密配置。

本结论仅验证历史 wrapper/构建/资产复制链并声明输入闭包限制。F01 整体由 Root 合并 Core、staged binding 与本证据后判断；不构成 C/actual、STOP、模型资格、Main/package 或正式接受，formal increment0。
'''
with (OUT/'review.md').open('x',encoding='utf-8') as f:f.write(md)
manifest={'schema':'researchos.historical-mu-provenance-review-manifest.v1','status':result['status'],'formal_increment':0,'files':[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='evidence-manifest.json']}
save('evidence-manifest.json',manifest)
assert all(ref(item['path'])==item for item in manifest['files'])
print(json.dumps({'review':ref(OUT/'review.json'),'manifest':ref(OUT/'evidence-manifest.json'),'manifest_entries':len(manifest['files']),'drift':0},ensure_ascii=False))
