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

## 签名状态

| 文件 | Get-AuthenticodeSignature |
|---|---|
| 原版 | Valid (Arm Limited) |
| 汉化版 | *每次生成后如实记录* |
