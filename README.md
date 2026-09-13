# Keil µVision 中文汉化项目 v1.0

**Keil µVision 5.43.1.0 资源级安全汉化** —— 通过修改 Windows PE 资源（RT_STRING / RT_MENU / RT_DIALOG）实现 µVision IDE 界面中文化。

**本仓库不提供、也绝不存储任何 Keil / Arm 软件二进制。** 用户使用自己合法安装的官方 UV4.exe，配合本仓库的脚本与翻译数据，在**本地**生成仅供个人使用的汉化版。

```
官方原版 UV4.exe（用户自备）
        +
translations/keil_translation.csv (827 条翻译)
        +
scripts/ 自动化工具链
        ↓
本地生成 UV4_CN_RC3_1.exe
```

## 安全红线

- 只修改 **UI 资源**（RT_STRING / RT_MENU / RT_DIALOG，LANGID 1033）
- 不修改 .text / .rdata / .data / .reloc / PE 头 / 证书表
- 不触碰许可证 / 授权 / FlexNet / 工具链 / 调试器 DLL
- 不伪造签名；不绕过安全机制
- 原版 UV4.exe 必须先备份

## 使用

```bash
# 1. 确认版本（必须 5.43.1.0）
python scripts/verify.py backup/UV4_5.43.1.0_ORIGINAL.exe

# 2. 生成汉化版
python scripts/apply_translation.py

# 3. 校验（只改 .rsrc，其余逐字节一致）
python scripts/verify.py backup/UV4_5.43.1.0_ORIGINAL.exe output/UV4_CN_RC3_1.exe --manifest output/uv4_cn_rc3_1_manifest.json
```

## 状态

| 阶段 | 内容 | 状态 |
|---|---|---|
| PHASE 0 | 资源分析与可行性 | ✅ 完成 |
| PHASE 1B1/1B2.x | RT_STRING/MENU/DIALOG 翻译 | ✅ 完成 |
| PHASE 1B3 | 全量补漏 + RC1 | ✅ 完成 |
| **v1.0** | **827 条翻译，覆盖 6 大功能区** | ✅ **发布** |

## 目录

```
translations/  翻译数据库 (827 条)
scripts/       工具链 (extract/apply/verify/mapper)
docs/          分析报告/测试报告/映射表
tests/         自动化测试
```

## Known Limitations

| 类别 | 说明 |
|---|---|
| .rdata 驱动文本 | Project Targets: / Groups: / Files: 标签、编辑器右键 Go To 家族 |
| Shell/Runtime | Property Sheet 标题/按钮（OK/Cancel/Help/Defaults）、sheet title |
| Driver DLL | CMSIS-DAP Target Driver Setup、Flash Download 页面 |
| 特殊 LANGID | 9/1031/1041/2057/0x2000 未纳入 v1.0 |
| License/Legal | About 版权/授权文本、License Management 保持英文 |
| Colors & Fonts | Window/Element 预定义列表部分保持英文 |

## Supported Version

µVision **5.43.1.0**（SHA256 `428baf13…c42f89`）—— 其他版本需重新走 PHASE 0 流程。
