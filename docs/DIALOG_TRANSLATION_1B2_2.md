# PHASE 1B2.2 批次报告 — 工程与目标管理 Dialog 群（8 个）

- 日期：2026-09-13 ｜ 基线：µVision 5.43.1.0（SHA256 校验通过）
- 范围：RT_DIALOG 128/132/135/139/147/170/614/2047（均 LANGID 1033）
- 规则不变：仅 Dialog title / BUTTON·STATIC string title；locator 三重校验；
  整资源重序列化；logical ≤ 原分配；allocation padding 纯 00。

## 尺寸汇总（实测序列化）

| Dialog | 标题 | Original | Logical | Pad | Fits |
|---|---|---|---|---|---|
| 128 | 工程内文件 | 398 | 346 | 52 | YES |
| 132 | 组 / 添加文件 | 490 | 418 | 72 | YES |
| 135 | 文件扩展名 | 860 | 688 | 172 | YES |
| 139 | 获取 '%s' 的文件类型 | 362 | 340 | 22 | YES |
| 147 | 选项 | 472 | 408 | 64 | YES |
| 170 | 器件 | 1188 | 1016 | 172 | YES |
| 614 | 管理运行时环境 | 440 | 388 | 52 | YES |
| 2047 | MDK Version 5: 器件支持 | 1564 | 1400 | 164 | YES |

全部为无损编解码器实测序列化值。

## 逐控件翻译表

### Dialog 128 — 工程内文件

| Index | ID | Class | Original | Chinese |
|---|---|---|---|---|
| title | — | — | `Files in Project` | `工程内文件` |
| 0 | 4294967295 | STATIC | `&Select Group:` | `选择组(&S):` |
| 2 | 4294967295 | STATIC | `&Files in Groups:` | `组内文件(&F):` |
| 4 | 1017 | BUTTON | `&Add Files...` | `添加文件(&A)...` |

不翻译：控件 3（SysTreeView32，工程树运行时数据）。

### Dialog 132 — 组 / 添加文件

| Index | ID | Class | Original | Chinese |
|---|---|---|---|---|
| title | — | — | `Groups / Add Files` | `组 / 添加文件` |
| 0 | 4294967295 | BUTTON | ` &Group to Add: ` | ` 要添加的组(&G): ` |
| 2 | 1007 | BUTTON | `&Add` | `添加(&A)` |
| 3 | 4294967295 | BUTTON | ` &Available Groups: ` | ` 可用组(&A): ` |
| 5 | 1022 | BUTTON | `&Add Files to Group...` | `向组添加文件(&A)...` |
| 6 | 1021 | BUTTON | `&Remove Group` | `移除组(&R)` |

### Dialog 135 — 文件扩展名

| Index | ID | Class | Original | Chinese |
|---|---|---|---|---|
| title | — | — | `File Extensions` | `文件扩展名` |
| 0 | 4294967295 | STATIC | ` Default File Type Extensions:` | ` 默认文件类型扩展名:` |
| 1 | 4294967295 | STATIC | `C Source File:` | `C 源文件:` |
| 3 | 4294967295 | STATIC | `C++ Source File:` | `C++ 源文件:` |
| 5 | 4294967295 | STATIC | `Asm Source File:` | `汇编源文件:` |
| 7 | 4294967295 | STATIC | `Object File:` | `目标文件:` |
| 9 | 4294967295 | STATIC | `Library File:` | `库文件:` |
| 11 | 4294967295 | STATIC | `Document File:` | `文档文件:` |
| 13 | 4294967295 | STATIC | `PL/M Source File:` | `PL/M 源文件:` |

不翻译：EDIT 控件中的扩展名数据（运行时数据）。

### Dialog 139 — 获取 '%s' 的文件类型

| Index | ID | Class | Original | Chinese |
|---|---|---|---|---|
| title | — | — | `Get Filetype for '%s'` | `获取 '%s' 的文件类型` |
| 0 | 4294967295 | STATIC | `File:` | `文件:` |
| 2 | 4294967295 | STATIC | `Type:` | `类型:` |
| 4 | 1 | BUTTON | `&OK` | `确定(&O)` |
| 5 | 2 | BUTTON | `&Cancel` | `取消(&C)` |

标题含 `%s`（运行时文件名），printf token 保留。

### Dialog 147 — 选项

| Index | ID | Class | Original | Chinese |
|---|---|---|---|---|
| title | — | — | `Options` | `选项` |
| 0 | 4294967295 | STATIC | `Target:` | `目标:` |
| 4 | 4294967295 | STATIC | `Translators Command Line:` | `翻译器命令行:` |
| 6 | 1 | BUTTON | `OK` | `确定` |
| 7 | 2 | BUTTON | `Cancel` | `取消` |

### Dialog 170 — 器件

| Index | ID | Class | Original | Chinese |
|---|---|---|---|---|
| title | — | — | `Device` | `器件` |
| 0 | 4294967295 | STATIC | `Vendor:` | `厂商:` |
| 2 | 4294967295 | STATIC | `Device:` | `器件:` |
| 4 | 4294967295 | STATIC | `Toolset:` | `工具集:` |
| 6 | 4294967295 | STATIC | `Search:` | `搜索:` |
| 9 | 4294967295 | STATIC | `Des&cription:` | `描述(&C):` |
| 13 | 1605 | BUTTON | `Use Extended &Linker (LX51) instead of BL51` | `使用扩展链接器(&L)替代 BL51` |
| 14 | 1606 | BUTTON | `Use Extended &Assembler (AX51) instead of A51 ` | `使用扩展汇编器(&A)替代 A51` |
| 15 | 4294967295 | STATIC | `&Select Toolset:` | `选择工具集(&S)` |

KEEP：控件 8（`Static` 占位文本）；[1]/[3]/[5]（Vendor/Device/Toolset 运行时值，
`<unknown>` 占位）。控件 11 `&Data base con&tents:` 双助记键结构特殊，本轮 KEEP。

### Dialog 614 — 管理运行时环境

| Index | ID | Class | Original | Chinese |
|---|---|---|---|---|
| title | — | — | `Manage Run-Time Environment` | `管理运行时环境` |
| 0 | 1 | BUTTON | `OK` | `确定` |
| 1 | 2 | BUTTON | `Cancel` | `取消` |
| 3 | 57670 | BUTTON | `Help` | `帮助` |

不翻译：控件 2/4/5（MfcButton 自定义类：Resolve/Details/Select Packs，首轮禁改）。

### Dialog 2047 — MDK Version 5: 器件支持

| Index | ID | Class | Original | Chinese |
|---|---|---|---|---|
| title | — | — | `MDK Version 5: Device Support` | `MDK Version 5: 器件支持` |
| 0 | 1 | BUTTON | `OK` | `确定` |
| 1 | 2 | BUTTON | `Cancel` | `取消` |
| 2 | 4294967295 | STATIC | `Install Software Pack with device support and select device` | `安装包含器件支持的 Software Pack 并选择器件` |
| 3 | 4294967295 | STATIC | `Device:` | `器件:` |
| 4 | 4294967295 | STATIC | `Vendor:` | `厂商:` |
| 8 | 10003 | STATIC | `The device support for MDK Version 5 is provided as Software Pack.` | `MDK Version 5 的器件支持以 Software Pack 形式提供。` |
| 9 | 4294967295 | STATIC | `Project:` | `工程:` |

不翻译：[5]/[6]/[10]（器件名/厂商名/工程名为运行时替换的 DYNAMIC 静态文本）、
[7] MfcLink、[11]–[14]（引导性英文长句，本轮保守未译，记录为后续候选）。

## 助记键与冲突

各 Dialog 同级助记键 after-set 与 before-set 一致（无新增冲突）；
原文无 `&` 的控件中文不加助记键（数量一致规则）。

## 明确未包含（后续批次候选）

- Target 属性页三变体 142/163/178（架构归属需 GUI 来源实证 —— 风险边界第 10 条）
- 375 Editor 设置页（62 控件，规模大，单独一批）
- 2047 控件 11–14（引导性英文长句）
- 170 控件 11（双助记键结构）
