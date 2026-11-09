# Tree diagnostic 环境修订二

状态 SOURCE_PURE_ONLY_NOT_RUN，等独立复核；旧diagnostic01、04和bundle05缓存证据不改，不重放GUI。新改动只在C runner：

- 从已通过绝对路径/正常Windows盘符形状校验的 SystemRoot 派生 SystemDrive（规范大写盘符），不继承或信任单独的 ambient/scope SystemDrive。其他显式最小环境不改。
- Electron _electron.launch 的cwd改为已mkdir的owned scope.run_root；启动argv仍绝对bundle/apps/desktop。launch-input记录electron_cwd供实际核对。

这只改变Electron cwd。Core仍由Main显式设置REPO cwd，以保留真实相对 migrations/spec依赖；本包没有改Core cwd或D产品源。Root的独立exact2产品环境修复与fresh build06由Root另行整合/验证；本包不声称sealed bundle在未来GUI后已保持完整。

helper、diagnostic_only/budget0、noOK、native owner/UTC/path/IDCANCEL等全部不变，旧源和失败不覆盖。新增8项纯env/cwd反例及Node syntax通过；只提取实际函数/launch片段并使用fake SDK调用接收options，没有import SDK、启动GUI/Core/UIA或模型。旧检查按完全相同代码引用不重跑，不作新产品接受。

Root需在独立QA后填最新实际bundle/manifest/source与fresh scope，外层exact Job监督机制不变。SystemDrive及Electron cwd的实际OS缓存效果尚未测量，不删除、容忍或从manifest排除旧未列文件。
