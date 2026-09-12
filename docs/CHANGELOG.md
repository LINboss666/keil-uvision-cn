# CHANGELOG

格式：日期 / 阶段 / 提交 / 修改内容 / 涉及 Resource ID / 新增翻译条目 / 已知问题 / 测试状态。

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
