# Colors & Fonts 列表来源映射 (PHASE 1B2.5 RC3.2)

- 日期：2026-09-13 ｜ **只读调查**，零修改
- 工具：`output/colors_fonts_map.py`（六路搜索 + owner 归属）
- 原始证据：`output/colors_fonts_mapping.json`

## 结论

Colors & Fonts 页的两个运行时列表（Window / Element）的内容 **绝大部分来自
.rdata ANSI 硬编码或运行时构造**，不属于 RT_STRING / RT_DIALOG 安全资源。

**仅 6 个 Window 项 + 4 个 Element 项** 存在 RT_STRING 1033 资源层来源，
但这些 RT_STRING 条目同时被菜单/工具栏 prompt 使用（多用途共享），
翻译它们会改变状态栏和菜单提示文本，而非仅影响 Colors & Fonts 列表。

## 安全评估

即使 RT_STRING 资源可达，这些字符串**很可能同时用于**：
- profile name / 配置键（注册表保存颜色设置时的 key）
- string comparison / lookup table identifier（Colors & Fonts 内部匹配）

**无法证明 display-only** → **DEFER**。

如果未来允许实验修改，必须验证：
A. 选择所有 Window 项正常
B. 选择所有 Element 项正常
C. 修改颜色后 Apply/OK 正常
D. 退出并重启 µVision 后颜色设置仍能恢复
E. 切回英文原版读取同一配置仍正常

## 明细

### Window 列表

| 文本 | 分类 | 来源 |
|---|---|---|
| All Editors | **.rdata DEFER** | .rdata ANSI |
| Asm Editor files | unknown | 无命中 |
| C/C++ Editor files | unknown | 无命中 |
| Build Output Window | RT_STRING 1033 | id=35033（prompt，多用途） |
| Debug (printf) Viewer | RT_STRING 1033 | id=713（prompt，多用途） |
| Disassembly Window | RT_STRING 1033 | id=32752/697（prompt，多用途） |
| Editor Text files | unknown | 无命中 |
| Logic Analyzer | RT_STRING 1033 | id=35429/35446（prompt，多用途） |
| Memory Window | RT_STRING 1033 | id=271/704（prompt，多用途） |
| UART #1 Window | **.rdata DEFER** | .rdata ANSI |
| UART #2 Window | **.rdata DEFER** | .rdata ANSI |
| UART #3 Window | **.rdata DEFER** | .rdata ANSI |

### Element 列表

| 文本 | 分类 | 来源 |
|---|---|---|
| Caret Line | **.rdata DEFER** | .rdata ANSI |
| Text Selection | **.rdata DEFER** | .rdata ANSI |
| Right Margin | **.rdata DEFER** | .rdata ANSI + RT_DIALOG 375 |
| Default | RT_STRING 1033 | 多处 RT_DIALOG/STRING（多用途） |
| Comment | RT_STRING 1033 | 多处 RT_DIALOG/STRING（多用途） |
| Number | RT_STRING 1033 | 多处（多用途） |
| String | RT_STRING 1033 | 多处（多用途） |
| Operator | **.rdata DEFER** | .rdata ANSI |
| Identifier | **.rdata DEFER** | .rdata ANSI |
| CPU Instruction | unknown | 无命中 |
| FPU Instruction | unknown | 无命中 |
| Assembler Directive | unknown | 无命中 |
| Assembler Directive Operand | unknown | 无命中 |
| Comment Block (e.g. GNU) | unknown | 无命中 |
| Character/String (single quote) | unknown | 无命中 |
| Register / User Keywords / Label | unknown | 无命中 |

## 统计

| 分类 | Window | Element | 合计 |
|---|---|---|---|
| RT_STRING 1033 (资源可达但多用途共享) | 4 | 4 | 8 |
| .rdata (DEFER) | 4 | 5 | 9 |
| unknown (运行时构造) | 2 | 7 | 9 |
| **合计** | **12** | **16** | **28** |

**Safe-to-translate count: 0**（RT_STRING 命中项为多用途共享，翻译影响面不可控）
**Deferred count: 9** (.rdata 硬编码)
**Unknown count: 9** (运行时构造)

## 建议

**DEFER 全部 Colors & Fonts 列表项。** 这些字符串大概率同时用于内部
lookup/profile/配置键，翻译风险远大于收益。如果未来 GPT 决定做专项实验
（PHASE 2），必须先完成上述 A-G 安全测试矩阵。
