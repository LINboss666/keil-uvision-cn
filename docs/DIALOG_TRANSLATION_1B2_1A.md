# PHASE 1B2.1a 候选报告 — 首批 Dialog 烟雾测试

- 日期：2026-09-13 ｜ 基线：µVision 5.43.1.0（SHA256 校验通过）
- 范围：仅 Dialog title / BUTTON·STATIC 控件的 string title；版权/版本/授权/
  法律文本保持原文；font / rect / ID / class / creation data 全部禁改。
- 全部尺寸预测由无损编解码器实际序列化计算（非估算）。

## 候选考察结论

| Resource ID | LANGID | Template | Original Size | Dialog Title | Font | DS_SHELLFONT | Controls | 决定 |
|---|---|---|---|---|---|---|---|---|
| 100 | 1033 | DLGTEMPLATEEX | 1084 B | `About µVision` | Arial 9pt (charset 0) | 否 | 10 | ✅ **入选**（标题 + OK） |
| 129 | 1033 | DLGTEMPLATEEX | 588 B | `Targets` | Microsoft Sans Serif 8pt (charset 1) | 否 | 8 | ✅ **入选**（标题 + 5 BUTTON + 1 组框） |
| 511 | 1033 | DLGTEMPLATEEX | 696 B | `Batch Setup` | MS Shell Dlg 8pt (charset 1) | **是** | 11 | ✅ **入选**（标题 + 10 BUTTON/STATIC） |
| 465 | 1033 | DLGTEMPLATEEX | 416 B | `Project Items` | Microsoft Sans Serif 8pt (charset 1) | 否 | 6 | ⏸ 暂缓（3 个已满足 5–20 条预算；下一批候选） |

不选择 License / FlexNet 专用窗口；Dialog 100 的版本号、版权、授权、法律条款
STATIC 文本**保持英文原文**，仅译标题与 OK 按钮。

## Dialog 100 — About µVision

- Resource ID 100 ｜ LANGID 1033 ｜ DLGTEMPLATEEX ｜ Original 1084 B
- Font: Arial, 9pt, charset 0 ｜ DS_SHELLFONT: no
- Serialized Size: **1080 B** ｜ Delta: −4 B ｜ Allocation Padding: 4 B ｜ **Fits: YES**

| Control Index | Control ID | Class | Original | Proposed Chinese |
|---|---|---|---|---|
| (dialog) | — | — | `About µVision` | `关于 µVision` |
| 9 | 1 | BUTTON | `OK` | `确定` |

不翻译：控件 1/2/4/6（版本、版权、授权、法律文本）、7 `Copy Info`、8 `Legal Notices`（本轮保守）、0/3/5（图标/空 STATIC）。

## Dialog 129 — Targets

- Resource ID 129 ｜ LANGID 1033 ｜ DLGTEMPLATEEX ｜ Original 588 B
- Font: Microsoft Sans Serif, 8pt, charset 1 ｜ DS_SHELLFONT: no
- Serialized Size: **472 B** ｜ Delta: −116 B ｜ Allocation Padding: 116 B ｜ **Fits: YES**

| Control Index | Control ID | Class | Original | Proposed Chinese |
|---|---|---|---|---|
| (dialog) | — | — | `Targets` | `目标` |
| 0 | 4294967295 | BUTTON (组框) | ` &Target to Add: ` | ` 要添加的目标(&T): ` |
| 2 | 1025 | BUTTON | `&Add` | `添加(&A)` |
| 3 | 1539 | BUTTON | `&Copy all Settings from Current Target` | `从当前目标复制全部设置(&C)` |
| 4 | 4294967295 | BUTTON (组框) | ` &Available Targets: ` | ` 可用目标(&A): ` |
| 6 | 1026 | BUTTON | `&Set as Current Target` | `设为当前目标(&S)` |
| 7 | 1023 | BUTTON | `&Remove Target` | `移除目标(&R)` |

不翻译：控件 1（EDIT）、5（LISTBOX）——首轮禁改非 BUTTON/STATIC 类。

## Dialog 511 — Batch Setup

- Resource ID 511 ｜ LANGID 1033 ｜ DLGTEMPLATEEX ｜ Original 696 B
- Font: MS Shell Dlg, 8pt, charset 1 ｜ DS_SHELLFONT: **yes**
- Serialized Size: **536 B** ｜ Delta: −160 B ｜ Allocation Padding: 160 B ｜ **Fits: YES**

| Control Index | Control ID | Class | Original | Proposed Chinese |
|---|---|---|---|---|
| (dialog) | — | — | `Batch Setup` | `批量编译设置` |
| 0 | 4294967295 | STATIC | `Select Project Targets:` | `选择工程目标:` |
| 2 | 1223 | BUTTON | `Build` | `编译` |
| 3 | 1862 | BUTTON | `Rebuild` | `重新编译` |
| 4 | 1863 | BUTTON | `Clean` | `清理` |
| 5 | 1864 | BUTTON | `Select All` | `全选` |
| 6 | 1865 | BUTTON | `Deselect All` | `取消全选` |
| 7 | 2 | BUTTON | `Cancel` | `取消` |
| 8 | 57670 | BUTTON | `&Help` | `帮助(&H)` |
| 9 | 1 | BUTTON | `Close` | `关闭` |
| 10 | 2253 | BUTTON | `Stop after first failing project` | `在首个失败工程后停止` |

不翻译：控件 1（SysTreeView32 自定义类，首轮禁改）。

## Locator 与守卫说明

- 定位器：`(ResourceID, LANGID, control_index)`，交叉校验 `control_id` /
  `control_class` / `Original` 三项，任一不一致 → FAIL。
  实战记录：本轮 locator 拦截 2 次 ID 转录错误
  （511 ctl:4 Clean 实为 1863 而非 1864；ctl:5 Select All 实为 1864 而非 1865）。
- 助记键：原文含 `&` 的保留原字母（&T/&A/&C/&S/&R/&H）；原文无 `&` 的
  （Build/Rebuild/Cancel/Select All 等）中文不加助记键（数量一致规则）。
- 511 ctl:5 与 ctl:6 同 Control ID 1865（Keil 原始资源如此）—— 按 control_index
  定位不受影响，这正是禁止仅用 Control ID 定位的原因。

## RESOURCE_TOO_LARGE 评估

三个入选 Dialog 序列化后均 **缩小**（−4 / −116 / −160 字节），
allocation padding 以纯 00 填充至原分配尺寸；Resource Data Entry size 保持原值；
无任何 .rsrc 扩展或资源移动。
