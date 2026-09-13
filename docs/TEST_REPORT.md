# 测试报告 (TEST_REPORT)

每个产出 `UV4_CN.exe` 的版本，必须执行以下矩阵并如实记录结果。
"编译通过"不等于"测试通过"；未执行的项必须明确标注未执行。
图例：✅ PASS ｜ ❌ FAIL ｜ ➖ 未单独报告（用户报告中未单列，不代表失败）

## PHASE 1A 用户真机测试报告（FINAL VALIDATION，2026-09-13）

### 实测环境

| 项 | 值 |
|---|---|
| 测试对象 | `UV4_CN_TEST.exe`（PHASE 1A 汉化测试版，SHA256 `f43167cb…4584`，本地生成） |
| 基线版本 | Keil µVision 5.43.1.0 / MDK 5.43.0.0 |
| 工程 | NS800 RT-Thread 项目 `project.uvprojx`（target `rt-thread`） |
| 工具链 | ArmClang V6.24 |
| 真实硬件 | NS800RT7P65D + CMSIS-DAP / DAPLink |
| 测试执行人 | 用户本人（LMX）；Agent 未参与执行 |

### 实测结果（用户报告原文汇总）

- **GUI / IDE**：启动正常；加载 `project.uvprojx` 正常；中文顶层菜单
  文件/编辑/视图/工程/Flash/调试/外设/工具/SVCS/窗口/帮助 全部正常显示，
  无乱码、无崩溃、无明显布局异常，菜单展开正常；Options for Target 可正常打开。
- **Build**：`Using Compiler 'V6.24'`、`Build target 'rt-thread'`、
  生成 `.\build\rt-thread.axf`，**0 Error(s) / 0 Warning(s)**，ArmClang 构建链正常。
- **Flash（真机）**：CMSIS-DAP 连接、Flash Algorithm、Target DLL、目标 Flash
  均正常；`Erase Done. / Programming Done. / Verify OK. / Flash Load finished`。
- **Debug（真机）**：Ctrl+F5 进入/退出 Debug Session、F5 Run、Stop、F11 Step、
  F10 Step Over 全部正常；Registers / Memory / Watch / Call Stack + Locals /
  Disassembly 窗口正常；源码 / PC 当前执行位置显示正常。

### 最终结论（用户判定）

**PHASE 1A：FUNCTIONAL TEST PASSED** —— 静态验证 PASS、GUI PASS、Build PASS、
CMSIS-DAP PASS、Flash PASS、Debug PASS；未发现汉化 RT_STRING 修改导致
IDE 崩溃、构建链异常、Flash 异常、Debugger 异常、工程损坏。

状态：✅ IMPLEMENTED ｜ ✅ STATIC VERIFIED ｜ ✅ USER HARDWARE TESTED ｜ ✅ PASSED

## 测试矩阵（PHASE 1A，基于用户真实测试结果填写）

| # | 测试项 | 结果 | 备注 |
|---|---|---|---|
| TEST 1 | 启动 µVision | ✅ PASS | 汉化版正常启动，顶层菜单全中文、无乱码 |
| TEST 2 | 打开现有 .uvprojx 工程 | ✅ PASS | NS800 RT-Thread 工程 `project.uvprojx` 正常加载 |
| TEST 3 | 编辑 C 文件 | ➖ 未单独报告 | 用户报告未单列此项 |
| TEST 4 | Build Target (F7) | ✅ PASS | `Build target 'rt-thread'`，0 Error / 0 Warning |
| TEST 5 | Rebuild all target files | ➖ 未单独报告 | 用户报告未单列此项 |
| TEST 6 | 查看 Build Output | ✅ PASS | 生成 `.\build\rt-thread.axf`，输出正常 |
| TEST 7 | 打开 Options for Target | ✅ PASS | 可正常打开 |
| TEST 8 | 打开 Device 页面 | ➖ 未单独报告 | 用户报告未单列此项 |
| TEST 9 | 进入 Debug Settings | ➖ 未单独报告 | 用户报告未单列此项 |
| TEST 10 | 使用现有 DAPLink / Debug Adapter | ✅ PASS | CMSIS-DAP / DAPLink + NS800RT7P65D |
| TEST 11 | Flash Download | ✅ PASS | Erase Done → Programming Done → Verify OK → Flash Load finished |
| TEST 12 | 进入 Debug Session | ✅ PASS | Ctrl+F5 进入，Ctrl+F5 退出 |
| TEST 13 | 查看 Registers / Memory / Watch / Call Stack / Disassembly | ✅ PASS | 五窗口正常；F5/F11/F10/Stop 正常；源码/PC 位置显示正常 |
| TEST 14 | 正常退出 µVision | ➖ 未单独报告 | 用户报告未单列此项 |
| TEST 15 | 再次启动并加载上次工程 | ➖ 未单独报告 | 用户报告未单列此项 |

## 编译一致性验证

同一工程分别用原版与汉化版 UV4.exe Rebuild，比对构建日志
（compiler/assembler/linker invocation、Program Size、Error/Warning）
与输出文件哈希（HEX/AXF），确认汉化不改变构建管线。

| 项目 | 结果 |
|---|---|
| 严格 A/B Rebuild 对比 | **未执行**（PHASE 1B 前可选补充项） |
| 间接证据（PHASE 1A） | 汉化版 Build Target：0 Error / 0 Warning，正常生成 `.\build\rt-thread.axf`；Flash Verify OK —— 构建管线未受影响 |

## 签名状态

| 文件 | Get-AuthenticodeSignature |
|---|---|
| 原版 UV4.exe | Valid (Arm Limited) |
| 汉化版 UV4_CN_TEST.exe | HashMismatch（预期；未伪造签名、未绕过安全机制） |

## PHASE 1A 静态验证（2026-09-13，apply_translation.py + verify.py --manifest）

| 项 | 结果 |
|---|---|
| 基线校验 | 输入 SHA256 == `428baf13…`（固定 baseline）✓ |
| 写入 | 43 条 / 10 个 RT_STRING 块（LANGID 1033）；new_blob ≤ 原分配（块 11 恰好等长，其余末尾补零） |
| apply 语义验证 | 资源树布局不变；各块 16 条；目标条目 == Chinese；同块非目标与原版完全一致；非目标资源逐字节一致 ✓ |
| `verify.py --manifest` | **PASS**：changed_byte_count=1997，changed_ranges=1730，载荷白名单 10 块（由原版资源树重新推导），**non_target_resource_changes=0**；PE 头/节表/.text/.rdata/.data/.reloc/证书表/overlay 逐字节一致 |
| 结构抽查（汉化版重扫描） | 菜单 40 / 对话框 246 / 加速键表 5 不变；未动条目（113 `µVision`、127 `PANE_FOR_RTAH…`、129 `\nSnap…` 文档模板串）逐字一致 |
| 签名 | 原版 **Valid** (Arm Limited) → 汉化版 **HashMismatch**（预期；未伪造签名、未绕过任何安全机制） |
| 自测回归 | VERIFY-1..5 6/6 通过 |
| GUI 测试矩阵（TEST 1–15） | ✅ **已执行**（用户真机测试，见"PHASE 1A 用户真机测试报告"；TEST 3/5/8/9/14/15 未单独报告） |
| 编译一致性（原版 vs 汉化版 Rebuild + 日志/产物哈希对比） | ⚠ 严格 A/B 未执行（间接证据：汉化版 0E/0W + Flash Verify OK，见真机报告） |

## PHASE 1B1 最终 GUI 验证（2026-09-13，GPT 转述用户实测）

### 实测结果

| 区域 | 结果 | 明细 |
|---|---|---|
| Project 主菜单 | ✅ PASS / PARTIAL | `New µVision Project...` → **新建 µVision 工程...** ✓；`Stop build` → **停止编译** ✓；Build Target / Rebuild / Batch Build 等既有条目继续正常中文。仍英文：`Options for File/Target...`、`Remove File ...`、`Translate <filepath> ...` —— 属动态文本 / runtime-updated 项，**不视为 RT_STRING/RT_MENU patch 失败** |
| Flash 菜单 | ✅ PASS | `Erase` → **擦除** ✓；Download 保持中文 |
| Project Window 右键（Target / Group / File 三种） | ⚠ PARTIAL BY DESIGN | 三种结构均正常；Build/Rebuild 类正常中文。仍英文：`Options for Target/Group/File`、`Add Group`、`Add New Item`、`Add Existing Files`、`Remove File/Group`、`Manage Project Items`、`Open Map File`、`Open Build Log`、`Show Include File Dependencies`、`Translate <file>`。结论：Keil 的 Project Window context menu 会按当前对象（Target/Group/File）动态适配文本 |
| Editor Context Menu | ⚠ PARTIAL（结构 PASS） | 菜单结构正常，无崩溃/乱码/层级异常。仍英文：Split Window horizontally、Toggle Header/Code File、Insert/Remove Breakpoint、Enable/Disable Breakpoint、Refresh Source Browser View、Update Source Browser Information、Go To Definition/Declaration/Next·Previous Reference...、Show All References...、Insert/Remove Bookmark、Undo、Redo、Cut、Copy、Paste、Select All。中文项：大纲、高级 |
| Build 回归 | ✅ PASS | F7：`Using Compiler V6.24`，生成 `rt-thread.axf`，**0 Error(s) / 0 Warning(s)**，无构建回归 |

### 重要结论（措辞按审核要求）

即使 RT_STRING / RT_MENU / command prompt 相关资源已经补齐，
编辑器右键最终 GUI 仍显示英文 —— **resource-vs-GUI behavior strongly supports
runtime command-UI text replacement, consistent with MFC ON_UPDATE_COMMAND_UI /
CCmdUI::SetText mechanism**（未经 dynamic tracing / call-site analysis，
不声称任何具体 .rdata 地址"已被证明传给 CCmdUI::SetText"）。

特殊剩余项：`Refresh Source Browser View`（RT_STRING 181 已翻译，GUI 仍英文）
→ 记录为 **unresolved runtime source / runtime override likely**，
按审核指示不在 PHASE 1B1 继续深挖。

### PHASE 1B1 最终结论

| 维度 | 结果 |
|---|---|
| STATIC VALIDATION | ✅ PASS |
| GUI STRUCTURE | ✅ PASS |
| RT_STRING | ✅ PASS |
| RT_MENU | ✅ PASS |
| BUILD REGRESSION | ✅ PASS |
| RESOURCE-LEVEL LOCALIZATION | ✅ PASS |
| COVERAGE | ⚠ PARTIAL BY DESIGN（runtime override text remains English） |
| .rdata | ✅ UNCHANGED（bit-identical，PHASE 1.x 禁改维持） |
| 崩溃 / 乱码 / 菜单结构损坏 / command ID 异常 / Build 异常 | 无 |

**PHASE 1B1 PASS — RESOURCE-LEVEL COMPLETE — COVERAGE PARTIAL BY DESIGN。**
剩余英文接受；未来如追求更高覆盖率，走 PHASE 2 — EXPERIMENTAL RDATA
LOCALIZATION 专项评估（当前禁止实施）。

## PHASE 1B2.2 批次静态验证（2026-09-13，工程与目标管理 Dialog 群：128/132/135/139/147/170/614/2047）

| 项 | 结果 |
|---|---|
| 基线 / 门禁 | SHA256 校验通过；**40/40 MENU round-trip** ✓；**246/246 DIALOG round-trip** ✓（applier 内置门禁 + 独立测试双重执行）；DIALOG-1..9 38/38 |
| 写入 | 累计 334 条（本轮新增 50 条：8 个 Dialog 的 title + BUTTON/STATIC string title）；全部整资源重序列化，logical ≤ 原分配（全部缩小） |
| Control locator | (ResourceID, LANGID, control_index) + ID/Class/Original 三重交叉校验 ✓ |
| 逐 Dialog 验证 | 128: 398→346（pad 52）；132: 490→418（pad 72）；135: 860→688（pad 172）；139: 362→340（pad 22）；147: 472→408（pad 64）；170: 1188→1016（pad 172）；614: 440→388（pad 52）；2047: 1564→1400（pad 164）—— 仅 manifest 指定 title 路径变化 ✓ |
| 139 标题模板 | `Get Filetype for '%s'` → `获取 '%s' 的文件类型`（printf token 保留）✓ |
| allocation padding | 资源尾部纯 00、长度精确（= 原分配 − logical）✓ |
| `verify.py --manifest` | **PASS**：changed_byte_count=15400，changed_ranges=9478，载荷白名单 **46 个资源范围**，**non_target_resource_changes=0**；其余 **238 个 Dialog bit-identical** |
| .rdata bit-identical | original == patched：`7e5438f7…f912` ✓ |
| 签名 | 原版 **Valid** → 测试版 **HashMismatch**（预期） |
| 自测回归 | VERIFY-1..6 7/7；DIALOG-1..9 38/38 |
| GUI 测试（1B2.2） | ⛔ **未执行** —— 等 GPT 批准后由用户手动测试 `UV4_CN_1B2_2_TEST.exe`（重点：Project 内文件/组窗口、File Extensions 页、Get Filetype 对话框（%s 文件名正常代入）、Device 页中文渲染、RTE/MDK 器件支持窗口按钮；裁切 → UI_LAYOUT_ISSUES.md） |


## PHASE 1B2.1b1 静态验证（2026-09-13，Manage Project Items 1033 资源：RT_STRING 32704 + RT_DIALOG 465/466/468）

| 项 | 结果 |
|---|---|
| 基线 / 门禁 | SHA256 校验通过；**40/40 MENU round-trip** ✓；**246/246 DIALOG round-trip 门禁（新增，applier 内置）** ✓；DIALOG-1..9 38/38 |
| 写入 | 累计 284 条（STRING 153 + MENU 79 + DIALOG 20 + RT_STRING 32704 等）；1B2.1b1 新增 33 条：RT_STRING 32704（prompt 整条 2 段）+ RT_DIALOG 465 ×4 / 466 ×22 / 468 ×6 |
| Control locator | (ResourceID, LANGID, control_index) + ID/Class/Original 三重交叉校验 ✓ |
| prompt 结构 | 32704：newline 分段 2→2，无 printf/反斜杠t，助记键 0=0 ✓ |
| 逐 Dialog 验证 | 465：416→352（pad 64）；466：2384→2052（pad 332）；468：672→596（pad 76）—— 仅 manifest 指定 title 路径变化；style/exStyle/rect/ID/class/font/helpID/creation data 全部一致 ✓ |
| 466 KEEP 项 | `&BIN:` `&INC:` `&LIB:` `&Regfile:` `...` 保持原文（技术缩写不强行中文化）✓ |
| allocation padding | 资源尾部纯 00、长度精确（= 原分配 − logical）✓ |
| verify.py --manifest | **PASS**：changed_byte_count=12016，changed_ranges=7743，载荷白名单 **38 个资源范围**，**non_target_resource_changes=0**；其余 **243 个 Dialog bit-identical** |
| .rdata bit-identical | original == patched：7e5438f7…f912 ✓ |
| 签名 | 原版 **Valid** → 测试版 **HashMismatch**（预期） |
| 自测回归 | VERIFY-1..6 7/7；DIALOG-1..9 38/38 |
| GUI 测试（1B2.1b1） | ⛔ **未执行** —— 等 GPT 批准后由用户手动测试 UV4_CN_1B2_1B_TEST.exe（重点：外层标题"管理工程项目"、三个 Tab"工程项目/文件夹/扩展名/书籍"、第四页 Project Info/Layer 仍英文预期、466 全部中文与裁切（重点 Use GCC Compiler / Setup Default ARM Compiler Version 长按钮）、468 只查 UI、动态标签 Project Targets:/Groups:/Files: 仍英文预期、OK/Cancel/Help 仍英文预期） |


## PHASE 1B2.1a 最终 GUI 验证（2026-09-13，GPT 转述用户实测）

### 实测环境

`UV4_CN_1B2_1A_TEST.exe` ｜ 基线 µVision 5.43.1.0 ｜ 工程 NS800 RT-Thread `project.uvprojx`

### 逐 Dialog 实测结果

| Dialog | 结果 | 实测明细 |
|---|---|---|
| 100 — About µVision | ✅ PASS | 标题 `About µVision` → **关于 µVision** ✓；`OK` → **确定** ✓；中文显示正常。无乱码/豆腐块/字符缺失/Dialog 崩溃/控件错位/明显裁切。版本、版权、License、Legal Notices、Copy Info 等法律/授权/版本文本保持英文 —— 符合本阶段要求。字体 Arial 9pt 未修改，中文可正常显示 |
| 511 — Batch Setup | ✅ PASS | 实测中文：批量编译设置 / 选择工程目标 / 编译 / 重新编译 / 清理 / 全选 / 取消全选 / 取消 / 帮助(H) / 关闭 / 在首个失败工程后停止 全部正常。Project/Target 名称（project、rt-thread）保持用户工程原始内容，未被错误汉化。无乱码/豆腐块/崩溃/按钮错位/明显裁切。字体 MS Shell Dlg 8pt（DS_SHELLFONT=yes）未修改 |
| 129 — Targets | ➖ **NOT EXERCISED / UI ENTRY NOT RESOLVED** | 本轮未找到直接用户入口，**不标记 FAIL**。用户实际打开的是 Project → Manage → Project Items（对应当前正式工作流的 Manage Project Items 窗口，非 Dialog 129）。按 GPT 指示不追加测试 Dialog 129 |

### 非目标 Dialog 回归

| 窗口 | 结果 |
|---|---|
| Options for Target 'rt-thread' | ✅ 正常打开，所有 Tab/控件布局正常（本阶段未翻译，保持英文符合预期） |
| Manage Project Items | ✅ 正常打开，显示 Project Targets / Groups / Files / Set as Current Target / Add Files / OK / Cancel / Help 等英文（本阶段未翻译，符合预期）—— **证明非目标 Dialog 未被误伤** |

### Build 回归

F7：`Using Compiler V6.24`，生成 `rt-thread.axf`，**0 Error(s) / 0 Warning(s)** —— 无构建回归。

### PHASE 1B2.1a 最终结论

| 维度 | 结果 |
|---|---|
| STATIC VALIDATION | ✅ PASS |
| DIALOG CODEC | ✅ PASS |
| ABOUT GUI | ✅ PASS |
| BATCH SETUP GUI | ✅ PASS |
| NON-TARGET DIALOG REGRESSION | ✅ PASS |
| BUILD | ✅ PASS |
| FONT RENDERING | ✅ PASS |
| LAYOUT | ✅ PASS（no obvious clipping found） |

**PHASE 1B2.1a：PASS**（Dialog 129 NOT EXERCISED / UI ENTRY NOT RESOLVED，未标记 FAIL）。

## PHASE 1B2.1a 静态验证（2026-09-13，首批 Dialog 烟雾测试：100/129/511）

| 项 | 结果 |
|---|---|
| 基线 / 门禁 | SHA256 校验通过；40/40 MENU round-trip ✓；**246/246 DIALOG round-trip** ✓（原版）；DIALOG-1..9 **38/38** |
| 写入 | 累计 251 条（STRING 152 + MENU 79 + **DIALOG 20**）；本轮新增 Dialog 文本 20 条（100 ×2、129 ×7、511 ×11，含 dialog title） |
| Control locator | (ResourceID, LANGID, control_index) + ID/Class/Original 三重交叉校验 ✓（实战拦截 2 次 ID 转录错误：511 ctl:4 1864→1863、ctl:5 1865→1864） |
| 逐 Dialog 验证 | 100：1084→1080（pad 4）；129：588→472（pad 116）；511：696→536（pad 160）—— 仅 manifest 指定 title 路径变化；style/exStyle/rect/ID/class/font/helpID/creation data 全部一致 ✓ |
| allocation padding | 资源尾部纯 00、长度精确（= 原分配 − logical）；原版 semantic trailing 保持 0 ✓ |
| `verify.py --manifest` | **PASS**：changed_byte_count=9465，changed_ranges=6535，载荷白名单 **34 个资源范围**，**non_target_resource_changes=0**；其余 **243 个 Dialog bit-identical** |
| .rdata bit-identical | original == patched：`7e5438f7…f912` ✓ |
| 签名 | 原版 **Valid** → 测试版 **HashMismatch**（预期） |
| 自测回归 | VERIFY-1..6 7/7；DIALOG-1..9 38/38 |
| GUI 测试（1B2.1a） | ✅ **已执行** —— 见 "PHASE 1B2.1a 最终 GUI 验证" |

## PHASE 1B2.0b 验证输出（真实 stdout，2026-09-13 执行，exit=0）

> 1B2.0a 审核指出：快照加硬修改漏提交（commit 8ccbbe5 仅暂存了测试文件，
> `scripts/extract_resources.py` 的加硬版 `dialog_semantic_snapshot()` 留在
> 未提交工作区），导致 HEAD 上 DIALOG-4 会 KeyError。本节 stdout 来自
> **加硬版已入库后**的真实执行；另将快照字段对齐审核规范
> （creation_data_len / creation_data_sha256 / creation_size_bytes 扁平字段），
> 并增加防回归断言（字段改名不可能再次静默漏掉）。
> 同时新增 `.gitattributes`（`*.py/*.md/*.csv/*.json → LF`）根治上轮
> extract_resources.py 的整文件 CRLF/LF churn（本次提交包含该一次性归一，
> 真实内容差异见 `git diff --ignore-cr-at-eol`：30/7 行）。

```text
RT_DIALOG 总数: 246; 基线校验: 通过
  [PASS] DIALOG-1 parse 246/246
  [PASS] DIALOG-2 serialize 246/246
  [PASS] DIALOG-3 byte-identical 246/246 (std 52/52, ex 194/194)
== TEST DIALOG-4: Standard 合成 fixture ==
  [PASS] std: size_bytes=6/payload=4 round-trip 稳定
  [PASS] std: nonzero creation data 保真
  [PASS] std: odd size_bytes=7/payload=5 round-trip 稳定
  [PASS] std: 两 fixture 控件起始 offset 均 DWORD 对齐 — offsets=[[44, 92], [44, 96]]
  [PASS] std: 语义一致
  [PASS] std 快照字段绑定: creation_size_bytes == 6
  [PASS] std 快照字段绑定: creation_data_len == 4 且 creation_data_sha256 == sha256(payload)
== TEST DIALOG-5: Extended 合成 fixture ==
  [PASS] ex: round-trip 稳定
  [PASS] ex: helpID/exStyle/weight/italic/charset/extraCount=5 保真
  [PASS] ex: 控件起始 offset 均 DWORD 对齐
  [PASS] ex 快照字段绑定: dlgVer==1 / signature==0xFFFF / dialog helpID==0x1234
  [PASS] ex 快照字段绑定: control helpID==0x5678 / extraCount==5 / creation_data_len==5 / creation_data_sha256==sha256(payload)
== TEST DIALOG-6: 字段破坏 → 语义验证器必须发现 ==
  [PASS] DIALOG-6 破坏字段被语义验证器发现 (IDD_FINDREPLBASE,1033) — diffs=['controls[0].style: 1342242817 → 1342243070', "title: 'Dialog' → 'Xialog'"]
== TEST DIALOG-7: 文本长度奇偶突变 → 对齐自动重建 ==
  [PASS] std 对齐突变: 全部控件 offset % 4 == 0 — pads even=[0, 0] odd=[0, 2]
  [PASS] std 覆盖 0-byte→2-byte 与 2-byte→0-byte — c2 pad: 偶长度标题 0 字节 ↔ 奇长度标题 2 字节
  [PASS] ex 对齐突变: 全部控件 offset % 4 == 0 — pads even=[0, 0] odd=[0, 2]
  [PASS] ex 覆盖 0-byte→2-byte 与 2-byte→0-byte — c2 pad: 偶长度标题 0 字节 ↔ 奇长度标题 2 字节
  [PASS] std 突变前后除 title/text 外语义字段未变化
== TEST DIALOG-8: 语义破坏守卫 (必须全部 FAIL/拒绝) ==
  [PASS] DIALOG-8.1 dialog helpID 改 1 bit → 发现
  [PASS] DIALOG-8.2 signature 改变 → 发现
  [PASS] DIALOG-8.3 cDlgItems 与控件数不一致 → serializer 拒绝
  [PASS] DIALOG-8.4 control exStyle 改变 → 发现
  [PASS] DIALOG-8.5 creation data 同长度改 1 字节 → 发现
  [PASS] DIALOG-8.6 extraCount 与 creation data 不一致 → serializer 拒绝
  [PASS] DIALOG-8.7 std size_bytes 与 payload 不一致 → serializer 拒绝
  [PASS] DIALOG-8.8 trailing 不透明字节变化 → 发现
========================================================================
自测结论: 29/29 项全部通过
```

回归：VERIFY-1..6 自测 7/7；`parse_dialog_template` 投影视图兼容
（map_dynamic_strings 回归 exit=0）。

## PHASE 1B1.2 静态验证（2026-09-13，RT_MENU 592/624/191/800/22565/400 + 补充 RT_STRING 含 command prompt）

| 项 | 结果 |
|---|---|
| 菜单 round-trip 门禁 | **40/40** parse → serialize → byte-identical ✓（写入前强制） |
| 写入 | 累计 231 条：STRING 152（22 块）+ MENU 79（9 个资源）；1B1.2 新增 44 条（STRING 21 含 command prompt 整条、MENU 23 仅 GUI mapping 确认路径）；全部整资源重序列化，new_blob ≤ 原分配 |
| prompt 结构校验（新增门禁） | `57634/57635/57637/57642/57643/57644` 六条 command prompt 整条处理：newline 分段 2→2、printf token 一致、`\t` 后快捷键逐字一致 ✓ |
| 守卫实录 | ①校验器拦截 3 条"原文无助记键而中文误加 (&X)"（MENU 191/800 0/17、400 0/0）→ 修正；②拦截 MENU 191 同级助记键冲突（0/8 原文助记键为 **B** 而非 N，会与未译 `I&nstruction Trace` 撞车）→ 保持原字母 B |
| apply 语义验证 | 资源树布局不变；各 STRING 块 16 条；MENU 树逐节点 command ID / flags / 树形 / 数量 / header_offset 不变；仅目标路径文本变化；无新同级助记键冲突 ✓ |
| `verify.py --manifest` | **PASS**：changed_byte_count=8168，changed_ranges=5756，载荷白名单 **31 个资源范围**（由原版资源树重新推导），**non_target_resource_changes=0** |
| **.rdata bit-identical** | original == patched：SHA256 `7e5438f70385cb3d357b1ed00fa4ab2e47cc2fcc15452dfe5a845f244148f912` ✓ |
| 签名 | 原版 **Valid** → 1B1.2 测试版 **HashMismatch**（预期） |
| 自测回归 | VERIFY-1..6 7/7 通过 |
| GUI 测试（1B1.2） | ✅ **已执行** —— 见 "PHASE 1B1 最终 GUI 验证"（写入机制/主菜单/Flash PASS；Project Tree 与编辑器右键 PARTIAL BY DESIGN，剩余英文为 runtime override，已接受） |

## PHASE 1B1 用户 GUI 测试结果（GPT 转述汇总，2026-09-13）

| 项 | 结果 |
|---|---|
| RT_STRING / RT_MENU 写入机制 | ✅ PASS |
| 主菜单 Edit / View / Project 等 | ✅ PASS（大量条目已中文） |
| 文件标签页右键（MENU 1205） | ✅ PASS |
| Project Tree 右键 | ⚠ PARTIAL —— 运行时更新的条目仍英文（根/组上下文来自未覆盖的 MENU 592/624 + .rdata 驱动，见 `DYNAMIC_MENU_MAPPING.md`） |
| 源码编辑器右键 | ⚠ PARTIAL —— 多数运行时生成/更新条目仍英文（MENU 191/800/22565 未覆盖 + .rdata ANSI 字面量驱动；"大纲/高级"弹出标题已中文） |
| 崩溃 / 乱码 / 菜单结构损坏 / command ID 异常 | 无 |
| 1B1 技术验证 | ✅ PASS（写入机制正确；覆盖率缺口源于 MFC 运行时机制，已由 PHASE 1B1.1 映射定位） |

## PHASE 1B1 静态验证（2026-09-13，RT_MENU + 补充 RT_STRING，`apply_translation.py` + `verify.py --manifest`）

| 项 | 结果 |
|---|---|
| 菜单 round-trip 门禁 | 写入前 **40/40 RT_MENU** parse → serialize → byte-identical ✓（自测 VERIFY-6，7/7 通过） |
| 写入 | RT_STRING 131 条（17 块）+ RT_MENU 56 条（资源 143/1200/1205）；全部**整资源重序列化**，new_blob ≤ 原分配（块 3841 等长 268→268） |
| 守卫实录 | applier 拦截 1 次 CSV 路径转录错误（MENU 1200 的 0/1/3 与 0/1/4 抄串，Original 比对直接拒绝）→ 修正 CSV 后通过；另 1 处整块超长（block 3841 +2 字节）按规则缩短措辞解决 |
| apply 语义验证 | 资源树布局不变；各 STRING 块 16 条；**MENU 树逐节点比较：command ID / flags / MF_POPUP 性 / 树形 / item 数量 / header_offset 全部不变**，仅 manifest 指定路径的 text 变化且 == Chinese；无新同级助记键冲突 ✓ |
| `verify.py --manifest` | **PASS**：changed_byte_count=6220，changed_ranges=4414，载荷白名单 **21 个资源范围**（由原版资源树重新推导），**non_target_resource_changes=0**；PE 头/节表/.text/.rdata/.data/.reloc/证书表/overlay 逐字节一致 |
| 结构抽查（汉化版重扫描） | 菜单 40 / 对话框 246 / 加速键表 5 不变；未动条目（如 MENU 1200 `0/1/2 Collapse Selected Definitions`、弹出标题 `&Edit`）逐字一致 |
| 签名 | 原版 **Valid** (Arm Limited) → 1B1 测试版 **HashMismatch**（预期） |
| 自测回归 | VERIFY-1..6 7/7 通过 |
| GUI 测试（1B1） | ⛔ **未执行** —— 等 GPT 审核通过后由用户手动测试 `UV4_CN_1B1_TEST.exe` |

## 验证器/解析器自测（PHASE 0.1 — `tests/test_selftest.py`，2026-09-13 执行，exit=0）

| 用例 | 内容 | 结果 |
|---|---|---|
| VERIFY-1 | 原版 vs 原版 | ✅ PASS（exit 0） |
| VERIFY-2 | 临时副本 .rsrc 内 1 字节翻转 | ✅ PASS（exit 0），仅报告 .rsrc 变化（1 处/1 字节） |
| VERIFY-3 | 临时副本 .text 内 1 字节翻转 | ✅ 预期 FAIL（exit 1），报告 .text 变化 |
| VERIFY-4 | 临时副本 PE 头部 1 字节翻转 | ✅ 预期 FAIL（exit 1），报告 PE-Headers 变化 |
| VERIFY-5 | RT_STRING parse → serialize 无修改往返 | ✅ 259/259 块逐字节一致 |
| 附加 | 缩短条目后整块变短（末尾补零语义演示） | ✅ 原块 622 字节 → 缩短后 598 字节 |

临时 PE 均在系统临时目录生成并销毁，不进入 Git。完整输出：`output/selftest_phase01.log`（本地）。
