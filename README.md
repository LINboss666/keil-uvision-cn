# keil-uvision-cn

针对 **Keil µVision (MDK) 官方原版 UV4.exe** 的本地中文界面汉化项目。

**本仓库不提供、也绝不存储任何 Keil / Arm 软件二进制。**
用户使用自己合法安装的官方 UV4.exe，配合本仓库的脚本与翻译数据，
在**本地**生成仅供个人使用的汉化版 `UV4_CN.exe`。

```
官方原版 UV4.exe（用户自备）
        +
translations/ 翻译数据库 (CSV + 术语表)
        +
scripts/ 自动化脚本 (只读分析 / 应用翻译 / 校验)
        ↓
本地生成 output/UV4_CN.exe
```

## 目录结构

```
keil-uvision-cn/
├─ backup/                  # 原版备份 (gitignored, 不上传)
├─ translations/
│  ├─ glossary.json         # 统一术语表 (含"禁止翻译"清单)
│  └─ keil_translation.csv  # 翻译数据库: ResourceType,ResourceID,ItemRef,LANGID,Original,Chinese,Status,Notes
├─ scripts/
│  ├─ extract_resources.py  # 只读 PE 资源扫描器 (纯标准库)
│  └─ verify.py             # 基线固化 / 双文件逐节对照校验
├─ output/                  # 本地产物 (gitignored): 资源清单 JSON、UV4_CN.exe
├─ docs/
│  ├─ BASELINE.md           # 目标版本基线 (仅元数据与哈希)
│  ├─ ANALYSIS.md           # PHASE 0 资源分析报告
│  ├─ TRANSLATION_GLOSSARY.md
│  ├─ UI_LAYOUT_ISSUES.md   # 中文截断/布局问题跟踪
│  ├─ TEST_REPORT.md        # 每版本 GUI 测试矩阵结果
│  └─ CHANGELOG.md
└─ tests/                   # 自动验证脚本 (后续阶段)
```

## 用法（当前为 PHASE 0，仅分析）

```bash
# 1. 分析自己机器上的 UV4.exe（只读，不修改）
python scripts/extract_resources.py "C:\Keil_v5\UV4\UV4.exe" --json output\resource_inventory.json

# 2. 固化基线 / 校验汉化版只改了资源、代码节逐字节一致
python scripts/verify.py backup\UV4_5.43.1.0_ORIGINAL.exe
python scripts/verify.py backup\UV4_5.43.1.0_ORIGINAL.exe output\UV4_CN.exe   # 双文件对照
```

## 安全与合规底线

- 只修改 **UI 资源**（RT_STRING / RT_MENU / RT_DIALOG），不修改 `.text` 等代码节，
  不做任何二进制硬编码补丁，不触碰许可证 / 授权 / 加密逻辑与 FlexNet。
- 不绕过任何 Arm / Keil 安全机制；不伪造数字签名。
- 修改后 Arm EV 数字签名**必然失效**（预期行为，会在测试报告中如实记录）。
- 原版 UV4.exe 必须先备份（见 `docs/BASELINE.md`）。
- 不从第三方下载任何已汉化 / 已修改的 Keil 二进制。
- `.gitignore` 阻止一切 `.exe/.dll/.lic` 及 `backup/`、`output/` 进入版本库。

## 状态

| 阶段 | 内容 | 状态 |
|---|---|---|
| PHASE 0 | UV4 5.43.1.0 资源分析与可行性 | ✅ 完成（`docs/ANALYSIS.md`） |
| PHASE 0.1 | GPT 一轮审核修复（verifier 加固 / 菜单头 offset / 方案修订） | ✅ 完成（已审核通过） |
| PHASE 1A | 仅 RT_STRING 基础汉化（43 条，`UV4_CN_TEST.exe`） | ✅ IMPLEMENTED / ✅ STATIC VERIFIED / ✅ **USER HARDWARE TESTED / PASSED** |
| PHASE 1B1 | RT_MENU + 补充 RT_STRING（187 条，`UV4_CN_1B1_TEST.exe`） | ✅ 静态验证 PASS / 用户 GUI：写入机制 PASS，上下文菜单 PARTIAL（运行时覆盖已定位） |
| PHASE 1B1.1/.1a | 运行时来源调查 + mapping 工具加固 | ✅ 完成并审核通过（`DYNAMIC_MENU_MAPPING.md`） |
| PHASE 1B1.2 | resource-only menu completion（231 条，`UV4_CN_1B1_2_TEST.exe`） | ✅ **RESOURCE-LEVEL COMPLETE / USER HARDWARE TESTED / COVERAGE PARTIAL BY DESIGN**（1B1 关闭） |
| PHASE 1B2.0/.0a | 无损 RT_DIALOG 编解码器（246/246 byte-identical 门禁） | ✅ 完成并审核通过（含 1B2.0b 加固） |
| PHASE 1B2.1a | 首批 Dialog 烟雾测试（About/Targets/Batch Setup，20 条） | ✅ **STATIC PASS / GUI PASS / BUILD PASS**（1B2.1 关闭） |
| PHASE 1B2.1b0 | Manage Project Items 来源调查 | ✅ 完成并审核通过 |
| PHASE 1B2.1b1 | Manage Project Items 1033 汉化（32704 + 465/466/468） | ✅ 静态验证 PASS（并入 1B2.2 累积测试版） |
| PHASE 1B2.2 批次 | 工程与目标管理 Dialog 群 8 个（128/132/135/139/147/170/614/2047，+50 条） | 🔍 静态验证 PASS，待 GPT 审核 → 用户真机测试 |
| PHASE 1B+ | RT_MENU / 对话框 / Options for Target 等 | 未开始 |

## 环境

- Windows 10/11，Python 3.10+（脚本仅用标准库，无需 pip）
- Git + GitHub CLI（版本管理与审核流程，见 `docs/CHANGELOG.md`）
- 基线版本：µVision V5.43.1.0（MDK 5.43.0.0，ArmClang 6.24），
  见 `docs/BASELINE.md`；其他版本需重新提取资源并迁移翻译。
