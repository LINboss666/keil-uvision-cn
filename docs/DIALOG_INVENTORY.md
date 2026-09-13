# RT_DIALOG 资源清单 (PHASE 1B2.0)

- 由 `scripts/dialog_inventory.py` 自动生成（只读；基线 SHA256 校验通过，绑定 µVision 5.43.1.0）。原始数据：`output/dialog_inventory.json`（本地）。
- round-trip 门禁：**246/246 byte-identical**（parse → serialize）。
- parse warnings：0（要求 0）。

| 统计项 | 值 |
|---|---|
| RT_DIALOG total | 246 |
| Standard DLGTEMPLATE | 52 |
| Extended DLGTEMPLATEEX | 194 |
| LANGID histogram | {"1033": 218, "2057": 24, "9": 1, "1031": 2, "8192": 1} |
| Controls total | 3389 |
| DS_SETFONT | 246 |
| DS_SHELLFONT | 62 |
| dialogs with menu | 0 |
| dialogs with custom windowClass | 0 |
| ordinal control classes | 3327 |
| string control classes | 62 |
| ordinal titles | 5 |
| string titles | 2307 |
| nonzero creation data | 0 |
| dialogs with trailing bytes | 0 |
| max trailing bytes | 0 |
| total trailing bytes | 0 |
| dialogs with NONZERO trailing | 0 |
| candidate slack (trailing 全 00) | 0 |


nonzero creation data：**无**（std size_bytes 与 ex extraCount 均为 0，UV4 样本不触发两种 size 语义差异；语义仍按微软标准分别实现并由合成 fixture 锁定）。

## 可识别的重要 Dialog（标题/控件文本关键词匹配）

- `100` lang=1033 title='About µVision' controls=10 关键词=['About', 'License']
- `129` lang=1033 title='Targets' controls=8 关键词=['Target']
- `142` lang=1033 title='Target' controls=47 关键词=['Target']
- `147` lang=1033 title='Options' controls=8 关键词=['Target']
- `152` lang=1033 title='L66 Locate' controls=21 关键词=['Target']
- `162` lang=1033 title='' controls=2 关键词=['Target']
- `163` lang=1033 title='Target' controls=65 关键词=['Target']
- `164` lang=1033 title='Database' controls=20 关键词=['Device']
- `170` lang=1033 title='Device' controls=20 关键词=['Device']
- `172` lang=1033 title='Output' controls=42 关键词=['Flash', 'Target']
- `173` lang=1033 title='C51' controls=28 关键词=['Pack']
- `178` lang=1033 title='Target' controls=49 关键词=['Target']
- `182` lang=1033 title='C251' controls=28 关键词=['Pack']
- `183` lang=1033 title='Target' controls=64 关键词=['Target']
- `184` lang=1033 title='L251 Locate' controls=14 关键词=['Target']
- `187` lang=1033 title='L51 Locate' controls=29 关键词=['Target']
- `188` lang=1033 title='Properties' controls=26 关键词=['Target']
- `209` lang=1033 title='Debug' controls=55 关键词=['Component']
- `397` lang=1033 title='PC-Lint Options' controls=13 关键词=['Target']
- `443` lang=1033 title='Device' controls=21 关键词=['Device', 'Pack']
- `446` lang=1033 title='Utilities' controls=27 关键词=['Flash', 'Target']
- `451` lang=1033 title='Target' controls=32 关键词=['Target']
- `453` lang=1033 title='Output' controls=39 关键词=['Flash', 'Target']
- `461` lang=1033 title='Linker' controls=28 关键词=['Target']
- `465` lang=1033 title='Project Items' controls=6 关键词=['Target']
- `473` lang=1033 title='Single-User License' controls=17 关键词=['License']
- `483` lang=1033 title='Target' controls=38 关键词=['Target']
- `490` lang=1033 title='LA Locate' controls=14 关键词=['Target']
- `495` lang=1033 title='Floating License Users' controls=5 关键词=['License']
- `500` lang=1033 title='Target' controls=89 关键词=['Target']
- `502` lang=1033 title='Properties' controls=29 关键词=['Target']
- `511` lang=1033 title='Batch Setup' controls=11 关键词=['Target']
- `514` lang=1033 title='µVision Project Dependencies' controls=8 关键词=['Target']
- `612` lang=1033 title='µVision - Cannot access target hardware' controls=8 关键词=['Device', 'Target']
- `614` lang=1033 title='Manage Run-Time Environment' controls=6 关键词=['Pack', 'Run-Time Environment', 'Manage Run-Time']
- `616` lang=1033 title='RTE Component Properties' controls=12 关键词=['Component']
- `618` lang=1033 title='Properties' controls=18 关键词=['Pack', 'Target']
- `629` lang=1033 title='MDK Version 5: Device Support' controls=8 关键词=['Options for Target', 'Device', 'Pack', 'Target']
- `636` lang=1033 title='µVision Legacy Device Support' controls=10 关键词=['Device', 'Pack', 'Download']
- `638` lang=1033 title='Using an MDK Version 4 Project' controls=8 关键词=['Device', 'Pack', 'Download']
- `639` lang=1033 title='Using an MDK Version 4 Project' controls=8 关键词=['Device', 'Pack']
- `641` lang=9 title='Missing Device Information' controls=3 关键词=['Device']
- `801` lang=1033 title='MDK: Selected Software Component Requires Code Generation' controls=9 关键词=['Component']
- `807` lang=1031 title='Manage Component Viewer Description Files' controls=5 关键词=['Component']
- `819` lang=1033 title='PC-Lint Options' controls=20 关键词=['Pack']
- `823` lang=1033 title='Static Code Analysis - Analyzer Package Selection' controls=4 关键词=['Pack']
- `859` lang=8192 title='Project Info/Layer' controls=18 关键词=['License', 'Target']
- `2047` lang=1033 title='MDK Version 5: Device Support' controls=15 关键词=['Options for Target', 'Device', 'Pack', 'Select Device', 'Target', 'Download']
- `32700` lang=1033 title='L166 Locate' controls=21 关键词=['Target']
- `32706` lang=1033 title='Linker' controls=24 关键词=['Target']
- `32708` lang=1033 title='Output' controls=31 关键词=['Flash', 'Target']
- `32709` lang=1033 title='Target' controls=32 关键词=['Target']
- `32720` lang=1033 title='Floating License' controls=19 关键词=['License']
- `32721` lang=1033 title='Floating License Administrator' controls=9 关键词=['License']
- `32722` lang=1033 title='Checkout Floating-User License' controls=4 关键词=['License']
- `32730` lang=1033 title='FlexNet License' controls=19 关键词=['License']
- `32731` lang=1033 title='FlexLM License' controls=5 关键词=['License']
- `32737` lang=1033 title='µVision Device Support' controls=13 关键词=['Device', 'Pack', 'Download']
- `32738` lang=1033 title='Select Software Packs' controls=4 关键词=['Pack']
- `32739` lang=1033 title='Wait for Pack Installer' controls=4 关键词=['Pack']
- `32741` lang=1033 title='User-Based License' controls=17 关键词=['License']

## 状态

本阶段（PHASE 1B2.0）**只调查、不翻译**：未修改任何 RT_DIALOG payload，未生成任何汉化 EXE。后续正式 Dialog 汉化（PHASE 1B2.1，待批准）将只允许 Dialog title / Control title(text) 变化，其余字段以语义快照强制 identical。
