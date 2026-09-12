# CHANGELOG

格式：日期 / 阶段 / 提交 / 修改内容 / 涉及 Resource ID / 新增翻译条目 / 已知问题 / 测试状态。

## 2026-09-13 — PHASE 0.1 REVIEW FIXES（GPT 第一轮审核结论：CHANGES REQUESTED）

- **fix: harden verifier section comparison and add whole-file diff guard**
  - 修复 `verify.py compare()` 中 `names` 变量复用（节名被资源类型名覆盖）导致
    "代码节变化可能被误报为一致"的缺陷：拆分 `section_names` / `resource_names`；
  - 受保护节判定直接基于 `changed_sections` 与固定集合
    `PROTECTED_SECTIONS = {.text, .rdata, .data, .pdata, CODE, DATA}`；
  - 节比较内部使用**完整 SHA256**（仅打印截短）；受保护节 / 非允许区域任何变化
    → **FAIL + 退出码 1**（不再只是打印警告）；
  - 新增**整文件 byte-level changed-range 审计**：要求文件大小一致；
    DOS 头 / PE-COFF / Optional / 节表 / .text / .rdata / .data / .reloc /
    证书表 / overlay 必须逐字节一致；所有变化字节必须落在 .rsrc；
    输出 `changed_byte_count` / `changed_ranges` / `changed_regions`。
- **fix: honor menu template header offsets**
  - RT_MENU (version 0)：首项位置改为 `4 + MENUITEMTEMPLATEHEADER.offset`；
  - MENUEX (version 1)：按 `MENUEX_TEMPLATE_HEADER`（WORD wVersion、WORD wOffset、
    DWORD dwHelpId）实现，首项位置 `4 + wOffset`，不再硬编码；
  - 重扫描 UV4.exe：**version 0 = 40、version 1 = 0、header_offset 全为 0、
    parse errors = 0**，此前的菜单分析结论不变（修复为预防性正确）。
- **fix/feat: add RT_STRING reserializer and verifier/parser self-tests**
  - 新增 `serialize_string_table()`：整块重序列化（PHASE 1A 写入路径，
    替代已废弃的逐字符串尾部零填充）；
  - 新增 `tests/test_selftest.py`：VERIFY-1..5 全部通过（6/6），临时 PE 在系统
    临时目录生成与销毁，不进 Git。
- **docs: revise phase 1 resource rewrite strategy**
  - ANALYSIS.md：废弃"逐字符串同尺寸尾部零填充"，改为 resource-level
    reserialization；PHASE 1 拆分 **1A（仅 RT_STRING，20–40 条）**与 1B+；
    RT_MENU version 直方图与 parse errors=0 入档；新增非常规 LANGID 调查
    （LANGID 9→对话框 641、8192→859、1031→807/811 均为英文用户 UI 且无其他
    语言副本，纳入 1B+ 策略；8192 动手前需再次确认；1041 不动）。
- **涉及 Resource ID**：仍仅分析/自测，未修改任何 Keil 二进制。
- **新增翻译条目**：无。
- **已知问题**：无新增（ANALYSIS.md §10 风险清单更新）。
- **测试状态**：VERIFY-1..5 6/6 通过；`verify.py` CLI 对照（原版 vs 备份）退出码 0；
  GUI 测试不适用（未生成修改后的二进制）。
- **Git**：tag `v0.1-analysis` 保持指向 50b5147 不动（历史审核基线）。

## 2026-09-13 — PHASE 0（tag: v0.1-analysis）

- **修改内容**
  - 初始化项目骨架（.gitignore / LICENSE / README / 术语表 / 各文档）。
  - 新增 `scripts/extract_resources.py`：只读 PE 资源扫描器（节表、资源树、
    String/Menu/Dialog/Accelerator 解码、探针字符串→所属资源映射、硬编码扫描）。
  - 新增 `scripts/verify.py`：基线固化 + 双文件逐节哈希对照（用于验证
    "汉化只改 .rsrc、代码节逐字节一致"）。
  - 完成 UV4 5.43.1.0 基线固化与资源分析（`docs/BASELINE.md`、`docs/ANALYSIS.md`）。
  - 原版备份：`C:\Keil_v5\UV4\Backup_Original\` 与项目 `backup/`（均 gitignored）。
- **涉及 Resource ID**：仅只读分析，未修改任何资源。
- **新增翻译条目**：无（PHASE 1 生成 `keil_translation.csv`）。
- **已知问题**：见 `docs/ANALYSIS.md` §10 风险点。
- **测试状态**：
  - ✅ `verify.py` 基线模式自测通过（SHA256、节表哈希、资源计数）。
  - ✅ 246 个对话框 / 40 个菜单模板全部解析成功，0 告警。
  - ⛔ GUI 测试：不适用（纯分析阶段，未生成任何修改后的二进制）。
