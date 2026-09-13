# 运行时菜单文本来源映射 (PHASE 1B1.1)

- 日期：2026-09-13 ｜ **只读调查**，未修改任何文件、未生成任何补丁
- 工具：`scripts/map_dynamic_strings.py`（六路来源搜索：RT_STRING / RT_MENU /
  RT_DIALOG(只查) / RT_240 / .rdata UTF-16 / .rdata ANSI + command ID 关联分析）
- 原始证据：`output/dynamic_menu_mapping.json`（本地）

## 背景

1B1 真机 GUI：主菜单与文件标签右键大量汉化成功，但**编辑器右键**与**工程树右键（根/组）**
的相当多条目仍为英文，而对应 RT_MENU/RT_STRING 条目已是中文。
结论：µVision 在 `WM_INITMENUPOPUP` / `ON_UPDATE_COMMAND_UI` 阶段用
`CCmdUI::SetText()` / `LoadString()` 动态改写菜单文本。本报告定位每条 GUI 文本的真实来源。

## 关键发现（MFC 动态覆盖假设 → 证实，共三种机制）

1. **隐藏/未覆盖的菜单资源**：
   - `MENU 22565 'Popups'`：标准 MFC 编辑命令弹出骨架（cmd 57643 Undo / 57644 Redo /
     57635 Cut / 57634 Copy / 57637 Paste / 57642 Select All）—— 编辑器右键中
     Undo/Redo/Cut/Copy/Paste/Select All 的静态来源，1B1 未覆盖。
   - `MENU 191 / 800 'DbWinMenu'`：**编辑器/窗口右键的真身**（1B1 汉化的 MENU 1200
     不是 GUI 实际加载的那份）——`Insert/Remove &Breakpoint`(cmd 32765, 0/8)、
     `&Enable/Disable Breakpoint`(cmd 35017, 0/9)、`Insert/Remove Bookmark\tCtrl+F2`
     (cmd 45267, 0/17) 等均未翻译。
   - `MENU 592 / 624 'Context'`：**工程树组/根上下文菜单**（与文件上下文 MENU 143
     同 command ID 但为独立未翻译副本）——Project Tree "部分汉化"的直接原因。
2. **LoadString / prompt 第二段机制**：菜单项 caption 运行时从 RT_STRING 加载
   （prompt 格式为 `长提示\n短标题`，第二段即菜单文本）：
   `159 New µ&Vision Project...`、`744 Remo&ve Item`、`164 Stop b&uild`、
   `167 &Erase`、`104/181 Source Browser 两项`、`5763x 系列` —— 1B1 均未翻译。
3. **.rdata ANSI 字面量 → CCmdUI::SetText**：`@0x7C0790-0x7C0AA8` 连续块内
   `Split Window horizontally`(0x7C0800)、`Toggle Header/Code File`(0x7C0848)、
   `Update Source Browser Information`(0x7C0878)、`Enable/Disable Breakpoint`(0x7C089C)、
   `Insert/Remove Breakpoint`(0x7C08B8)、`Go To Definition of '%s'`(0x7C08E8)、
   `Go To Previous/Next Reference To '%s'`(0x7C0904/0x7C0928)、
   `Go To Definition Of '%s'`(0x7C0948)、`Show All References of '%s'`(0x7C0964)、
   `Go To Previous/Next Reference of '%s'`(0x7C0980/0x7C09A4)、
   `Go To Declaration of '%s'`(0x7C09C4)、`Redo`(0x7C09E0)、`Undo`(0x7C09E8)、
   `Insert/Remove Bookmark`(0x7C09F0)、`Select All`(0x7C0A2C)、`Paste`(0x7C0A38)、
   `Copy`(0x7C0A40)。
   **按现行红线（禁改 .rdata），这些条目无法通过资源层汉化，维持英文**；
   是否放开属未来专项决策（需 GPT 批准并单独评估风险）。

## 映射表

| GUI 文本 | 出现位置 | 分类 | 来源证据（资源 ID / LANGID / 原文 / 是否已翻译） |
|---|---|---|---|
| Split Window horizontally | 编辑器右键 | **D .rdata ANSI** | `.rdata@0x7C0800`；RT_STRING/RT_MENU 无命中 |
| Toggle Header/Code File | 编辑器右键 | **D .rdata ANSI** | `.rdata@0x7C0848` |
| Insert/Remove Breakpoint | 编辑器右键 | **A+B+D 多源** | RT_STRING 1033 id=770 `I&nsert/Remove Breakpoint`（未译）；MENU 191/800 0/8 cmd=32765（未译）；prompt 32765 第二段 `Insert/Remove Breakpoint`；`.rdata@0x7C08B8` |
| Enable/Disable Breakpoint | 编辑器右键 | **A+B+D 多源** | RT_STRING id=771（未译）；MENU 191/800 0/9 cmd=35017（未译）；`.rdata@0x7C089C` |
| Refresh Source Browser View | 编辑器右键 | **A 静态 RT_STRING（未译）** | id=181（未译）；AC6 变体 id=464 |
| Update Source Browser Information | 编辑器右键 | **A 静态 RT_STRING（未译）** | id=104（未译）；AC6 变体 id=493 |
| Go To Definition of '%s' | 编辑器右键 | **D .rdata ANSI 模板** | `.rdata@0x7C08E8 "Go To Definition of '%s'"`（另有 Of 大写变体 @0x7C0948） |
| Go To Declaration of '%s' | 编辑器右键 | **D .rdata ANSI 模板** | `@0x7C09C4` |
| Go To Next Reference of '%s' | 编辑器右键 | **D .rdata ANSI 模板** | `@0x7C09A4`（To 变体 @0x7C0928） |
| Go To Previous Reference of '%s' | 编辑器右键 | **C+D** | RT_STRING 1033 id=35521 `Go To &Previous Reference of '%s'`（未译模板）+ `.rdata@0x7C0980` |
| Show All References of '%s' | 编辑器右键 | **D .rdata ANSI 模板** | `@0x7C0964` |
| Insert/Remove Bookmark | 编辑器右键 | **B+A+D 多源** | MENU 191/800 0/17 cmd=45267 `Insert/Remove Bookmark\tCtrl+F2`（未译，GUI 实际来源）；MENU 1200 0/2/0（已译但非 GUI 所用）；RT_STRING 147（已译）；`.rdata@0x7C09F0` |
| Undo | 编辑器右键 | **B+A+D 多源** | MENU 22565 0/0 cmd=57643 `&Undo`（未译）；RT_STRING 57643 prompt 第二段 `Undo`；20628 `&Undo\tCtrl+Z`（未译）；140（已译，非此菜单所用）；`.rdata@0x7C09E8` |
| Redo | 编辑器右键 | **B+D** | MENU 22565 0/1 cmd=57644（未译）；`.rdata@0x7C09E0` |
| Cut | 编辑器右键 | **B+A+D** | MENU 22565 0/3 cmd=57635（未译）；RT_STRING 20629（未译）；prompt 57635 第二段；`.rdata` |
| Copy | 编辑器右键 | **B+A+D** | MENU 22565 0/4、191/800 0/19 cmd=57634（未译）；RT_STRING 20630（未译）；`.rdata@0x7C0A40` |
| Paste | 编辑器右键 | **B+A+D** | MENU 22565 0/5 cmd=57637（未译）；RT_STRING 20631（未译）；`.rdata@0x7C0A38` |
| Select All | 编辑器右键 | **B+A+D** | MENU 22565 0/7 cmd=57642（未译）；MENU 400 0/0 `Select All\tCtrl+A`；RT_STRING 20633 `Select &All`（未译）、prompt 57642/202 第二段；`.rdata@0x7C0A2C` |
| Options for Target 'rt-thread'... | 工程树右键/Project 菜单 | **C 动态格式串（RT_STRING）** | id=749 `%sptions for Target '%s'%s%s` —— 渲染为 `O` + `ptions for Target 'rt-thread'` + `` + `...`；另有 9 处 .rdata ANSI 'Options for Target' |
| Add Group... | 工程树右键 | **B（未译副本）+D** | MENU 143 0/4（已译，文件上下文）；根上下文用未译来源：MENU 592/624 同 cmd=35481 副本 + `.rdata ANSI 'Add Group...'` |
| Manage Project Items... | 工程树右键 | **B（未译副本）+D** | MENU 143 0/6（已译）；MENU 592 0/9、624 0/4 cmd=32704（未译）；`.rdata ANSI` |
| Open Map File | 工程树右键 | **B（未译副本）+D** | MENU 143 0/10（已译）；MENU 624 0/8 cmd=32699（未译）；`.rdata ANSI` |
| Open Build Log | 工程树右键 | **B（未译副本）+D** | MENU 143 0/11（已译）；MENU 624 0/9 cmd=2081（未译）；`.rdata ANSI` |
| Show Include File Dependencies | 工程树右键 | **B（未译副本）+D** | MENU 143 0/18（已译）；MENU 592 0/11、624 0/16 cmd=35409（未译）；`.rdata ANSI` |
| New µVision Project... | Project 菜单 | **A 静态 RT_STRING（未译）** | id=159 `New µ&Vision Project...`（1B1 漏项）—— Project 菜单首项运行时 LoadString(159) |
| Remove Item | Project 菜单 | **A+B** | RT_STRING id=744 `Remo&ve Item`（未译，GUI 实际来源）；MENU 143 0/5（已译） |
| Translate... | Project 菜单 | **A 静态 RT_STRING（未译）** | id=162 `Tr&anslate...\tCtrl+F7` |
| Stop build | Project 菜单 | **A+B** | RT_STRING id=164 `Stop b&uild`（未译）；MENU 592 0/7、624 0/14 cmd=32721（未译） |
| Erase | Flash 菜单 | **A 静态 RT_STRING（未译）** | id=167 `&Erase`（未译）；prompt 35405 第二段 `Erase` |

## Command ID 映射（cmd → 静态菜单文本 → 运行时可见 → 快捷键）

| Command ID | 静态菜单文本（所在资源） | 运行时可见文本 | 快捷键 |
|---|---|---|---|
| 57643 (ID_EDIT_UNDO) | `&Undo`（MENU 22565 0/0） | Undo（英文） | Ctrl+Z（RT_ACCELERATOR） |
| 57644 (ID_EDIT_REDO) | `&Redo`（MENU 22565 0/1） | Redo | Ctrl+Shift+Z |
| 57635 (ID_EDIT_CUT) | `Cu&t`（22565 0/3；21215 0/0） | Cut | Ctrl+X |
| 57634 (ID_EDIT_COPY) | `&Copy`（22565 0/4；191/800 0/19；427 0/1；21215 0/1） | Copy | Ctrl+C |
| 57637 (ID_EDIT_PASTE) | `&Paste`（22565 0/5；21215 0/2） | Paste | Ctrl+V |
| 57642 (ID_EDIT_SELECT_ALL) | `Select &All`（22565 0/7） | Select All | Ctrl+A |
| 32765 | `Insert/Remove &Breakpoint`（191/800 0/8，未译） | Insert/Remove Breakpoint | — |
| 35017 | `&Enable/Disable Breakpoint`（191/800 0/9，未译） | Enable/Disable Breakpoint | — |
| 45267 | `Insert/Remove Bookmark\tCtrl+F2`（191/800 0/17，未译） | Insert/Remove Bookmark | Ctrl+F2 |
| 32704 | `Mana&ge Project Items...`（143 已译；592/624 未译副本） | 中文（文件上下文）/ 英文（根上下文） | — |
| 32699 | `Open &Map File`（143 已译；624 0/8 未译） | 同上规律 | — |
| 2081 | `Op&en Build Log`（143 已译；624 0/9 未译） | 同上规律 | — |
| 35409 | `Show I&nclude File Dependencies`（143 已译；592/624 未译） | 同上规律 | — |
| 35481 | `A&dd Group...`（143 已译） | Add Group...（根上下文） | — |
| — (模板) | RT_STRING 749 `%sptions for Target '%s'%s%s` | Options for Target 'rt-thread'... | Alt+F7 |

> 同一 Command ID 同时对应：RT_MENU 静态文本（可多份副本，143 已译而 592/624 未译）+
> RT_STRING command/prompt（如 5763x 系列 prompt 第二段）+ 运行时动态文本
> （.rdata ANSI 字面量）——三种来源并存，已在上表逐项标注。

## 结论与 1B1.2 候选（仅记录，未经批准不执行）

- **可经资源层修复（静态 RT_STRING / RT_MENU）**：
  RT_STRING：159、162、164、167、744、770、771、104、181、20628–20633、
  57643/57644/57634/57635/57637/57642（prompt 第二段）；RT_MENU：592、624
  （工程树组/根上下文）、191、800（DbWinMenu）、22565（隐藏编辑弹出）、400。
- **资源层无法覆盖（.rdata ANSI 驱动，维持英文）**：Split Window horizontally、
  Toggle Header/Code File、Go To Definition/Declaration/References of '%s' 家族、
  Show All References of '%s'，以及上述条目在编辑器右键中的最终显示
  （若运行时以 .rdata 字面量 SetText 为准）。是否放开 .rdata 属未来专项决策。
- RT_DIALOG / .rdata / .text / DLL：本阶段零接触。
