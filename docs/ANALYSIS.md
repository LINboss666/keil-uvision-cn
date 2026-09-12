# PHASE 0 分析报告 — UV4.exe 汉化可行性

- 日期：2026-09-13
- 目标：`C:\Keil_v5\UV4\UV4.exe`（官方原版，只读分析，未做任何修改）
- 工具：`scripts/extract_resources.py`（纯 Python 标准库只读扫描器）+ PowerShell
- 完整机读清单：`output/resource_inventory.json`（本地，gitignored）

---

## 1. 文件基本信息

| 项目 | 值 |
|---|---|
| 完整路径 | `C:\Keil_v5\UV4\UV4.exe` |
| FileVersion / ProductVersion | 5.43.1.0 / 5.43.1.0（与 About µVision 一致） |
| 产品 / 公司 | µVision IDE / ARM Limited，Copyright (C) 2025 ARM Ltd and ARM Germany GmbH |
| 文件大小 | 12,765,464 bytes |
| SHA256 | `428baf13d15e6760af1618def9c9815c97f0321cc5e459ec7adc4dde41c42f89`（Get-FileHash 与 certutil 双重验证一致） |
| PE 架构 | PE32（32 位 x86，Machine=0x014C），GUI 子系统，ImageBase 0x400000 |
| 数字签名 | **Valid** — CN=Arm Limited, O=Arm Limited（GlobalSign GCC R45 EV CodeSigning CA 2020 签发，有效期 2025-01-05 ~ 2027-02-05） |
| DllCharacteristics | DYNAMIC_BASE(ASLR)、NX_COMPAT(DEP)、TERMINAL_SERVER_AWARE |
| 链接时间 | 2025-08-19 19:15:41 UTC |

同机注意事项：
- `D:\Keil c51\UV4\UV4.exe` 是另一个独立的 C51 安装，**不在本项目范围，永不触碰**。
- `C:\Keil_v5\UV4\FlexNet\` 为许可证组件，**永不触碰**。
- 同目录 `UV4.dll` 经扫描只含 MANIFEST/VERSION 资源，无 UI 资源 → UI 资源集中在 UV4.exe。

## 2. PE 节表

| 节 | VirtualSize | VAddr | SizeOfRawData | RawPtr | 特征 |
|---|---|---|---|---|---|
| .text | 0x727176 | 0x1000 | 0x727200 | 0x400 | 0x60000020（代码） |
| .rdata | 0x142AD6 | 0x729000 | 0x142C00 | 0x727600 | 0x40000040（只读数据） |
| .data | 0x21672BC | 0x86C000 | 0x26E00 | 0x86A200 | 0xC0000040 |
| **.rsrc** | 0x30CC10 | 0x29D4000 | 0x30CE00 | 0x891000 | 0xC0000040（**资源 ≈ 3.2 MB**） |
| .reloc | 0x8C0E4 | 0x2CE1000 | 0x8C200 | 0xB9DE00 | 0x42000040 |

导入表 24 个 DLL，**无 MFC/VC 运行库 DLL → MFC 静态链接**（这也解释了 12 MB 体积）。
.rsrc 位于最后一个可读写节，.reloc 之前——资源改写只需处理该节。

## 3. 资源树概览（1642 个叶子节点，17 种类型）

| 类型 | 数量 | 字节 | 语言分布 |
|---|---|---|---|
| RT_DIALOG | **246** | 200,762 | 1033×218，2057×24，9×1，1031×2，8192×1 |
| RT_STRING | **259 块** | 98,470 | 1033(955 条非空)，1041(534 条)，2057(123 条) |
| RT_MENU | **40** | 11,190 | 1033×39，2057×1 |
| RT_ACCELERATOR | **5** | 1,224 | 1033 |
| RT_BITMAP | 136 | 743,418 | — |
| RT_ICON / RT_GROUP_ICON | 152 / 42 | 866,844 / 2,380 | — |
| RT_CURSOR / RT_GROUP_CURSOR | 51 / 42 | 14,996 / 966 | — |
| PNG（自定义类型名） | 553 | 1,012,317 | 工具栏/图标素材 |
| RT_240（自定义） | 57 | 15,065 | 对话框列表控件**列头定义**（ANSI 串：Name/Class/Type/Memory Space/Uses…） |
| RT_241（自定义） | 7 | 150 | — |
| STYLE_XML（自定义） | 5 | 83,741 | — |
| TYPELIB / RT_VERSION / RT_MANIFEST | 1/1/1 | 16,540/768/381 | manifest 为最小 asInvoker |
| AFX_DIALOG_LAYOUT | 44 | 88 | MFC 布局 blob，不动 |

**多语言副本注意**：同一资源 ID 可能同时存在 1033(en-US)、2057(en-GB)、1041(ja) 副本。
翻译时 1033 与 2057 必须同步修改，1041 保留不动。

## 4. 关键发现：主菜单的存放机制（MFC 动态弹出菜单）

主菜单顶栏标题**不在 RT_MENU 里**（40 个 RT_MENU 是各停靠窗口的上下文菜单与
小型弹出菜单），而是作为 **RT_STRING 字符串表条目**存在，运行时由程序装配。
已用"日语副本对照 + 所属资源偏移归属"双重确认：

| 菜单 | 标题原文 | String ID |
|---|---|---|
| 文件 | `&File` | **117** |
| 编辑 | `&Edit` | **139** |
| Flash | `Fl&ash` | **165** |
| 视图 | `&View` | **681** |
| 工程 | `&Project` | **729** |
| 调试 | `&Debug` | **759** |
| 外设（仅调试模式） | `Pe&ripherals` | **784** |
| 工具 | `&Tools` | **786** |
| SVCS | `&SVCS` | **793** |
| 窗口 | `&Window` | **795** |
| 帮助 | `&Help` | **799** |

内置的**日语（1041）资源**（如 id=128 `保存(&S)\tCtrl+S`、id=162
`コンパイル ... (&A)\tCtrl+F7`、id=786 `ツール(&T)`、id=165 `フラッシュ (&A)`）
证明：这套 UI 完全支持通过资源层多语言化，中文按同样机制处理即可。

常用命令/菜单项（RT_STRING，节选，均含必须保留的 `&`/`\t`/`%s` 结构）：

| String ID | 原文 | 说明 |
|---|---|---|
| 121 / 124 / 128 | `&New...\tCtrl+N` / `&Open\tCtrl+O` / `&Save\tCtrl+S` | File 菜单项 |
| 152 | `&Build Target\tF7` | 编译目标 |
| 153 / 160 | `&Build '%s (%s)'\tF7` / `&Rebuild '%s (%s)'` | 多工程模板，`%s` 必须保留 |
| 154 | `&Rebuild all target files` | 重新编译 |
| 166 | `&Download` | 下载 |
| 738 / 739 / 741 | `Run-Time &Environment...` / `&Select Software Packs...` / `Pack &Installer...` | RTE / Pack |
| 743 / 746 | `&Select Device for Target ...` / `&Select Device for Target '%s' …` | 选择器件 |
| 748 | `O&ptions...\tAlt+F7` | 目标选项 |
| 749–755 | `%sptions for Target '%s'%s%s` 等 | **复用模板**：首字符由运行时注入，结构必须原样保留 |
| 756 | `Clean &Targets` | 清理 |
| 758 | `&Configure Flash Tools...` | Flash 菜单首项 |
| 760 | `Start/Stop &Debug Session\tCtrl+F5` | 开始/停止调试 |
| 761–783 | `Reset &CPU` / `&Run\tF5` / `&Stop\tEsc` / `S&tep\tF11` / `&Breakpoints...` / `Debug Settin&gs...` 等 | Debug 菜单 |

**不要触碰**的资源文本示例（程序逻辑用途，非 UI 文案）：id=118（进度条占位空格串）、
id=119（`This is the space for the Progress Bar`）、id=123（`AABC*DEFGHIJKLMNOPQRSTUVW`，
字体度量串）、id=129/1953 附近的 `\nSnap\nSnap\n\n\nSnap.Document\n...`（MFC 文档模板注册串）、
id=133 `&Device Database…` 与 id=134 `License &Management...`（**授权相关，按规范保留英文**）。

趣味发现：MENU 543 的占位菜单标题是 `Bullshit!`（Arm 工程师的内部玩笑，不影响任何功能）。

## 5. String Table 示例（随机抽取）

| String ID | 文本 |
|---|---|
| 117 | `&File` |
| 124 | `&Open\tCtrl+O` |
| 152 | `&Build Target\tF7` |
| 154 | `&Rebuild all target files` |
| 681 | `&View` |
| 697 | `&Disassembly Window` |
| 699 | `Re&gisters Window` |
| 701 | `Watc&h Windows` |
| 704–708 | `&Memory Windows` / `Memory &1`…`Memory &4` |
| 729 | `&Project` |
| 760 | `Start/Stop &Debug Session\tCtrl+F5` |
| 35438 | `Scan function names in current editor files\nScan Current Editor Files`（状态栏提示 `\n` 工具栏提示，MFC 双段格式） |

字符串表共 259 块 / 合并视图 1078 条非空（1033:955、1041:534、2057:123），全部 UTF-16LE，
`(块ID-1)×16+序号` 映射清晰。

## 6. Dialog 概览

246 个对话框全部解析成功（标准 DLGTEMPLATE 与 DLGTEMPLATEEX 两种格式都有）。
关键对话框（res_id → 标题）：

| res_id | 标题 | 备注 |
|---|---|---|
| 100 | `About µVision` | 关于框 |
| 128 / 129 / 132 | `Files in Project` / `Targets` / `Groups / Add Files` | 工程窗口系列 |
| 142 | `Target` | 47 个控件 |
| 614 | （含 `Manage Run-Time Environment`） | RTE |
| 629 / 2047 | （含 `Options for Target`） | 目标选项属性页 |
| 139 | `Get Filetype for '%s'` | 模板标题，`%s` 保留 |

其余大量对话框标题为运行时注入或空标题（由 RT_STRING 提供文案）。
**语言分布**：218×1033 + 24×2057 + 少量其他 → 2057 副本同样需要处理。

## 7. 硬编码字符串扫描结论

对 27 个探针串在整份文件中做 UTF-16LE/ASCII 全扫描并按节归类：

- 探针命中的**绝大多数 UI 文本位于 .rsrc**（RT_STRING/RT_MENU/RT_DIALOG），与 §4/§5 一致。
- `.rdata` 存在**大量 ANSI 消息/格式串**（如
  `"Project File '%s'\n\nhas been modified externally, Reload ?"`、
  `"Bad or missing [%s] section in file 'Tools.Ini'"`、147 处 `Error`、377 处 `File`…），
  以及少量 UTF-16 串。这些是代码内字符串，**PHASE 1 一律不动**，仅登记
  （清单在 `output/resource_inventory.json` → `hardcoded_scan`）。
- `&File`/`&Edit` 等的 ASCII 命中均为 `"Add Existing &Files to Group '%s'..."`
  一类消息串的子串误匹配，不是主菜单。
- 自定义类型 RT_240（57 块）是对话框列表控件的**列头定义**（ANSI 自定义二进制格式），
  属第二梯队汉化对象，需要专用解析器，PHASE 1 不处理。

## 8. 汉化可行性结论（对应任务书 A–E）

| 问题 | 结论 |
|---|---|
| A. 大部分 UI 文本是否标准 PE 资源？ | **是。** 菜单项（RT_MENU×40）、对话框（RT_DIALOG×246）、字符串/提示/主菜单标题（RT_STRING，955 条 1033）全部在 .rsrc，且 UTF-16LE。 |
| B. 能否主要靠修改 .rsrc 完成汉化？ | **能。** PHASE 1 采用"同尺寸原位改写"（中文 UTF-16 字节数 ≤ 英文原文，尾部零填充）；这也是风险最小的方案。若个别文案必须加长，再评估"重建 .rsrc 节"方案（技术上可行：重排资源目录 + 更新节表，.reloc 不受影响，因为资源在运行时按目录树寻址）。 |
| C. 有没有明显硬编码字符串？ | **有，但占比小。** .rdata 的 ANSI 格式串/消息、RT_240 列头、极少量 .data 串。PHASE 1 不动，登记留档；不采用任何 .text/.rdata 二进制补丁。 |
| D. 是否存在 Unicode/UTF-16 字符串？ | **是。** 全部 UI 资源（String/Menu/Dialog 文本）均为 UTF-16LE，可直接写入中文，无需编码转换；仅 RT_240 为 ANSI（后续单独处理）。 |
| E. 中文字体显示预计是否正常？ | **正常。** 对话框字体为标准 GUI 字体（MS Shell Dlg/Segoe UI 系），Windows 对中文有字体回退（YaHei 系）；资源 LANGID 保持不变即可。风险主要是**宽度差异导致的截断**，用 `UI_LAYOUT_ISSUES.md` 跟踪。 |

结论：**PHASE 0 判定——汉化可行，推荐进入 PHASE 1（基础菜单 + 主要对话框）。**

## 9. 推荐工具链

| 工具 | 用途 | 状态 |
|---|---|---|
| `scripts/extract_resources.py` | 只读资源扫描/导出（本项目自研，纯标准库） | ✅ 已就绪并自测 |
| `scripts/verify.py` | 基线固化 + 汉化版/原版逐节哈希对照 | ✅ 已就绪并自测 |
| `scripts/apply_translation.py` | 读取 CSV → 同尺寸原位改写 RT_STRING/RT_MENU/RT_DIALOG | PHASE 1 开发 |
| Python 3.12 | 运行环境 | ✅ 本机 3.12.5 |
| Git + GitHub CLI（gh） | 版本管理与审核流程 | ✅ 已登录 |
| Resource Hacker（可选） | 人工抽查资源的 GUI 对照工具（**仅核对用，不参与生成**） | 按需 |

## 10. 风险点

1. **数字签名失效**：修改后 Arm EV 签名必然无效（HashMismatch）。首次启动可能有
   SmartScreen/杀软提示。如实记录，不伪造签名、不绕过安全机制。
2. **同尺寸约束**：中文若超长会被拒绝写入（宁可缩短措辞），避免破坏资源布局。
3. **结构化模板**：`%sptions for Target` 复用模板、`\t` 快捷键段、`&` 助记键、
   `\n` 分段提示，改写脚本必须逐项校验，`verify.py` 会复查。
4. **多语言副本**：2057(en-GB) 与 1033 同 ID 并存，漏改 2057 会导致部分文本不生效。
5. **运行时注入文本**：个别标题（对话框空标题、动态菜单项）由代码注入，
   资源级汉化无法覆盖，属已知边界（预计 <10% UI）。
6. **布局截断**：中文更窄一般不会截断，但按钮/复选框可能偏挤，走 `UI_LAYOUT_ISSUES.md`。
7. **版本升级**：Keil 更新后需重新提取/diff/迁移（本项目 CSV + 脚本即为此设计）。
8. **授权红线**：License Management 字符串、FlexNet、.text、调试器 DLL、工具链
   全部不动；`&Device Database…`、`License &Management...` 等授权相关文本**保留英文**。

## 11. 下一步计划（PHASE 1 提案，待批准）

1. `translations/keil_translation.csv`：从 `resource_inventory.json` 导出 PHASE 1 范围
   （主菜单 11 个标题 + File/Edit/View/Project/Flash/Debug 一级与二级菜单项 + 主要对话框标题，
   约 300–500 条），按 `TRANSLATION_GLOSSARY.md` 规范翻译。
2. 开发 `scripts/apply_translation.py`：同尺寸原位改写 + 结构校验 + 长度守卫。
3. 工作副本流程：官方 `UV4.exe` → `output/UV4_CN.exe`（全程不覆盖原版）。
4. `verify.py` 双文件对照：确认 `.text/.rdata/.data/.reloc` 逐字节一致、仅 `.rsrc` 变化。
5. 用户按 `docs/TEST_REPORT.md` 矩阵实测（TEST 1–15）+ 编译一致性对比。
6. 生成 `docs/CHANGELOG.md` 条目、commit、push、REVIEW HANDOFF，STOP 等审核。
