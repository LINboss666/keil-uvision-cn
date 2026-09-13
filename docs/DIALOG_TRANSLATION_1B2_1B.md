# PHASE 1B2.1b1 候选表 — Manage Project Items 1033 资源汉化

- 日期：2026-09-13 ｜ 基线：µVision 5.43.1.0（SHA256 校验通过）
- 范围：RT_STRING 32704 + RT_DIALOG 465/466/468（均 LANGID 1033）
- 禁改：RT_DIALOG 859 (0x2000)、.rdata、.text、RT_240、DLL
- 全部尺寸为无损编解码器实际序列化结果。

## RT_STRING 32704 — 属性表标题 / 菜单 command prompt（整条处理）

| 段 | Original | Chinese |
|---|---|---|
| 1 | `Manage Project Items` | `管理工程项目` |
| 2 | `File Extensions, Books and Environment...` | `设置文件扩展名、书籍和开发环境...` |

newline 分段 2→2；无 printf / `\t` / 助记键。该 prompt 同时影响
菜单状态栏提示与属性表标题来源（预期资源级变化）。

## RT_DIALOG 465 — Project Items page

Original 416 B → Logical **352 B**（pad 64）｜ Fits: YES
翻译：title `Project Items`→`工程项目`；ctl:3/4/5 三个 BUTTON（见下）。
**不可达项**：`Project Targets:` / `Groups:` / `Files:` 三个列表标签为
.rdata/runtime 绘制（.rdata ANSI exact 命中），资源层不可达 → PARTIAL BY DESIGN。

| Index | ID | Class | Original | Chinese |
|---|---|---|---|---|
| title | — | — | `Project Items` | `工程项目` |
| 3 | 1728 | BUTTON | `&Set as Current Target` | `设为当前目标(&S)` |
| 4 | 1729 | BUTTON | `&Add Files...` | `添加文件(&A)...` |
| 5 | 1730 | BUTTON | `Add Files as &Image...` | `添加文件为图像(&I)...` |

不翻译：LISTBOX ×3（运行时工程数据）。

## RT_DIALOG 466 — Folders/Extensions page（46 控件）

Original 2384 B → Logical **2052 B**（pad 332）｜ Fits: YES

| Index | ID | Class | Original | Chinese | Status |
|---|---|---|---|---|---|
| title | — | — | `Folders/Extensions` | `文件夹/扩展名` | TRANSLATE |
| 0 | 1534 | BUTTON | `&Use Settings from TOOLS.INI:` | `使用 TOOLS.INI 中的设置(&U):` | TRANSLATE |
| 1 | 4294967295 | STATIC | `Tool Base Folder:` | `工具基础目录:` | TRANSLATE |
| 2 | 1539 | EDIT | — | — | DYNAMIC |
| 3 | 4294967295 | STATIC | `&BIN:` | — | KEEP |
| 4 | 1535 | EDIT | — | — | DYNAMIC |
| 5 | 4294967295 | STATIC | `&INC:` | — | KEEP |
| 6 | 1536 | EDIT | — | — | DYNAMIC |
| 7 | 4294967295 | STATIC | `&LIB:` | — | KEEP |
| 8 | 1537 | EDIT | — | — | DYNAMIC |
| 9 | 4294967295 | STATIC | `&Regfile:` | — | KEEP |
| 10 | 1538 | EDIT | — | — | DYNAMIC |
| 11 | 4294967295 | STATIC | `C Source:` | `C 源文件:` | TRANSLATE |
| 12 | 1722 | EDIT | — | — | DYNAMIC |
| 13 | 4294967295 | STATIC | `C++ Source:` | `C++ 源文件:` | TRANSLATE |
| 14 | 1723 | EDIT | — | — | DYNAMIC |
| 15 | 4294967295 | STATIC | `Asm Source:` | `汇编源文件:` | TRANSLATE |
| 16 | 1724 | EDIT | — | — | DYNAMIC |
| 17 | 4294967295 | STATIC | `Object:` | `目标文件:` | TRANSLATE |
| 18 | 1725 | EDIT | — | — | DYNAMIC |
| 19 | 4294967295 | STATIC | `Library:` | `库文件:` | TRANSLATE |
| 20 | 1726 | EDIT | — | — | DYNAMIC |
| 21 | 4294967295 | STATIC | `Document:` | `文档:` | TRANSLATE |
| 22 | 1727 | EDIT | — | — | DYNAMIC |
| 23 | 1543 | BUTTON | `Use ARM Compiler` | `使用 ARM 编译器` | TRANSLATE |
| 24 | 1542 | BUTTON | `Use &GCC Compiler (GNU) for ARM projects` | `ARM 工程使用 &GCC 编译器 (GNU)` | TRANSLATE |
| 25 | 4294967295 | STATIC | `ARMCC Folder:` | `ARMCC 目录:` | TRANSLATE |
| 26 | 1541 | EDIT | — | — | DYNAMIC |
| 27 | 4294967295 | STATIC | `Prefi&x:` | `前缀(&X):` | TRANSLATE |
| 28 | 1814 | EDIT | — | — | DYNAMIC |
| 29 | 4294967295 | STATIC | `Folder:` | `目录:` | TRANSLATE |
| 30 | 1540 | EDIT | — | — | DYNAMIC |
| 31 | 1546 | BUTTON | `U&se Keil CARM` | `使用 Keil CARM(&S)` | TRANSLATE (legacy/条件显示) |
| 32 | 2006 | STATIC | `CMSIS Folder:` | `CMSIS 目录:` | TRANSLATE |
| 33 | 1544 | EDIT | — | — | DYNAMIC |
| 34 | 4294967295 | STATIC | `Select ARM Development Tools:` | `选择 ARM 开发工具:` | TRANSLATE |
| 35 | 2008 | STATIC | `RL-ARM Folder:` | `RL-ARM 目录:` | TRANSLATE |
| 36 | 1545 | EDIT | — | — | DYNAMIC |
| 37 | 4294967295 | STATIC | `Development Tool Folders:` | `开发工具目录:` | TRANSLATE |
| 38 | 2007 | STATIC | `RTX-ARM Folder:` | `RTX-ARM 目录:` | TRANSLATE |
| 39 | 1548 | EDIT | — | — | DYNAMIC |
| 40 | 4294967295 | STATIC | `Default File Extensions:` | `默认文件扩展名:` | TRANSLATE |
| 41 | 1549 | EDIT | — | — | DYNAMIC |
| 42 | 2105 | BUTTON | `...` | — | KEEP |
| 43 | 4294967295 | BUTTON | — | — | DYNAMIC (无 title) |
| 44 | 4294967295 | BUTTON | — | — | DYNAMIC (无 title) |
| 45 | 1223 | BUTTON | `Setup Default ARM Compiler Version` | `设置默认 ARM 编译器版本` | TRANSLATE |

KEEP 项：`&BIN:` `&INC:` `&LIB:` `&Regfile:`（技术缩写，保留原标签形式）
与 `...`（纯省略号按钮）。EDIT 全部 DYNAMIC（用户路径数据，禁改）。

## RT_DIALOG 468 — Books page（14 控件）

Original 672 B → Logical **596 B**（pad 76）｜ Fits: YES

| Index | ID | Class | Original | Chinese | Status |
|---|---|---|---|---|---|
| title | — | — | `Books` | `书籍` | TRANSLATE |
| 0 | 4294967295 | STATIC | `File:` | `文件:` | TRANSLATE |
| 1/2/3 | 1732/1540/1734 | EDIT | — | — | DYNAMIC |
| 4/5/6 | 1729/1730/1731 | LISTBOX | — | — | DYNAMIC |
| 7 | 4294967295 | STATIC | `Default Root:` | `默认根目录:` | TRANSLATE |
| 8 | 1733 | EDIT | — | — | DYNAMIC |
| 9 | 4294967295 | STATIC | `Default Root:` | `默认根目录:` | TRANSLATE |
| 10 | 1050 | EDIT | — | — | DYNAMIC |
| 11 | 4294967295 | STATIC | `Default Root:` | `默认根目录:` | TRANSLATE |
| 12 | 1051 | EDIT | — | — | DYNAMIC |
| 13 | 1223 | BUTTON | `New/Change Book...` | `新建/更改书籍...` | TRANSLATE |

三个 `Default Root:` 重复项分别按 control_index（7/9/11）定位。
EDIT/LISTBOX 中的书名/路径/项目内容完全不变。

## 汇总

| Dialog | Original | Logical | Pad | Fits |
|---|---|---|---|---|
| 465 | 416 | 352 | 64 | YES |
| 466 | 2384 | 2052 | 332 | YES |
| 468 | 672 | 596 | 76 | YES |
| RT_STRING 32704 | — | — | — | （prompt 整条，2 段结构保留） |
