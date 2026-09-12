# 测试报告 (TEST_REPORT)

每个产出 `UV4_CN.exe` 的版本，必须执行以下矩阵并如实记录结果。
"编译通过"不等于"测试通过"；未执行的项必须明确标注未执行。

## 测试矩阵

| # | 测试项 | 结果 | 备注 |
|---|---|---|---|
| TEST 1 | 启动 µVision | | |
| TEST 2 | 打开现有 .uvprojx 工程 | | |
| TEST 3 | 编辑 C 文件 | | |
| TEST 4 | Build Target (F7) | | |
| TEST 5 | Rebuild all target files | | |
| TEST 6 | 查看 Build Output | | |
| TEST 7 | 打开 Options for Target | | |
| TEST 8 | 打开 Device 页面 | | |
| TEST 9 | 进入 Debug Settings | | |
| TEST 10 | 使用现有 DAPLink / Debug Adapter | | |
| TEST 11 | Flash Download | | |
| TEST 12 | 进入 Debug Session | | |
| TEST 13 | 查看 Registers / Memory / Watch / Call Stack / Disassembly | | |
| TEST 14 | 正常退出 µVision | | |
| TEST 15 | 再次启动并加载上次工程 | | |

## 编译一致性验证

同一工程分别用原版与汉化版 UV4.exe Rebuild，比对构建日志
（compiler/assembler/linker invocation、Program Size、Error/Warning）
与输出文件哈希（HEX/AXF），确认汉化不改变构建管线。

| 项目 | 原版 UV4.exe | 汉化版 UV4_CN.exe | 一致 |
|---|---|---|---|
| *PHASE 1 起填写* | | | |

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

## 签名状态

| 文件 | Get-AuthenticodeSignature |
|---|---|
| 原版 | Valid (Arm Limited) |
| 汉化版 | *每次生成后如实记录* |
