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
