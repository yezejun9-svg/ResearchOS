# Freeze01 独立UI源码审查：NEEDS_FIX

唯一产品阻断为workbench.jsx453–459：actual send函数在等待提交/GET成功期间允许输入，迟到成功无条件清空当前草稿。两种输入（新文本、编辑后回原文）均实证失败，属于一个P2来源。需draft edit revision/lifecycle保护，而不是仅文本相等。旧freeze10pins保持。

独立UI14项：11通过、2项同源草稿失败、1项QA参数错误；独立mock HTTP/IPC/journal15项通过。QA参数错误纠正后activity窄测3项通过，首轮原始失败与原test完整copy保留。作者UI12+bridge21+旧activity7项重放全通过。

原始输出和精确命令见checks01、checks02-qa-fixture-correction。未运行真实server/Electron/Native/CLI/model、旧DB或认证内容。build不重跑，因为已存在可复现源阻断；作者Vite只作已pin的作者开发证据。真实IME/窄屏、Windows执行/权限/取消均未取得资格。

review.json含exact10 source_sha256、freeze/manifest pins、唯一origin分类与raw hash。decision=NEEDS_FIX，formal_increment=0。修复后必须freeze02再独立重验，不把旧失败改绿。
