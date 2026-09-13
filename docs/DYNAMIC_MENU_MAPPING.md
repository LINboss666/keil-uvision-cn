# 运行时菜单文本来源映射 (PHASE 1B1.1 / 1B1.1a)

- 生成方式：**完全由 `scripts/map_dynamic_strings.py` 自动生成**（分类由结构化
  evidence 集合自动推导，人工覆盖数 = 0），重新运行即可复现。
- 日期：2026-09-13 ｜ **只读调查**，未修改任何文件、未生成任何补丁
- 基线：输入文件 SHA256 已由脚本校验，绑定 µVision 5.43.1.0
  （`428baf13…c42f89`，见 `docs/BASELINE.md`）。

## 背景与方法

1B1 真机 GUI：主菜单与文件标签右键大量汉化成功，但**编辑器右键**与
**工程树右键（根/组）**的相当多条目仍为英文，而对应 RT_MENU/RT_STRING 条目
已是中文 —— 即 GUI 最终文本与静态资源不完全一致。

**运行时动态文本覆盖假设获得强证据支持，且行为与 MFC CCmdUI update mechanism
一致**（Microsoft MFC 官方允许 `WM_INITMENUPOPUP` / `ON_UPDATE_COMMAND_UI` /
`CCmdUI::SetText()` 动态修改菜单文本）。当前证据能证明的是：

- A. GUI 最终文本与静态 RT_MENU/RT_STRING 不完全一致；
- B. `.rdata` 中存在与 GUI 完全一致的 ANSI literal / format template；
- C. MFC 官方机制允许上述动态修改。

未经动态 tracing 或 call-site 分析，**不声称**某个具体 `.rdata` 地址
"已被证明传给 `CCmdUI::SetText()`"；下表中的 `.rdata` 偏移仅作为
"存在完全匹配 literal" 的证据记录。

搜索源（六路）：RT_STRING / RT_MENU / RT_DIALOG(只查) / RT_240 /
.rdata 等节 UTF-16LE / .rdata 等节 ANSI，外加 command ID → 同 ID
RT_STRING → RT_ACCELERATOR 关联。

## 自动映射表

| GUI 文本 | 出现位置 | 自动分类 | 证据（结构化 evidence 摘要） |
|---|---|---|---|

| Split Window horizontally | 编辑器右键 | D .rdata 硬编码(ANSI) | RAW ANSI @file+0x7C0800 [.rdata] (literal): 'Split Window horizontally' |
| Toggle Header/Code File | 编辑器右键 | D .rdata 硬编码(ANSI) | RAW ANSI @file+0x7C0848 [.rdata] (literal): 'Toggle Header/Code File' |
| Insert/Remove Breakpoint | 编辑器右键 | A 静态RT_STRING(未译)+B 静态RT_MENU(未译)+D .rdata 硬编码(ANSI)+RT_240(列头) | RT_STRING id=770 lang=1033 [exact]: 'I&nsert/Remove Breakpoint' <br> RT_MENU id=191 lang=1033 path=0/8 cmd=32765 [exact]: 'Insert/Remove &Breakpoint' <br> RT_MENU id=800 lang=1033 path=0/8 cmd=32765 [exact]: 'Insert/Remove &Breakpoint' <br> RT_240 id=487 lang=None [contains]: 'Remove' <br> RAW UTF-16LE @file+0xB86C26 [.rsrc] (literal): 'Insert/Remove Breakpoint' <br> RAW UTF-16LE @file+0xB8EBB0 [.rsrc] (literal): 'Insert/Remove Breakpoint' |
| Enable/Disable Breakpoint | 编辑器右键 | A 静态RT_STRING(未译)+B 静态RT_MENU(未译)+D .rdata 硬编码(ANSI) | RT_STRING id=771 lang=1033 [exact]: '&Enable/Disable Breakpoint' <br> RT_MENU id=191 lang=1033 path=0/9 cmd=35017 [exact]: '&Enable/Disable Breakpoint' <br> RT_MENU id=800 lang=1033 path=0/9 cmd=35017 [exact]: '&Enable/Disable Breakpoint' <br> RAW UTF-16LE @file+0x9666A8 [.rsrc] (literal): 'Enable/Disable Breakpoint' <br> RAW UTF-16LE @file+0x966AF6 [.rsrc] (literal): 'Enable/Disable Breakpoint' <br> RAW UTF-16LE @file+0xB90810 [.rsrc] (literal): 'Enable/Disable Breakpoint' |
| Refresh Source Browser View | 编辑器右键 | A 静态RT_STRING(未译)+D .rdata 硬编码(ANSI) | RT_STRING id=181 lang=1033 [exact]: 'Refresh Source Browser View' <br> RT_STRING id=464 lang=1033 [contains]: 'Refresh Source Browser View (only AC6)' <br> RAW UTF-16LE @file+0xB91574 [.rsrc] (literal): 'Refresh Source Browser View' <br> RAW UTF-16LE @file+0xB970BA [.rsrc] (literal): 'Refresh Source Browser View' <br> RAW ANSI @file+0x7AA020 [.rdata] (literal): 'Refresh Source Browser View' |
| Update Source Browser Information | 编辑器右键 | A 静态RT_STRING(未译)+D .rdata 硬编码(ANSI) | RT_STRING id=104 lang=1033 [exact]: 'Update Source Browser Information' <br> RT_STRING id=493 lang=1033 [contains]: 'Update Source Browser Information (only AC6)' <br> RAW UTF-16LE @file+0xB912AC [.rsrc] (literal): 'Update Source Browser Information' <br> RAW UTF-16LE @file+0xB96FDA [.rsrc] (literal): 'Update Source Browser Information' <br> RAW ANSI @file+0x7C0878 [.rdata] (literal): 'Update Source Browser Information' |
| Go To Definition of 'main' | 编辑器右键 | D .rdata 硬编码(ANSI) | RAW ANSI @file+0x7C08E8 [.rdata] (template-prefix): "Go To Definition of '" |
| Go To Declaration of 'main' | 编辑器右键 | D .rdata 硬编码(ANSI) | RAW ANSI @file+0x7C09C4 [.rdata] (template-prefix): "Go To Declaration of '" |
| Go To Next Reference of 'main' | 编辑器右键 | D .rdata 硬编码(ANSI) | RAW ANSI @file+0x7C09A4 [.rdata] (template-prefix): "Go To Next Reference of '" |
| Go To Previous Reference of 'main' | 编辑器右键 | C 动态格式串(RT_STRING)+D .rdata 硬编码(ANSI) | RT_STRING id=35521 lang=1033 [template]: "Go To &Previous Reference of '%s'" <br> RAW ANSI @file+0x7C0980 [.rdata] (template-prefix): "Go To Previous Reference of '" |
| Show All References of 'main' | 编辑器右键 | D .rdata 硬编码(ANSI) | RAW ANSI @file+0x7C0964 [.rdata] (template-prefix): "Show All References of '" |
| Insert/Remove Bookmark | 编辑器右键 | A 静态RT_STRING[contains](已译→GUI仍英文,疑似运行时覆盖)+B 静态RT_MENU(已译→GUI仍英文,疑似运行时覆盖)+D .rdata 硬编码(ANSI)+RT_240(列头) | RT_STRING id=147 lang=1033 [contains]: '&Insert/Remove Bookmark\tCtrl+F2' <br> RT_MENU id=191 lang=1033 path=0/17 cmd=45267 [contains]: 'Insert/Remove Bookmark\tCtrl+F2' <br> RT_MENU id=800 lang=1033 path=0/17 cmd=45267 [contains]: 'Insert/Remove Bookmark\tCtrl+F2' <br> RT_MENU id=1200 lang=1033 path=0/2/0 cmd=33021 [exact]: '&Insert/Remove Bookmark' <br> RT_240 id=487 lang=None [contains]: 'Remove' <br> RAW UTF-16LE @file+0x96689E [.rsrc] (literal): 'Insert/Remove Bookmark' |
| Undo | 编辑器右键 | A 静态RT_STRING[contains](已译→GUI仍英文,疑似运行时覆盖)+B 静态RT_MENU(未译)+D .rdata 硬编码(ANSI)+RT_DIALOG 静态文本 | RT_STRING id=140 lang=1033 [contains]: '&Undo\tCtrl+Z' <br> RT_STRING id=20628 lang=1033 [contains]: '&Undo\tCtrl+Z' <br> RT_STRING id=57643 lang=1033 [contains]: 'Undo the last action\nUndo' <br> RT_STRING id=17102 lang=2057 [contains]: 'Undo %d Actions' <br> RT_STRING id=17103 lang=2057 [contains]: 'Undo 1 Action' <br> RT_MENU id=22565 lang=1033 path=0/0 cmd=57643 [exact]: '&Undo' |
| Redo | 编辑器右键 | A 静态RT_STRING[contains](已译→GUI仍英文,疑似运行时覆盖)+B 静态RT_MENU(未译)+D .rdata 硬编码(ANSI) | RT_STRING id=141 lang=1033 [contains]: '&Redo\tCtrl+Shift+Z' <br> RT_MENU id=22565 lang=1033 path=0/1 cmd=57644 [exact]: '&Redo' <br> RAW UTF-16LE @file+0xB856BA [.rsrc] (literal): 'Redo' <br> RAW UTF-16LE @file+0xB8D506 [.rsrc] (literal): 'Redo' <br> RAW UTF-16LE @file+0xB903CC [.rsrc] (literal): 'Redo' <br> RAW UTF-16LE @file+0xB90408 [.rsrc] (literal): 'Redo' |
| Cut | 编辑器右键 | A 静态RT_STRING[contains](已译→GUI仍英文,疑似运行时覆盖)+B 静态RT_MENU(未译)+RT_240(列头) | RT_STRING id=142 lang=1033 [contains]: 'Cu&t\tCtrl+X' <br> RT_STRING id=676 lang=1033 [contains]: '&Cut Current Line' <br> RT_STRING id=775 lang=1033 [contains]: 'Execut&ion Profiling' <br> RT_STRING id=20629 lang=1033 [contains]: 'Cu&t\tCtrl+X' <br> RT_STRING id=32791 lang=1033 [contains]: 'Start code execution\nRun' <br> RT_STRING id=32797 lang=1033 [contains]: 'Stop code execution\nStop' |
| Copy | 编辑器右键 | A 静态RT_STRING[contains](已译→GUI仍英文,疑似运行时覆盖)+B 静态RT_MENU(未译)+D .rdata 硬编码(ANSI)+RT_DIALOG 静态文本 | RT_STRING id=143 lang=1033 [contains]: '&Copy\tCtrl+C' <br> RT_STRING id=20630 lang=1033 [contains]: '&Copy\tCtrl+C' <br> RT_STRING id=16907 lang=2057 [contains]: 'Copy Tool\nCopy' <br> RT_MENU id=191 lang=1033 path=0/19 cmd=57634 [exact]: '&Copy' <br> RT_MENU id=427 lang=1033 path=0/1 cmd=35127 [exact]: '&Copy' <br> RT_MENU id=800 lang=1033 path=0/19 cmd=57634 [exact]: '&Copy' |
| Paste | 编辑器右键 | A 静态RT_STRING[contains](已译→GUI仍英文,疑似运行时覆盖)+B 静态RT_MENU(未译)+D .rdata 硬编码(ANSI) | RT_STRING id=144 lang=1033 [contains]: '&Paste\tCtrl+V' <br> RT_STRING id=20631 lang=1033 [contains]: '&Paste\tCtrl+V' <br> RT_STRING id=16908 lang=2057 [contains]: 'Paste Tool\nPaste' <br> RT_MENU id=21215 lang=1033 path=0/2 cmd=57637 [exact]: '&Paste' <br> RT_MENU id=21217 lang=1033 path=1/3 cmd=57637 [contains]: '&Paste\tCtrl+V' <br> RT_MENU id=22565 lang=1033 path=0/5 cmd=57637 [exact]: '&Paste' |
| Select All | 编辑器右键 | A 静态RT_STRING(未译)+B 静态RT_MENU(未译)+D .rdata 硬编码(ANSI)+RT_DIALOG 静态文本 | RT_STRING id=202 lang=1033 [contains]: 'Select the entire text\nSelect All' <br> RT_STRING id=20633 lang=1033 [exact]: 'Select &All' <br> RT_STRING id=57642 lang=1033 [contains]: 'Select the entire text\nSelect All' <br> RT_STRING id=202 lang=1041 [contains]: 'Select the entire text\nSelect All' <br> RT_STRING id=57642 lang=1041 [contains]: 'Select the entire text\nSelect All' <br> RT_MENU id=400 lang=1033 path=0/0 cmd=57642 [contains]: 'Select All\tCtrl+A' |
| Options for Target 'rt-thread'... | 工程树右键/Project 菜单 | C 动态格式串(RT_STRING)+D .rdata 硬编码(ANSI) | RT_STRING id=749 lang=1033 [template]: "%sptions for Target '%s'%s%s" <br> RAW ANSI @file+0x7BE7DC [.rdata] (template-prefix): "Options for Target '" <br> RAW ANSI @file+0x7CF5C7 [.rdata] (template-prefix): "Options for Target '" |
| Add Group... | 工程树右键 | B 静态RT_MENU(已译→GUI仍英文,疑似运行时覆盖)+D .rdata 硬编码(ANSI) | RT_MENU id=143 lang=1033 path=0/4 cmd=35481 [exact]: 'A&dd Group...' <br> RAW ANSI @file+0x7BE824 [.rdata] (literal): 'Add Group...' |
| Manage Project Items... | 工程树右键 | B 静态RT_MENU(已译→GUI仍英文,疑似运行时覆盖)+D .rdata 硬编码(ANSI) | RT_MENU id=143 lang=1033 path=0/6 cmd=32704 [exact]: 'Mana&ge Project Items...' <br> RT_MENU id=592 lang=1033 path=0/9 cmd=32704 [exact]: 'Mana&ge Project Items...' <br> RT_MENU id=624 lang=1033 path=0/4 cmd=32704 [exact]: 'Mana&ge Project Items...' <br> RAW ANSI @file+0x7BE834 [.rdata] (literal): 'Manage Project Items...' |
| Open Map File | 工程树右键 | B 静态RT_MENU(已译→GUI仍英文,疑似运行时覆盖)+D .rdata 硬编码(ANSI) | RT_MENU id=143 lang=1033 path=0/10 cmd=32699 [exact]: 'Open &Map File' <br> RT_MENU id=624 lang=1033 path=0/8 cmd=32699 [exact]: 'Open &Map File' <br> RAW ANSI @file+0x7BE8B0 [.rdata] (literal): 'Open Map File' |
| Open Build Log | 工程树右键 | B 静态RT_MENU(已译→GUI仍英文,疑似运行时覆盖)+D .rdata 硬编码(ANSI) | RT_MENU id=143 lang=1033 path=0/11 cmd=2081 [exact]: 'Op&en Build Log' <br> RT_MENU id=624 lang=1033 path=0/9 cmd=2081 [exact]: 'Op&en Build Log' <br> RAW ANSI @file+0x7BE8C0 [.rdata] (literal): 'Open Build Log' |
| Show Include File Dependencies | 工程树右键 | B 静态RT_MENU(已译→GUI仍英文,疑似运行时覆盖)+D .rdata 硬编码(ANSI) | RT_MENU id=143 lang=1033 path=0/18 cmd=35409 [exact]: 'Show I&nclude File Dependencies' <br> RT_MENU id=592 lang=1033 path=0/11 cmd=35409 [exact]: 'Show I&nclude File Dependencies' <br> RT_MENU id=624 lang=1033 path=0/16 cmd=35409 [exact]: 'Show I&nclude File Dependencies' <br> RAW ANSI @file+0x790480 [.rdata] (literal): 'Show Include File Dependencies' |
| New µVision Project... | Project 菜单 | A 静态RT_STRING(未译) | RT_STRING id=159 lang=1033 [exact]: 'New µ&Vision Project...' |
| Remove Item | Project 菜单/工程树 | A 静态RT_STRING(未译)+B 静态RT_MENU(已译→GUI仍英文,疑似运行时覆盖)+D .rdata 硬编码(ANSI)+RT_240(列头) | RT_STRING id=744 lang=1033 [exact]: 'Remo&ve Item' <br> RT_MENU id=143 lang=1033 path=0/5 cmd=35085 [exact]: 'R&emove Item' <br> RT_240 id=487 lang=None [contains]: 'Remove' <br> RAW UTF-16LE @file+0xB86EEA [.rsrc] (literal): 'Remove Item' <br> RAW UTF-16LE @file+0xB8EF2E [.rsrc] (literal): 'Remove Item' <br> RAW ANSI @file+0x7BE770 [.rdata] (literal): 'Remove Item' |
| Translate... | Project 菜单/工程树 | A 静态RT_STRING[contains](未译) | RT_STRING id=162 lang=1033 [contains]: 'Tr&anslate...\tCtrl+F7' |
| Stop build | Project 菜单/工程树 | A 静态RT_STRING(未译)+B 静态RT_MENU(已译→GUI仍英文,疑似运行时覆盖) | RT_STRING id=164 lang=1033 [exact]: 'Stop b&uild' <br> RT_MENU id=143 lang=1033 path=0/16 cmd=32721 [exact]: 'Stop b&uild' <br> RT_MENU id=592 lang=1033 path=0/7 cmd=32721 [exact]: 'Stop b&uild' <br> RT_MENU id=624 lang=1033 path=0/14 cmd=32721 [exact]: 'Stop b&uild' |
| Erase | Flash 菜单 | A 静态RT_STRING(未译)+D .rdata 硬编码(ANSI) | RT_STRING id=167 lang=1033 [exact]: '&Erase' <br> RT_STRING id=35405 lang=1033 [contains]: 'Erase flash memory\nErase' <br> RT_STRING id=57632 lang=1033 [contains]: 'Erase the selection\nErase' <br> RT_STRING id=57633 lang=1033 [contains]: 'Erase everything\nErase All' <br> RT_STRING id=57632 lang=1041 [contains]: 'Erase the selection\nErase' <br> RT_STRING id=57633 lang=1041 [contains]: 'Erase everything\nErase All' |
## Command ID 关联（脚本自动提取）

> "同 cmd" = 与命中菜单项共享 command ID 的其他资源证据
> （RT_STRING prompt / 其他菜单副本 / RT_ACCELERATOR 快捷键）。
> 完整明细见 `output/dynamic_menu_mapping.json`。

| Command ID | 同 ID 资源证据 |
|---|---|
| 2081 | RT_MENU:143:1033:'Op&en Build Log' |
| 2081 | RT_MENU:624:1033:'Op&en Build Log' |
| 32699 | RT_MENU:143:1033:'Open &Map File' |
| 32699 | RT_MENU:624:1033:'Open &Map File' |
| 32704 | RT_MENU:1204:1033:'Manage Books...' |
| 32704 | RT_MENU:143:1033:'Mana&ge Project Items...' |
| 32704 | RT_MENU:592:1033:'Mana&ge Project Items...' |
| 32704 | RT_MENU:624:1033:'Mana&ge Project Items...' |
| 32704 | RT_STRING:32704:1033:'Manage Project Items\nFile Extensions, Books and Environment...' |
| 32704 | RT_STRING:32704:1041:'プロジェクトに関する各種項目を管理します。\nプロジェクト各種項目...' |
| 32721 | RT_MENU:143:1033:'Stop b&uild' |
| 32721 | RT_MENU:592:1033:'Stop b&uild' |
| 32721 | RT_MENU:624:1033:'Stop b&uild' |
| 32721 | RT_STRING:32721:1033:'Cancel the current build\nStop Build' |
| 32721 | RT_STRING:32721:1041:'現在のビルド処理を停止します。\nビルドを停止' |
| 32765 | RT_MENU:191:1033:'Insert/Remove &Breakpoint' |
| 32765 | RT_MENU:800:1033:'Insert/Remove &Breakpoint' |
| 32765 | RT_STRING:32765:1033:'Insert or remove a breakpoint at the current line\nInsert/Remove Breakpoint' |
| 32765 | RT_STRING:32765:1041:'Insert or remove a breakpoint at the current line\nInsert/Remove Breakpoint' |
| 35017 | RT_MENU:191:1033:'&Enable/Disable Breakpoint' |
| 35017 | RT_MENU:800:1033:'&Enable/Disable Breakpoint' |
| 35017 | RT_STRING:35017:1033:'Enable or disable a breakpoint at the current line\nEnable/Disable Breakpoint' |
| 35017 | RT_STRING:35017:1041:'現在のカーソル行のブレークポイントを有効/無効にします。\nブレークポイントを有効化/無効化' |
| 35085 | RT_STRING:35085:1033:'Remove selected group or file\nRemove Item' |
| 35085 | RT_STRING:35085:1041:'Remove selected group or file\nRemove Item' |
| 35409 | RT_MENU:143:1033:'Show I&nclude File Dependencies' |
| 35409 | RT_MENU:592:1033:'Show I&nclude File Dependencies' |
| 35409 | RT_MENU:624:1033:'Show I&nclude File Dependencies' |
| 35409 | RT_STRING:35409:1033:'Show or hide include file dependencies\nInclude File Dependencies' |
| 35409 | RT_STRING:35409:1041:'Show or hide include file dependencies\nInclude File Dependencies' |
| 35481 | RT_STRING:35481:1033:'Create a new Project Group\nNew Group' |
| 35481 | RT_STRING:35481:1041:'Create a new Project Group\nNew Group' |
| 57634 | RT_MENU:191:1033:'&Copy' |
| 57634 | RT_MENU:21215:1033:'&Copy' |
| 57634 | RT_MENU:21217:1033:'&Copy\tCtrl+C' |
| 57634 | RT_MENU:22565:1033:'&Copy' |
| 57634 | RT_MENU:800:1033:'&Copy' |
| 57634 | RT_STRING:57634:1033:'Copy the selection to the clipboard\nCopy' |
| 57634 | RT_STRING:57634:1041:'選択したテキストをクリップボードにコピーします。\nコピー' |
| 57635 | RT_MENU:21215:1033:'Cu&t' |
| 57635 | RT_MENU:21217:1033:'Cu&t\tCtrl+X' |
| 57635 | RT_MENU:22565:1033:'Cu&t' |
| 57635 | RT_STRING:57635:1033:'Cut the selection and put it on the clipboard\nCut' |
| 57635 | RT_STRING:57635:1041:'選択したテキストをクリップボードに切り取ります。\n切り取り' |
| 57637 | RT_MENU:21215:1033:'&Paste' |
| 57637 | RT_MENU:21217:1033:'&Paste\tCtrl+V' |
| 57637 | RT_MENU:22565:1033:'&Paste' |
| 57637 | RT_STRING:57637:1033:'Insert clipboard contents\nPaste' |
| 57637 | RT_STRING:57637:1041:'テキストをクリップボードから貼り付けます。\n貼り付け' |
| 57642 | RT_MENU:400:1033:'Select All\tCtrl+A' |
| 57642 | RT_STRING:57642:1033:'Select the entire text\nSelect All' |
| 57642 | RT_STRING:57642:1041:'Select the entire text\nSelect All' |
| 57643 | RT_STRING:57643:1033:'Undo the last action\nUndo' |
| 57643 | RT_STRING:57643:1041:'直前の編集操作をキャンセルします。\n元に戻す' |
| 57644 | RT_STRING:57644:1033:'Redo the previous Undo action\nRedo' |
| 57644 | RT_STRING:57644:1041:'直前に元に戻した操作をやり直します。\nやり直し' |

## 结论与 1B1.2 候选（仅记录，未经批准不执行）

- **可经资源层修复（静态 RT_STRING / RT_MENU，候选清单）**：
  RT_STRING：159、162、164、167、744、770、771、104、181、20628–20633、
  57643/57644/57634/57635/57637/57642（command prompt，须整条处理：
  保留 newline 分段数 / 格式 token / 快捷键文本，不得只 raw patch "第二段"）；
  RT_MENU：592、624（工程树组/根上下文）、191、800（DbWinMenu）、
  22565（隐藏编辑弹出）、400。
- **资源层无法覆盖（.rdata literal 强证据，维持英文）**：Split Window horizontally、
  Toggle Header/Code File、Go To Definition/Declaration/References of '%s' 家族、
  Show All References of '%s'，以及最终被 .rdata runtime text 覆盖的其它项
  （以 1B1.2 GUI 测试实录为准）。是否放开 .rdata 属 **PHASE 2 — EXPERIMENTAL
  RDATA LOCALIZATION** 专项决策，当前禁止实施。
- RT_DIALOG / .rdata / .text / DLL：本阶段零接触。


## PHASE 1B1 GUI 实测补充（2026-09-13 最终验证，本节为实测记录，不改变上表自动分类）

1B1.2 构建版真机测试结果与上表映射的对照：

- **映射命中并生效**：`New µVision Project...`（id 159）→ 新建 µVision 工程 ✓；
  `Stop build`（id 164 / MENU 592·624·143）→ 停止编译 ✓；`Erase`（id 167）→ 擦除 ✓；
  Build/Rebuild/Batch Build 等既有条目保持中文 ✓。
- **仍英文且与 .rdata exact/template evidence 一致 → `runtime override likely`**：
  Split Window horizontally、Toggle Header/Code File、Go To Definition/Declaration/
  Next·Previous Reference of '%s'、Show All References of '%s'、
  Insert/Remove Breakpoint、Enable/Disable Breakpoint、Insert/Remove Bookmark、
  Undo/Redo/Cut/Copy/Paste/Select All（编辑器右键）。
- **仍英文但来源属动态格式串家族（未在 1B1.2 范围）**：
  `Options for Target/Group/File...`（RT_STRING 749–755 复用模板家族）、
  `Remove File ...`（id 745 `Remo&ve File '%s'`）、`Translate <filepath> ...`
  （id 752–754 家族）—— Project Window context menu 按 Target/Group/File
  当前对象动态适配。
- **unresolved runtime source**：`Refresh Source Browser View`
  （RT_STRING 181 已翻译，GUI 仍英文）→ runtime override likely，
  按 GPT 指示不在 PHASE 1B1 继续深挖。
- 措辞约束：resource-vs-GUI behavior strongly supports runtime command-UI text
  replacement, consistent with MFC ON_UPDATE_COMMAND_UI / CCmdUI::SetText
  mechanism；不声称具体 .rdata 地址已证明传入 SetText。
