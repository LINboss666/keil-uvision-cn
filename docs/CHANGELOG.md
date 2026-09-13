# CHANGELOG

格式：日期 / 阶段 / 提交 / 修改内容 / 涉及 Resource ID / 新增翻译条目 / 已知问题 / 测试状态。

## 2026-09-13 — PHASE 1B2.1a（首批 Dialog 烟雾测试：100/129/511；本地 UV4_CN_1B2_1A_TEST.exe 已构建，待审核）

- **feat: add dialog translation applier with semantic allowlist**
  - `extract_resources.py` 新增 `dialog_semantic_diff()`：除 manifest 指定的
    dialog.title.value / control[index].title.value（string kind）外，
    kind/dlgVer/signature/helpID/style/exStyle/cDlgItems/rect/menu/windowClass/
    font/ID/class/creation size+hash 一律必须 identical；trailing 剥离后由
    allocation padding 规则单独校验（纯 00、长度精确）。
  - `apply_translation.py` 支持 DIALOG 行：locator =
    (ResourceID, LANGID, control_index) + **ID/Class/Original 三重交叉校验**；
    首轮仅 BUTTON/STATIC + string title；logical ≤ 原分配（否则
    RESOURCE_TOO_LARGE）；allocation padding 纯 00 机械生成。
  - `verify.py` 接受 manifest v3。
- **feat: add phase 1b2.1a dialog translations**
  - CSV 扩列 `CtlID`/`CtlClass`，增至 **251 条（STRING 152 + MENU 79 + DIALOG 20）**；
    本轮新增 Dialog 文本 19 条：Dialog 100（About：标题 + OK，版权/版本/授权
    文本保持原文）、129（Targets：标题 + 6 控件）、511（Batch Setup：标题 + 10 控件）；
    原文含 `&` 保留原助记键字母，原文无 `&` 不加助记键。
- **docs: add 1b2.1a candidate report and validation**
  - `docs/DIALOG_TRANSLATION_1B2_1A.md`：四候选考察（100/129/511 入选，
    465 暂缓）、逐控件映射表、Serialized Size/Delta/Fits（全部实测序列化）、
    locator/助记键/RESOURCE_TOO_LARGE 评估。
- **涉及 Resource ID**：RT_DIALOG 100/129/511（1033）—— 其余 **243 个
  bit-identical**；RT_STRING/RT_MENU 沿用 1B1.2（本轮零新增）；
  .rdata/.text/RT_240/DLL 零改动。
- **新增翻译条目**：20（19 条 Dialog 文本 + CSV 中 1 条为 title 与 ctl 复计数勘误……
  以 CSV 实际行数 251 为准：本轮净增 20 行 DIALOG）。
- **守卫实录**：locator 拦截 2 次 Control ID 转录错误（511 ctl:4 Clean 1864→1863、
  ctl:5 Select All 1865→1864）；511 ctl:5/ctl:6 同 ID 1865（Keil 原始资源如此）
  —— 按 control_index 定位不受影响。
- **测试状态**：DIALOG-1..9 **38/38**（新增语义白名单/allocation padding/
  非 manifest 变化检测/RESOURCE_TOO_LARGE 条件断言）；verify --manifest PASS
  （changed 9465B / 6535 段 / allowed=34 / non_target=0）；243 个未改 Dialog
  bit-identical；.rdata SHA256 逐位一致；签名 Valid → HashMismatch（预期）；
  自测 7/7。**GUI 测试 ⛔ 未执行**（等 GPT 批准后用户手动测试）。
- **产物**：`output/UV4_CN_1B2_1A_TEST.exe`
  （SHA256 `8ea6b4b339b29da66d105fcd0536334783528419adc0dd23442403b4b31b6cfc`，
  本地 only，未提交、未运行）；`output/uv4_cn_1b2_1a_manifest.json`。
- **Git**：tag `v0.1-analysis` 不动；无 EXE/DLL/binary dump 入库。

## 2026-09-13 — PHASE 1B2.0b（落地漏提交的语义快照加硬 + 字段规范对齐；零翻译零 EXE）

- **事故与根因（GPT 审核 A/B/C 项回答）**：
  - A：1B2.0a 的 "25/25 PASS" 是在**未提交的工作区**执行的 —— 加硬版
    `dialog_semantic_snapshot()` 当时只存在于工作区；
  - B：commit 8ccbbe5 仅 `git add tests/test_dialog_codec.py`，**漏暂存**
    `scripts/extract_resources.py` 的快照加硬修改 → HEAD 上 DIALOG-4 必然
    KeyError（HEAD 仍访问 `cb_word`）；
  - C：push 未覆盖任何内容（远端 == 本地 HEAD == b397842），纯属漏暂存。
- **fix: land hardened dialog semantic snapshot (missed from 1b2.0a)**
  - 落地加硬版快照并按审核字段规范对齐：creation 统一为
    `{size_bytes|extra_count, creation_data_len, creation_data_sha256}`；
    控件新增扁平字段 `creation_size_bytes` / `creation_extra_count`
    （防字段改名静默回归的显式绑定）；
  - 快照覆盖：kind / dlgVer / signature / helpID / style / exStyle / cDlgItems /
    rect / menu / windowClass / title / font / 逐控件全字段 / trailing 长度与 SHA256。
  - 新增 `.gitattributes`（*.py/*.md/*.csv/*.json → LF）：根治上轮
    extract_resources.py 整文件 CRLF/LF churn（本提交含该一次性归一；
    真实内容差异 `git diff --ignore-cr-at-eol` = 30/7 行）。
- **fix: bake gui addendum into dynamic mapping generator**
  - 修复回归隐患：mapper 重新生成 `DYNAMIC_MENU_MAPPING.md` 时会覆盖事后追加的
    "1B1 GUI 实测补充" 附录 —— 现将附录以 `ADDENDUM_LINES` 固化进生成器
    （ADDENDUM_LINES 随文档自动再生，不再丢失）。
- **test: add snapshot creation-field regression asserts**
  - DIALOG-4/5 新增显式断言：`creation_size_bytes == 6`、
    `creation_data_sha256 == sha256(payload)`、`creation_data_len`、
    `dlgVer==1`、`signature==0xFFFF`、dialog/control helpID、`extraCount==5`。
- **docs: record phase 1b2.0b validation stdout**
  - TEST_REPORT 收录加硬版入库后的**真实 stdout**（29/29）。
- **涉及 Resource ID / 新增翻译条目**：无（**Translations Added = 0**，
  **Binary Modified = NO**，keil_translation.csv 未改动，未生成任何 EXE）。
- **测试状态**：DIALOG-1..8 **29/29 通过**（含新增防回归断言）；
  round-trip **52/52 std + 194/194 ex = 246/246**；自测 VERIFY-1..6 7/7；
  原版 UV4.exe SHA256 复验未动（428baf13…）。
- **已知问题**：仓库遗留一个 CRLF→LF 一次性归一（本提交内完成，
  `.gitattributes` 防复发）；无其他新增。
- **Git**：tag `v0.1-analysis` 不动；无 EXE/DLL/binary dump 入库。

## 2026-09-13 — PHASE 1B2.0a（dialog codec correctness hardening；纯 codec/测试/文档，零修改零翻译）

- **fix: correct standard dialog creation-data byte semantics**
  - 修正 STANDARD DLGITEMTEMPLATE creation-data 语义：首 WORD S 非零时
    **S 为总字节数且包含 size WORD 自身**（payload = buf[pos+2 : pos+S]，
    消耗 S 字节；非零时要求 S >= 2），废除错误的 `S * 2` WORD 计数；
    字段由 `cb_word` 更名 `size_bytes`；非零时 S < 2 或越界 → 解析报错。
  - 两种格式 size 语义保持独立：EXTENDED extraCount 仍为"其后字节数"（不含字段）。
  - 控件 AST 新增 `offset`（blob 内起始偏移，用于对齐断言；序列化不依赖）。
- **feat: make dialog serializer translation-alignment aware**
  - 两个 serializer 均改为**翻译感知对齐**：原 pad 长度 == 当前所需 DWORD 对齐
    时原样复用（无损 round-trip 不变），文本长度变化时按当前位置机械生成
    `b"\x00" * required`（`required = (-len(out)) & 3`），禁止错长度旧 pad；
  - serializer 一致性拒绝：cDlgItems != controls 数量、EXTENDED
    extraCount != creation data 字节数、STANDARD size_bytes != len(payload)+2
    或非零但 < 2 → 一律 ValueError 拒绝。
- **test: harden dialog semantic mutation guards**（tests/test_dialog_codec.py，
  **25/25 通过**）
  - DIALOG-4 扩展：std 合成 fixture 两组 —— size_bytes=6/payload=4 与
    **odd size_bytes=7/payload=5**（验证奇数尾部后下一控件仍 DWORD 对齐）；
  - DIALOG-5 重构：ex fixture c1 无 creation（标题奇偶驱动 c2 pad 0↔2）、
    c2 extraCount=5（ordinal title + nonzero creation data）；
  - DIALOG-6 保留：破坏字段 → 语义验证器发现；
  - **DIALOG-7 新增（对齐突变）**：std+ex 各做标题奇偶突变
    （**0-byte pad → 2-byte pad 与 2-byte → 0-byte 均覆盖**），
    突变后全部控件 offset % 4 == 0，且除 title/text 外语义字段未变化；
  - **DIALOG-8 新增（语义破坏守卫，8 项）**：dialog helpID 改 1 bit /
    signature 改变 / cDlgItems 不一致（serializer 拒绝）/ control exStyle 改变 /
    creation data 同长度改 1 字节 / extraCount 与数据不一致（serializer 拒绝）/
    std size_bytes 与 payload 不一致（serializer 拒绝）/ trailing 字节变化
    → 全部 FAIL 或拒绝。
- **docs: extend dialog slack inventory**
  - `DIALOG_INVENTORY.md` 新增 trailing 统计：**246 个对话框 trailing 全为 0**
    （无任何尾部 slack）→ 未来 Dialog 文本变长时**没有可消耗的尾部空间**，
    整块大小约束（RESOURCE_TOO_LARGE）同样适用于 Dialog。
  - 语义快照升级：纳入 kind/dlgVer/signature/helpID/cDlgItems/逐控件
    creation size 字段 + 内容 SHA256（同长度单字节变化可发现）/
    trailing 长度与哈希。
- **docs: mark 1b1.2 gui test executed**（41f4573，审核第 0 项）。
- **涉及 Resource ID / 新增翻译条目**：无（纯 codec/测试/文档；**Translations Added = 0**，
  **Binary Modified = NO**，未生成任何 EXE，keil_translation.csv 未改动）。
- **测试状态**：DIALOG-1..8 25/25；真实 gate 重新执行 **52/52 std + 194/194 ex =
  246/246 byte-identical**（语义修复后与修复前一致 —— 符合预期，因 UV4
  nonzero creation data = 0）；自测 VERIFY-1..6 7/7；原版 UV4.exe 未动。
- **已知问题**：无新增。STANDARD creation data 字节语义现按审核指定实现
  （S 含 size WORD 自身），并有两组合成 fixture 锁定（含 odd payload 对齐路径）。
- **Git**：tag `v0.1-analysis` 不动；无 EXE/DLL/binary dump 入库。

## 2026-09-13 — PHASE 1B2.0（LOSSLESS RT_DIALOG CODEC；只调查不翻译，零修改）

- **fix: make dialog parser lossless**
  - `extract_resources.py` 新增无损 AST 解析：`parse_dialog_ast()`（std/ex 双格式）；
    sz_Or_Ord 升级为结构化 `{kind: none|ordinal|string, value, display}`，
    **不再丢失 ordinal class atom**（display 仅作展示）；
    补齐此前丢失的控件 exStyle 与 creation data；
    **alignment padding 原样捕获**（`pad_before` / `trailing`，不假设全零）。
  - STANDARD creation data 语义（按 Windows 标准）：首 WORD S 非零时 S 包含
    size WORD 自身（总消耗 S*2 字节）；EXTENDED extraCount 仅为其后字节数。
    两种格式不混用；UV4 样本 nonzero creation data = 0（std/ex 均无），
    语义由合成 fixture 锁定。
  - 旧分析视图 `parse_dialog_template()` 重写为 AST 投影（输出形状兼容，
    map_dynamic_strings 等既有消费方回归通过）。
- **feat: add standard and extended dialog serializers**
  - `serialize_dialog_ast()`：从 lossless AST 完整重序列化（std/ex 各自实现，
    禁止 raw search/replace / hex patch）。
  - `dialog_semantic_snapshot()` / `compare_semantic_snapshots()`：结构语义快照
    （Dialog: style/exStyle/rect/menu/windowClass/title/font/控件数；
    Control: helpID/style/exStyle/rect/id/class/title/creation 长度）——
    后续正式翻译时只允许 Dialog title / Control title(text) 变化。
- **test: add 246-dialog round-trip gate**
  - `tests/test_dialog_codec.py`（DIALOG-1..6，10/10 断言通过）：
    ① parse 246/246；② serialize 246/246；③ **byte-identical 246/246**
    （std 52/52 + ex 194/194，含 first-diff/字节数/hexdump mismatch 报告）；
    ④ Standard 合成 fixture（string/ordinal class、string/ordinal title、
    nonzero creation data）round-trip；⑤ Extended 合成 fixture（helpID/exStyle/
    DS_SETFONT/weight/italic/charset/ordinal+string/nonzero extraCount）round-trip；
    ⑥ 故意破坏字段 → 语义验证器必须发现（实测捕获 style 位翻转 + 标题篡改）。
- **docs: add dialog resource inventory**
  - `scripts/dialog_inventory.py` + `docs/DIALOG_INVENTORY.md`（脚本自动生成，
    baseline SHA256 绑定）：RT_DIALOG total 246（Standard 52 / Extended 194），
    LANGID {1033:218, 2057:24, 9:1, 1031:2, 0x2000:1}，controls 3389，
    DS_SETFONT 246 / DS_SHELLFONT 62，dialogs with menu 0 / custom windowClass 0，
    ordinal 控件类 3327 / string 62，nonzero creation data 0，parse warnings 0，
    round-trip 246/246；并列出 About/Target/Device/Output/C51/C251 等可识别
    重要 Dialog。
- **docs: mark 1b1.2 gui test executed**：TEST_REPORT 中 1B1.2 GUI 行由
  "⛔ 未执行" 修正为 "✅ 已执行（见 PHASE 1B1 最终 GUI 验证）"（审核第 0 项）。
- **涉及 Resource ID / 新增翻译条目**：无（本阶段只调查，**零修改、零翻译、
  未生成任何汉化 EXE**）。
- **测试状态**：DIALOG-1..6 10/10；自测回归 VERIFY-1..6 7/7；mapper 回归 exit=0；
  原版 UV4.exe SHA256 复验未动（428baf13…）。
- **已知问题**：无。STANDARD creation data "size 含 size WORD 自身" 语义按审核
  要求实现并由合成 fixture 锁定；UV4 样本无 nonzero creation data，
  该语义无法用本样本经验性区分（已如实记录）。
- **Git**：tag `v0.1-analysis` 不动；无 EXE/DLL/binary dump 入库。

## 2026-09-13 — PHASE 1B1 FINAL VALIDATION（用户真机 GUI 验证 PASS；1B1 关闭）

- **修改内容**：仅文档（TEST_REPORT / CHANGELOG / README / DYNAMIC_MENU_MAPPING 附录），
  **不改源码、不改翻译、不生成新 EXE**。
- **用户真机 GUI 验证**（1B1.2 构建版 `UV4_CN_1B1_2_TEST.exe`）：
  - Project 主菜单：PASS/PARTIAL —— `新建 µVision 工程...`、`停止编译` 生效，
    Build/Rebuild/Batch Build 中文正常；仍英文 `Options for File/Target...`、
    `Remove File ...`、`Translate <filepath> ...`（动态文本，不视为 patch 失败）。
  - Flash 菜单：PASS —— `擦除` 生效，Download 保持中文。
  - Project Window 右键（Target/Group/File）：PARTIAL BY DESIGN —— 结构正常、
    Build/Rebuild 类中文；`Options for ...`/`Add Group`/`Manage Project Items`/
    `Open Map File`/`Open Build Log`/`Show Include File Dependencies` 等仍英文
    （context menu 按当前对象动态适配）。
  - Editor Context Menu：结构 PASS；`大纲/高级` 中文；Split Window horizontally、
    Toggle Header/Code File、Go To/References 家族、断点/书签、Undo/Redo/Cut/Copy/
    Paste/Select All 仍英文 —— resource-vs-GUI behavior strongly supports runtime
    command-UI text replacement, consistent with MFC ON_UPDATE_COMMAND_UI /
    CCmdUI::SetText mechanism（不声称具体 .rdata 地址已证明传入 SetText）。
  - Build 回归：PASS（V6.24，`rt-thread.axf`，0 Error / 0 Warning）。
- **特殊剩余项**：`Refresh Source Browser View`（RT_STRING 181 已译仍英文）→
  记录 `unresolved runtime source / runtime override likely`，不在 1B1 深挖。
- **最终结论**：PHASE 1B1 PASS — RESOURCE-LEVEL COMPLETE — COVERAGE PARTIAL BY
  DESIGN；.rdata UNCHANGED；无崩溃/乱码/菜单结构损坏/command ID 异常/Build 异常。
  剩余英文接受；更高覆盖率走 PHASE 2 — EXPERIMENTAL RDATA LOCALIZATION（未批准）。
- **涉及 Resource ID / 新增翻译条目**：无（仅文档）。
- **Git**：tag `v0.1-analysis` 不动；无二进制入库。

## 2026-09-13 — PHASE 1B1.2（resource-only menu completion；本地 UV4_CN_1B1_2_TEST.exe 已构建，待审核）

- **feat: validate command prompt segment structure**
  - `text_validators.py` 新增 prompt 结构门禁：含 `\n` 的 STRING entry 必须整条处理，
    `original_segments == chinese_segments`（分段数不一致 → FAIL）；
    printf token / `\t` 快捷键 / 助记键校验继续全量执行。
- **feat: complete resource-backed dynamic menu translations**
  - CSV 增至 **231 条（STRING 152 + MENU 79，LANGID 1033）**，1B1.2 新增 44 条：
    - RT_STRING 21 条：159/162/164/167/744/770/771/104/181、20628–20633
      （含 20632 `&Delete\tDelete`）、command prompt **57634/57635/57637/57642/
      57643/57644 整条处理**（2 段结构完整保留）；
    - RT_MENU 23 项（仅 GUI mapping 确认路径）：MENU 592 ×3、624 ×5、
      191/800 ×4+4（DbWinMenu 断点/书签/Copy）、22565 ×6（MFC 隐藏编辑弹出）、400 ×1。
- **fix: report raw evidence offsets as file offsets**
  - `map_dynamic_strings.py` RAW 证据显示由 `@.rdata+0x…` 修正为
    `@file+0x… [section]`（语义正确化，不影响分类），映射文档重新生成。
- **涉及 Resource ID**：RT_STRING 22 块（8/9/10/11/31/32/41/42/43/44/45/46/47/48/49/50/51/
  3841/1290/3603 等其中 22 个）+ RT_MENU 143/1200/1205/592/624/191/800/22565/400
  共 9 个（均 1033）。**.rdata/.text/.data/.reloc/证书表/RT_DIALOG/RT_240/
  LANGID 9/1031/0x2000/1041 零改动。**
- **新增翻译条目**：44（累计 231）。
- **已知问题**：无新增。守卫实录：①3 条"原文无助记键误加 (&X)"被拦截修正；
  ②MENU 191 助记键冲突被拦截（0/8 原文助记键 B，修正为 `(&B)` 保持原字母）。
- **测试状态**：apply 语义验证全过；`verify --manifest` PASS
  （changed_byte_count=8168 / changed_ranges=5756 / allowed=31 /
  **non_target_resource_changes=0**）；**.rdata SHA256 逐位一致**
  （`7e5438f7…f912`）；自测 7/7；GUI 测试 ⛔ 未执行（等审核后用户手动测试）。
- **产物**：`output/UV4_CN_1B1_2_TEST.exe`
  （SHA256 `b67768e77a087603188771da8a793e7824e95f0837c50f18fefe8581fe24cbf6`，
  本地 only，未提交、未运行）；`output/uv4_cn_1b1_2_manifest.json`。
- **预期管理**：不保证所有英文消失 —— 1B1.2 目标是补齐资源层可修复项；
  GUI 测试中若某项翻译了全部 RT_STRING/RT_MENU 来源后仍显示英文，
  记录 `runtime override likely`（.rdata exact/template evidence 存在者保留英文）。

## 2026-09-13 — PHASE 1B1.1a（mapping 工具加固；纯只读，零修改）

- **fix: make dynamic source classification reproducible**
  - `map_dynamic_strings.py` 重构：全部命中改为**结构化证据**
    `{source_type, section, encoding, offset, resource_id, lang, item_path,
    command_id, text, match_type}`；`classify()` 基于**完整证据集合**自动推导
    （raw .rdata 证据正式纳入分类），新增"资源即模板"反向匹配
    （捕获 `%sptions for Target '%s'%s%s` 类多参数复用模板）与
    contains 降级标注（A/B [contains]）。
  - `docs/DYNAMIC_MENU_MAPPING.md` 改为**脚本全自动生成**：29 条 GUI 观察文本
    的分类全部由脚本自动得出（含 D .rdata 硬编码(ANSI) 10 条），**人工覆盖 = 0**，
    重新运行即可复现。
- **fix: bind dynamic mapping to UV4 baseline**
  - 增加 baseline SHA256 守卫：输入文件必须等于 µVision 5.43.1.0 固定基线
    （`428baf13…c42f89`），否则 FAIL 非零退出并提示"版本不匹配，需要重新执行
    PHASE 0"；已用翻转字节的临时副本实测拒绝路径（未产出任何文档）。
- **docs: align dynamic mapping wording with evidence**
  - 措辞修正：不声称"MFC 动态覆盖已证实 / 具体 .rdata 地址已证明传给
    CCmdUI::SetText"，统一表述为"**运行时动态文本覆盖假设获得强证据支持，
    且行为与 MFC CCmdUI update mechanism 一致**"；可证明的仅为
    A（GUI 最终文本与静态资源不完全一致）/ B（.rdata 存在完全匹配的
    ANSI literal / format template）/ C（MFC 官方允许该动态机制）。
- **涉及 Resource ID / 新增翻译条目**：无（纯调查工具与文档，零修改、零产物）。
- **测试状态**：脚本 exit=0；29/29 自动分类；守卫拒绝路径实测通过
  （翻转 .rdata 1 字节的临时副本 → 非零退出 + 正确提示，无文档产出）。
- **Git**：tag `v0.1-analysis` 不动；无二进制入库。

## 2026-09-13 — PHASE 1B1.1（运行时菜单文本来源调查；**纯只读，零修改**）

- **feat: add dynamic menu text source mapper**
  - 新增 `scripts/map_dynamic_strings.py`：对 GUI 观察文本做六路来源搜索
    （RT_STRING / RT_MENU / RT_DIALOG 只查 / RT_240 / .rdata UTF-16 / .rdata ANSI），
    并做 command ID → 同 ID RT_STRING → RT_ACCELERATOR 关联分析。
- **docs: map runtime-generated menu text sources**
  - 新增 `docs/DYNAMIC_MENU_MAPPING.md`：29 条 GUI 观察文本的来源映射表 +
    Command ID 映射表。
  - **运行时动态文本覆盖假设获得强证据支持，且行为与 MFC CCmdUI update mechanism
    一致**，三种来源机制：① 隐藏/未覆盖菜单资源
    （MENU 22565 'Popups' 编辑命令骨架、191/800 'DbWinMenu' 编辑器右键真身、
    592/624 工程树组/根上下文 —— 1B1 未覆盖）；② LoadString/prompt 第二段
    （159/744/164/167/104/181/5763x 等，1B1 未译）；③ .rdata 中存在与 GUI 完全
    一致的 ANSI literal / format template（@0x7C0790-0x7C0AA8：Go To
    Definition/References of '%s' 家族、Split Window horizontally、
    Toggle Header/Code File、断点两项等 —— 按红线不可改）。
  - **1B1 GUI 结果入档**：写入机制/主菜单/标签右键 PASS；Project Tree 与编辑器
    右键 PARTIAL（缺口全部归因到上述机制）；无崩溃/乱码/结构损坏/ID 异常。
- **涉及 Resource ID / 新增翻译条目**：无（纯调查，零修改、零产物）。
- **测试状态**：不适用（静态调查）；`docs/DYNAMIC_MENU_MAPPING.md` 为唯一交付物，
  另含 1B1.2 候选清单（RT_STRING 159/162/164/167/744/770/771/104/181/2062x/5763x +
  RT_MENU 592/624/191/800/22565/400）与 .rdata 不可覆盖项清单，均**未执行**。
- **Git**：tag `v0.1-analysis` 不动；无二进制入库。

## 2026-09-13 — PHASE 1B1（RT_MENU + 补充 RT_STRING；本地 UV4_CN_1B1_TEST.exe 已构建，待审核）

- **feat: add byte-identical RT_MENU serializer**
  - `serialize_menu_template()`：与 `parse_menu_template()` 严格互逆（仅 version 0，
    对 version 1 明确拒绝）；写入前对全部 RT_MENU 执行 parse → serialize →
    byte-identical 门禁，**40/40 通过**，任一失败即 STOP。
- **test: add RT_MENU round-trip regression tests**
  - `tests/test_selftest.py` 新增 VERIFY-6；自测 **7/7 通过**。
- **feat: extend manifest verifier to RT_MENU payloads**
  - `verify.py` 白名单从"仅 RT_STRING 块"升级为**通用资源范围**
    (`resource_type` / `resource_id` / `lang`)；范围仍一律由 ORIGINAL 资源树
    重新推导，不信任 manifest 写入的 offset；manifest v2。
- **feat: add mnemonic/format validators and menu applier support**
  - 新增 `scripts/text_validators.py`：printf 格式 token 完整解析
    （flags/width/precision/length modifier/conversion，含 `%.*s`、`%%`、`%lld` 等），
    Original/Chinese token 序列必须逐个一致；`\t` 后快捷键文本逐字一致
    （`Ctrl+O → Ctrl+P` 直接 FAIL）；助记键规则（`&&` 字面、禁止悬空 `&`、
    数量一致、字母变更必须在 Notes 记录）；同级助记键冲突 before/after 比对。
  - `apply_translation.py` v2：支持 MENU 行（ItemRef=路径寻址）、菜单 round-trip
    门禁、菜单语义树 diff（command ID / flags / 树形 / 数量 / header_offset）、
    同级冲突检测；Original 逐条与资源实际文本比对。
- **feat: add phase 1b1 menu translations**
  - CSV 扩列 `ItemRef`（STRING=StringID 数字，MENU=`0/2` 式路径）；
    **187 条（STRING 131 + MENU 56，全部 LANGID 1033）**：
    用户截图清单全覆盖（Edit 的撤销/重做/剪切/复制/粘贴/导航/书签/查找替换/
    大纲/高级/配置；View 的工具栏与各窗口；Project 的导入/导出/管理/批量编译；
    Tools/Help），外加工程窗口右键（MENU 143，15 项）、编辑器右键（MENU 1200，16 项）、
    编辑器标签右键（MENU 1205，25 项）。隐藏/internal 项（如弹出占位名
    `TemplateViewMenu`）不翻译。
- **涉及 Resource ID**：RT_STRING blocks 8/9/10/11/31/32/41/42/43/44/45/46/47/48/49/50/51/3841
  + RT_MENU 143/1200/1205（共 21 个资源，均 LANGID 1033）。
  RT_DIALOG / RT_240 / .rdata / 头部 / 证书表 / LANGID 9 / 1031 / 0x2000 / 1041 **零改动**。
- **新增翻译条目**：187 条（1A 存量 43 + 1B1 新增 144）。
- **已知问题**：无新增。守卫实录：applier 拦截 1 次 MENU 路径转录错误
  （0/1/3 与 0/1/4 抄串）；block 3841 整块超长 +2 字节 → 缩短措辞解决。
- **测试状态**：语义验证全过；`verify --manifest` PASS（changed_byte_count=6220 /
  changed_ranges=4414 / allowed=21 / **non_target_resource_changes=0**）；
  重扫描抽查通过（40 菜单/246 对话框/5 加速键不变）；签名 Valid → HashMismatch（预期）；
  GUI 测试 ⛔ 未执行（等审核后用户手动测试）。
- **产物**：`output/UV4_CN_1B1_TEST.exe`（SHA256 `5b2f421d02107e6c2509f45ed0f7bd5cbcd7530c7d8ee1bd9db2c2d6c8b21226`，
  本地 only，未提交、未运行）；`output/uv4_cn_1b1_manifest.json`。

## 2026-09-13 — PHASE 1A FINAL VALIDATION（用户真机测试 PASS）

- **修改内容**：仅文档（TEST_REPORT / CHANGELOG / README），代码与翻译数据零改动。
- **用户真机测试**（测试执行人：LMX 本人；Agent 未参与执行）：
  - 环境：`UV4_CN_TEST.exe` + NS800 RT-Thread 工程 `project.uvprojx`（target `rt-thread`）
    + ArmClang V6.24 + 真实硬件 NS800RT7P65D + CMSIS-DAP/DAPLink。
  - GUI：启动/加载工程正常；中文顶层菜单（文件/编辑/视图/工程/Flash/调试/外设/工具/
    SVCS/窗口/帮助）显示正常，无乱码、无崩溃、无明显布局异常；Options for Target 正常打开。
  - Build：`Build target 'rt-thread'`，0 Error / 0 Warning，生成 `.\build\rt-thread.axf`。
  - Flash：CMSIS-DAP 下 Erase Done → Programming Done → **Verify OK** → Flash Load finished。
  - Debug：Ctrl+F5 进入/退出、F5 Run、Stop、F11 Step、F10 Step Over、Registers / Memory /
    Watch / Call Stack + Locals / Disassembly、源码/PC 位置显示 —— 全部正常。
- **结论**：PHASE 1A **FUNCTIONAL TEST PASSED** —— ✅ IMPLEMENTED / ✅ STATIC VERIFIED /
  ✅ USER HARDWARE TESTED / ✅ PASSED。未发现汉化 RT_STRING 修改导致 IDE 崩溃、
  构建链异常、Flash 异常、Debugger 异常、工程损坏。
- **涉及 Resource ID / 新增翻译条目**：无（本阶段仅文档）。
- **如实记录的保留项**：TEST 3/5/8/9/14/15 用户报告未单独列出（矩阵中标注 ➖）；
  严格 A/B 编译一致性对比未执行（1B 前可选补充；间接证据：0E/0W + Flash Verify OK）。
- **Git**：tag `v0.1-analysis` 不动；无任何 EXE/DLL/二进制入库。

## 2026-09-13 — PHASE 1A（RT_STRING 基础汉化；本地 UV4_CN_TEST.exe 已构建，待审核）

- **feat: enforce 16-entry contract in string table serializer**
  - `serialize_string_table()` 强制恰好 16 条，否则抛错拒绝（RT_STRING 槽位契约）。
- **feat: manifest-aware payload allowlist for verifier**
  - `verify.py --manifest <json>`：白名单载荷范围一律由 ORIGINAL 资源树按
    (BlockID, LANGID) **重新推导**，不信任 manifest 中写入的 file_offset；
  - 校验 original/patched SHA256 与 manifest 一致；
  - 输出 `non_target_resource_changes`（必须为 0），白名单外任何字节变化 → FAIL。
- **feat: add RT_STRING translation applier**
  - `scripts/apply_translation.py`：输入 SHA256 必须等于固定 baseline →
    CSV 加载（ResourceType/ResourceID/StringID/LANGID/Original/Chinese/Status）→
    逐块完整解析 16 条 → 逐条校验"实际文本 == CSV Original"及 printf/`\t` 不变量 →
    重序列化 → `new_blob ≤ 原分配`（否则 **RESOURCE_TOO_LARGE**）→
    整块回写原偏移、变短只在整块末尾补 0 →
    语义验证（资源树布局不变 / 每块 16 条 / 目标 == Chinese / 同块非目标与原版
    完全一致 / 非目标资源逐字节一致 / 变化 ⊆ 目标载荷）→ 输出 exe + manifest。
- **feat: add phase 1a translation entries**
  - `translations/keil_translation.csv` 扩列（+StringID、+LANGID），**43 条（LANGID 1033）**：
    11 个顶层菜单标题（117/139/165/681/729/759/784/786/793/795/799）+ 32 个常用项；
    其中 115/125/132/136/137/682 为满足整块大小约束新增的同块真实翻译。
- **涉及 Resource ID**：RT_STRING blocks 8/9/10/11/43/46/47/48/49/50（全部 LANGID 1033）。
  **2057(en-GB) 未修改**（其 16 个块 1001–3633 不覆盖任何目标 ID，按规范不新建资源）；
  **1041 未动**；RT_MENU/RT_DIALOG/RT_240/.rdata/头部/证书表零改动。
- **新增翻译条目**：43 条（见上）。
- **已知问题**：无新增。LANGID 文档修正：0x2000 ≠ Windows invariant（invariant = 0x007F），
  语义按 unresolved/opaque 处理；LANGID 9 / 1031 / 0x2000 的英文对话框全部留到 PHASE 1B+，
  其中 0x2000 修改前需进一步确认。
- **测试状态**：
  - ✅ apply 语义验证全部通过；块大小 616→606 / 490→464 / 622→590 / 386→386 /
    702→690 / 570→566 / 822→758 / 666→588 / 692→648 / 486→480。
  - ✅ `verify.py --manifest` PASS：changed_byte_count=1997、changed_ranges=1730、
    allowed_payload_ranges=10、**non_target_resource_changes=0**。
  - ✅ 汉化版重扫描抽查：菜单 40 / 对话框 246 / 加速键 5 不变；
    未动条目（113/127/129 等）逐字一致。
  - ✅ 自测回归 6/6；原版 UV4.exe 哈希仍为 428baf13…（未动）。
  - ⛔ GUI 测试（TEST 1–15）与编译一致性测试：未执行（等审核通过后用户手动测试）。
  - 签名：原版 Valid (Arm Limited) → 汉化版 **HashMismatch**（预期，未伪造、未绕过）。
- **产物**：`output/UV4_CN_TEST.exe`（SHA256 `f43167cb333828150904ed38f22e7d3cadbb71df2030d33f1c73c4cdb7ef4584`，
  本地 only，未提交 Git，未运行）；`output/uv4_cn_test_manifest.json`。

## 2026-09-13 — PHASE 0.1 REVIEW FIXES（GPT 第一轮审核结论：CHANGES REQUESTED）

- **fix: harden verifier section comparison and add whole-file diff guard**
  - 修复 `verify.py compare()` 中 `names` 变量复用（节名被资源类型名覆盖）导致
    "代码节变化可能被误报为一致"的缺陷：拆分 `section_names` / `resource_names`；
  - 受保护节判定直接基于 `changed_sections` 与固定集合
    `PROTECTED_SECTIONS = {.text, .rdata, .data, .pdata, CODE, DATA}`；
  - 节比较内部使用**完整 SHA256**（仅打印截短）；受保护节 / 非允许区域任何变化
    → **FAIL + 退出码 1**（不再只是打印警告）；
  - 新增**整文件 byte-level changed-range 审计**：要求文件大小一致；
    DOS 头 / PE-COFF / Optional / 节表 / .text / .rdata / .data / .reloc /
    证书表 / overlay 必须逐字节一致；所有变化字节必须落在 .rsrc；
    输出 `changed_byte_count` / `changed_ranges` / `changed_regions`。
- **fix: honor menu template header offsets**
  - RT_MENU (version 0)：首项位置改为 `4 + MENUITEMTEMPLATEHEADER.offset`；
  - MENUEX (version 1)：按 `MENUEX_TEMPLATE_HEADER`（WORD wVersion、WORD wOffset、
    DWORD dwHelpId）实现，首项位置 `4 + wOffset`，不再硬编码；
  - 重扫描 UV4.exe：**version 0 = 40、version 1 = 0、header_offset 全为 0、
    parse errors = 0**，此前的菜单分析结论不变（修复为预防性正确）。
- **fix/feat: add RT_STRING reserializer and verifier/parser self-tests**
  - 新增 `serialize_string_table()`：整块重序列化（PHASE 1A 写入路径，
    替代已废弃的逐字符串尾部零填充）；
  - 新增 `tests/test_selftest.py`：VERIFY-1..5 全部通过（6/6），临时 PE 在系统
    临时目录生成与销毁，不进 Git。
- **docs: revise phase 1 resource rewrite strategy**
  - ANALYSIS.md：废弃"逐字符串同尺寸尾部零填充"，改为 resource-level
    reserialization；PHASE 1 拆分 **1A（仅 RT_STRING，20–40 条）**与 1B+；
    RT_MENU version 直方图与 parse errors=0 入档；新增非常规 LANGID 调查
    （LANGID 9→对话框 641、8192→859、1031→807/811 均为英文用户 UI 且无其他
    语言副本，纳入 1B+ 策略；8192 动手前需再次确认；1041 不动）。
- **涉及 Resource ID**：仍仅分析/自测，未修改任何 Keil 二进制。
- **新增翻译条目**：无。
- **已知问题**：无新增（ANALYSIS.md §10 风险清单更新）。
- **测试状态**：VERIFY-1..5 6/6 通过；`verify.py` CLI 对照（原版 vs 备份）退出码 0；
  GUI 测试不适用（未生成修改后的二进制）。
- **Git**：tag `v0.1-analysis` 保持指向 50b5147 不动（历史审核基线）。

## 2026-09-13 — PHASE 0（tag: v0.1-analysis）

- **修改内容**
  - 初始化项目骨架（.gitignore / LICENSE / README / 术语表 / 各文档）。
  - 新增 `scripts/extract_resources.py`：只读 PE 资源扫描器（节表、资源树、
    String/Menu/Dialog/Accelerator 解码、探针字符串→所属资源映射、硬编码扫描）。
  - 新增 `scripts/verify.py`：基线固化 + 双文件逐节哈希对照（用于验证
    "汉化只改 .rsrc、代码节逐字节一致"）。
  - 完成 UV4 5.43.1.0 基线固化与资源分析（`docs/BASELINE.md`、`docs/ANALYSIS.md`）。
  - 原版备份：`C:\Keil_v5\UV4\Backup_Original\` 与项目 `backup/`（均 gitignored）。
- **涉及 Resource ID**：仅只读分析，未修改任何资源。
- **新增翻译条目**：无（PHASE 1 生成 `keil_translation.csv`）。
- **已知问题**：见 `docs/ANALYSIS.md` §10 风险点。
- **测试状态**：
  - ✅ `verify.py` 基线模式自测通过（SHA256、节表哈希、资源计数）。
  - ✅ 246 个对话框 / 40 个菜单模板全部解析成功，0 告警。
  - ⛔ GUI 测试：不适用（纯分析阶段，未生成任何修改后的二进制）。
