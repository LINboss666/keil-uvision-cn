#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
apply_translation.py — PHASE 1A: 官方原版 UV4.exe + 翻译数据库 → 本地 UV4_CN_TEST.exe

流程（全部满足 GPT 二轮审核的强制要求）:
    0. 输入文件 SHA256 必须 == 固定 baseline (docs/BASELINE.md);
    1. 从 ORIGINAL 的资源树解析 RT_STRING (BlockID, LANGID) → payload 范围,
       绝不信任 CSV/manifest 中人为记录的 file_offset;
    2. 读取 translations/keil_translation.csv (ResourceType=STRING 且 Status=DONE);
    3. 逐块: 完整解析 16 条 → 校验 实际文本 == CSV Original → 修改目标条目 →
       完整重序列化 16 条 → new_blob <= 原分配 (否则 RESOURCE_TOO_LARGE) →
       整块写回原偏移, 变短只在整块末尾补 0;
    4. 语义验证: 资源树布局不变; 每块仍 16 条; 目标 StringID == Chinese;
       同块未列入翻译表的字符串与原版完全一致; 其他一切资源逐字节一致;
    5. 写出 UV4_CN_TEST.exe 与 manifest JSON (供 verify.py --manifest 做载荷白名单审计)。

红线:
    * 不覆盖 C:\Keil_v5\UV4\UV4.exe; 不启动生成的测试版; 不触碰 .text/.rdata/.data/
      .reloc/头部/证书表; 不修改 RT_MENU/RT_DIALOG/RT_240/1041/0x2000 资源。

用法:
    python apply_translation.py [--original <UV4.exe>] [--csv <csv>] \
        [--output <exe>] [--manifest <json>]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_resources as er   # noqa: E402
import verify                     # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# docs/BASELINE.md 固化基线: µVision 5.43.1.0 官方原版
BASELINE_SHA256 = "428baf13d15e6760af1618def9c9815c97f0321cc5e459ec7adc4dde41c42f89"

DEFAULT_ORIGINAL = "backup/UV4_5.43.1.0_ORIGINAL.exe"
DEFAULT_CSV = "translations/keil_translation.csv"
DEFAULT_OUTPUT = "output/UV4_CN_TEST.exe"
DEFAULT_MANIFEST = "output/uv4_cn_test_manifest.json"

FORMAT_SPEC_RE = re.compile(r"%[-+ #0]*\d*(?:\.\d+)?[a-zA-Z]")


class ApplyError(Exception):
    """任何校验失败都以此异常中止, 不产出任何输出文件。"""


def find_string_blocks(pe: er.PEFile):
    """从 PE 资源树解析 RT_STRING (block_id, lang) -> (file_offset, size)。"""
    index = {}
    for r in er.flatten_resources(pe):
        if r["type_name"] == "RT_STRING" and r["name_kind"] == "id" and r["file_offset"]:
            index[(r["name"], r["lang"])] = (r["file_offset"], r["size"])
    return index


def load_translation_csv(path: Path):
    required = {"ResourceType", "ResourceID", "StringID", "LANGID",
                "Original", "Chinese", "Status"}
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ApplyError(f"CSV 缺少必需列: {sorted(missing)}")
        rows = list(reader)
    entries, skipped = [], 0
    for r in rows:
        if (r.get("Status") or "").strip().upper() != "DONE":
            continue
        if (r.get("ResourceType") or "").strip().upper() != "STRING":
            skipped += 1
            continue
        entry = {
            "block_id": int(r["ResourceID"]),
            "string_id": int(r["StringID"]),
            "lang": int(r["LANGID"]),
            "original": r["Original"],
            "chinese": r["Chinese"],
        }
        if entry["block_id"] != entry["string_id"] // 16 + 1:
            raise ApplyError(f"CSV 行 ResourceID 与 StringID 不自洽: {entry}")
        if not entry["chinese"]:
            raise ApplyError(f"Chinese 为空: StringID={entry['string_id']}")
        entries.append(entry)
    return entries, skipped


def check_format_invariants(original: str, chinese: str):
    """写入前的机械校验: printf 格式符与 \\t 必须一一对应。返回问题列表。"""
    problems = []
    so = sorted(FORMAT_SPEC_RE.findall(original))
    sc = sorted(FORMAT_SPEC_RE.findall(chinese))
    if so != sc:
        problems.append(f"printf 格式符不一致: 原文{so} vs 中文{sc}")
    if original.count("\t") != chinese.count("\t"):
        problems.append("\\t 数量不一致")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="PHASE 1A 翻译写入器")
    ap.add_argument("--original", default=DEFAULT_ORIGINAL)
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--output", default=DEFAULT_OUTPUT)
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    args = ap.parse_args(argv)

    original_path = Path(args.original)
    print("=" * 72)
    print("PHASE 1A: 应用 RT_STRING 翻译")
    print(f"  原版   : {original_path}")
    print(f"  翻译库 : {args.csv}")
    print(f"  输出   : {args.output}")
    print("-" * 72)

    # ---- 0. 基线校验 ----
    data = original_path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"  输入 SHA256: {sha}")
    if sha != BASELINE_SHA256:
        raise ApplyError("输入文件 SHA256 与固定 baseline 不一致 — 拒绝执行 "
                         "(版本不匹配, 必须重新走 PHASE 0 提取/分析流程)")
    pe = er.PEFile(data)
    blocks = find_string_blocks(pe)
    print(f"  基线校验: 通过 (RT_STRING 块 {len(blocks)} 个)")

    # ---- 1. 翻译库 ----
    entries, skipped = load_translation_csv(Path(args.csv))
    langs = sorted({e["lang"] for e in entries})
    print(f"  有效翻译条目: {len(entries)} 条 (LANGID: {langs}; 跳过非 STRING/非 DONE: {skipped})")

    grouped = {}
    for e in entries:
        grouped.setdefault((e["block_id"], e["lang"]), []).append(e)

    missing_blocks = [k for k in grouped if k not in blocks]
    if missing_blocks:
        raise ApplyError(f"翻译表引用了原版资源树中不存在的 RT_STRING 块: {missing_blocks} "
                         f"(禁止创建不存在的资源)")

    # ---- 2. 逐块重序列化并写回 ----
    patched = bytearray(data)
    modified_keys = []
    original_texts = {}
    for (block_id, lang) in sorted(grouped):
        offset, size = blocks[(block_id, lang)]
        blob = bytes(patched[offset: offset + size])
        strings = er.parse_string_table(blob)
        original_texts[(block_id, lang)] = list(strings)
        target_index = {}
        for e in grouped[(block_id, lang)]:
            idx = e["string_id"] - (block_id - 1) * 16
            if not (0 <= idx < 16):
                raise ApplyError(f"StringID {e['string_id']} 超出块 {block_id} 范围")
            actual = strings[idx]
            if actual != e["original"]:
                raise ApplyError(
                    f"Original 不一致: block={block_id} lang={lang} StringID={e['string_id']} "
                    f"CSV={e['original']!r} 实际={actual!r}")
            problems = check_format_invariants(e["original"], e["chinese"])
            if problems:
                raise ApplyError(f"格式不变量校验失败 StringID={e['string_id']}: {problems}")
            if "&" in e["original"] and "(&" not in e["chinese"]:
                print(f"  ⚠ StringID {e['string_id']}: 原文含助记键 &, 中文未采用 '(&X)' 形式")
            strings[idx] = e["chinese"]
            target_index[idx] = e["string_id"]
        new_blob = er.serialize_string_table(strings)          # 强制 16 条, 否则抛错
        if len(new_blob) > size:
            raise ApplyError(
                f"RESOURCE_TOO_LARGE: block={block_id} lang={lang} "
                f"重序列化 {len(new_blob)} 字节 > 原分配 {size} 字节 — 拒绝生成, 请缩短措辞")
        blob_out = new_blob + b"\x00" * (size - len(new_blob))  # 只在整块末尾补 0
        patched[offset: offset + size] = blob_out
        modified_keys.append((block_id, lang))
        print(f"  写回 block={block_id:<4} lang={lang} @{offset:#x}-{offset + size:#x} "
              f"({size} → {len(new_blob)} 字节, 末尾补零 {size - len(new_blob)}), "
              f"StringID={sorted(target_index.values())}")

    # ---- 3. 语义验证 ----
    print("-" * 72)
    print("语义验证:")
    patched_pe = er.PEFile(bytes(patched))
    blocks2 = find_string_blocks(patched_pe)
    if blocks2 != blocks:
        raise ApplyError("资源树布局发生变化 (块偏移/大小/清单不一致) — FAIL")
    print("  ✓ 资源树布局不变 (块偏移/大小/清单完全一致)")

    for (block_id, lang) in modified_keys:
        offset, size = blocks[(block_id, lang)]
        strings2 = er.parse_string_table(bytes(patched[offset: offset + size]))
        if len(strings2) != 16:
            raise ApplyError(f"block={block_id} lang={lang} 验证时条目数 != 16")
        before = original_texts[(block_id, lang)]
        for i in range(16):
            is_target = any(e["string_id"] - (block_id - 1) * 16 == i
                            for e in grouped[(block_id, lang)])
            if is_target:
                want = next(e["chinese"] for e in grouped[(block_id, lang)]
                            if e["string_id"] - (block_id - 1) * 16 == i)
                if strings2[i] != want:
                    raise ApplyError(f"目标 StringID {block_id * 16 - 16 + i} 未写入中文")
            elif strings2[i] != before[i]:
                raise ApplyError(
                    f"block={block_id} lang={lang} 未列入翻译表的条目 {i} 发生变化")
    print("  ✓ 目标条目 == Chinese; 同块非目标条目与原版完全一致")

    modified_resources = {("RT_STRING", b, l) for b, l in modified_keys}
    for r in er.flatten_resources(pe):
        off, size = r["file_offset"], r["size"]
        if off is None:
            continue
        key = (r["type_name"], r["name"], r["lang"])
        if key in modified_resources:
            continue
        if patched[off: off + size] != data[off: off + size]:
            raise ApplyError(f"非目标资源发生变化: {key} — FAIL")
    print("  ✓ 所有非目标 resource payload 与原版逐字节一致")

    audit = verify.audit_bytes(data, bytes(patched))
    allowed = [{"block_id": b, "lang": l,
                "start": blocks[(b, l)][0],
                "end": blocks[(b, l)][0] + blocks[(b, l)][1]}
               for b, l in modified_keys]
    non_target = 0
    for s, e in audit["ranges"]:
        covered = sum(max(0, min(e, al["end"]) - max(s, al["start"])) for al in allowed)
        non_target += (e - s) - covered
    if non_target:
        raise ApplyError(f"存在允许载荷之外的字节变化: {non_target} 字节 — FAIL")
    print(f"  ✓ changed_byte_count={audit['changed_byte_count']}, "
          f"changed_ranges={len(audit['ranges'])}, 全部 ⊆ 目标块载荷")

    # ---- 4. 产出 ----
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(patched)
    patched_sha = hashlib.sha256(patched).hexdigest()
    manifest = {
        "version": 1,
        "generator": "apply_translation.py (PHASE 1A)",
        "baseline": "docs/BASELINE.md — µVision 5.43.1.0",
        "original_sha256": sha,
        "patched_sha256": patched_sha,
        "targets": [{"resource_type": "RT_STRING", "block_id": b, "lang": l,
                     "string_ids": sorted(e["string_id"] for e in grouped[(b, l)])}
                    for b, l in sorted(modified_keys)],
    }
    Path(args.manifest).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print("-" * 72)
    print(f"已写出: {out_path}")
    print(f"        SHA256 = {patched_sha}")
    print(f"已写出: {args.manifest}")
    print("注意: 未经 GPT 审核与用户确认, 不要运行该测试版, 更不要覆盖正式 UV4.exe。")
    print("=" * 72)
    return verify.EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ApplyError as exc:
        print(f"\nFAIL: {exc}", file=sys.stderr)
        sys.exit(verify.EXIT_FAIL)
