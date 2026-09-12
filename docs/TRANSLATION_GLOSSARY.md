# 翻译术语表与字符串修改规范

配套机读版本：[`translations/glossary.json`](../translations/glossary.json)
翻译数据库：[`translations/keil_translation.csv`](../translations/keil_translation.csv)

## 一、主菜单标题（固定译法）

| 英文 | 中文 | 说明 |
|---|---|---|
| &File | 文件(&F) | 保留助记键 F |
| &Edit | 编辑(&E) | |
| &View | 视图(&V) | |
| &Project | 工程(&P) | 中国用户惯用"工程"，不用"项目" |
| Fl&ash | Flash(&A) | 助记键在 a 上 |
| &Debug | 调试(&D) | |
| Pe&ripherals | 外设(&R) | 仅调试模式出现的菜单 |
| &Tools | 工具(&T) | |
| &SVCS | SVCS(&S) | 缩写不翻译 |
| &Window | 窗口(&W) | |
| &Help | 帮助(&H) | |

## 二、统一术语

| 英文 | 中文 |
|---|---|
| Project | 工程 |
| Target | 目标 |
| Build | 编译 |
| Build Target | 编译目标 |
| Rebuild | 重新编译 |
| Batch Build | 批量编译 |
| Clean | 清理 |
| Download | 下载 |
| Options for Target | 目标选项 |
| Device | 器件 |
| Manage Run-Time Environment | 管理运行时环境 |
| Pack Installer | Pack 安装器 |
| Configuration / Settings | 配置 / 设置 |
| Memory / Register | 内存 / 寄存器 |
| Peripheral | 外设 |
| Call Stack | 调用栈 |
| Breakpoints | 断点 |
| Disassembly | 反汇编 |
| Logic Analyzer | 逻辑分析仪 |
| System Viewer | 系统查看器 |
| Memory Map | 内存映射 |
| Start/Stop Debug Session | 开始/停止调试 |
| Build Output | 编译输出 |
| Source Browser | 源代码浏览器 |

## 三、禁止翻译清单

CMSIS、RTX、RTOS、ARM/Arm、Cortex-M/R/A、DAP、CMSIS-DAP、DAPLink、J-Link、
ULINK、Pack、SVD、AGDI、SWD、JTAG、ArmClang、Arm Compiler、C51、C251、C166、
MDK、µVision、SVCS、PC-Lint、**License Management（授权相关文本一律保留英文，
避免任何歧义）**、FlexNet。

## 四、字符串修改硬性规则

1. **资源 ID / Dialog ID / 控件 ID / 命令 ID 一律不变**，只改显示文本。
2. **printf 格式符必须原样保留**：`%s %d %u %x %X %02X %08X %lu %p …`，
   以及 `\n` `\r` `\t`。
   例：`"Cannot open file '%s'"` → `"无法打开文件 '%s'"`。
3. **助记键 `&`**：英文 `&File` → 中文 `文件(&F)`；不得全部删除，
   优先保持原快捷键字母。
4. **快捷键段必须保留**：`&Open\tCtrl+O` → `打开(&O)\tCtrl+O`。
5. **复用模板**：`%sptions for Target '%s'%s%s` 这类模板（首字符由运行时
   注入）结构完全不动，仅在不破坏 `%` 占位的前提下谨慎处理。
6. **整块大小约束（resource-level reserialization）**：写入时按"整块解析 → 改目标条目 →
   重序列化全部 16 条 → 整块回写"处理；只要 `新块字节数 ≤ 原块分配` 即可，
   单条中文可以长于对应英文原文，但整块超长会被 `RESOURCE_TOO_LARGE` 拒绝；
   块变短时只在整块末尾补 0，字符串之间绝不塞 0。放不下的先缩短措辞，
   记录到 `UI_LAYOUT_ISSUES.md`。
7. 多语言副本（en-GB/lang 2057）与 en-US（1033）同一 ID 都要改，防止
   资源加载器选到未翻译副本；日语副本（1041）不动。
