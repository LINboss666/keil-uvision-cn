#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
text_validators.py — 菜单/字符串翻译的机械校验器（PHASE 1B1）

提供四类校验, 供 apply_translation.py 在写入前逐条执行:
    1. printf 格式占位符: 按 flags/width/precision/length/conversion 完整解析,
       Original 与 Chinese 的 token 序列必须逐个一致 (支持 %s %d %i %u %x %X %p
       %ld %lu %lld %llu %zu %.*s %02X %08X %% 以及 width/precision/length modifier)。
    2. "\\t" 快捷键段: 每个 \\t 之后的文本必须与 Original 完全一致
       (例如 '\\tCtrl+O' 不得变成 '\\tCtrl+P', 即使 \\t 数量相同)。
    3. 助记键 '&': 识别 '&X' 与 '&&'(字面 &); 禁止悬空 '&' (串尾孤立 &);
       中文助记键数量必须与原文一致; 字母可以改变但必须记录 (Notes 非空)。
    4. 同级助记键冲突: 对菜单同一弹出层内的兄弟项收集助记键字母,
       禁止引入原文中不存在的新冲突。
"""

from __future__ import annotations

import re

# 完整 printf 规格符: % [+flags][width][.precision][length]conversion, 以及 %%
FORMAT_TOKEN_RE = re.compile(
    r"%(?:%"
    r"|[-+ #0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:hh|h|ll|l|L|q|j|z|t|I64|I32|I)?"
    r"[diouxXeEfFgGaAcspn])"
)


def format_tokens(text: str):
    """按出现顺序提取 printf 格式 token (%% 也算一个 token)。"""
    return FORMAT_TOKEN_RE.findall(text)


def check_format_tokens(original: str, chinese: str):
    """token 序列必须完全一致 (顺序敏感, printf 位置语义)。返回问题列表。"""
    problems = []
    to, tc = format_tokens(original), format_tokens(chinese)
    if to != tc:
        problems.append(f"printf 格式 token 不一致: 原文{to} vs 中文{tc}")
    return problems


def check_shortcut_segments(original: str, chinese: str):
    """每个 \\t 之后的快捷键文本必须与 Original 完全一致。返回问题列表。"""
    problems = []
    so, sc = original.split("\t"), chinese.split("\t")
    if len(so) != len(sc):
        problems.append(f"\\t 数量不一致: 原文 {len(so) - 1} vs 中文 {len(sc) - 1}")
    else:
        for i, (a, b) in enumerate(zip(so[1:], sc[1:]), start=1):
            if a != b:
                problems.append(f"\\t 后第 {i} 段快捷键文本被改变: {a!r} → {b!r}")
    return problems


def extract_mnemonics(text: str):
    """提取助记键字母序列; '&&' 计为字面 &; 串尾孤立 '&' 记为 None (悬空)。"""
    out = []
    i = 0
    while i < len(text):
        if text[i] == "&":
            if i + 1 < len(text) and text[i + 1] == "&":
                i += 2                      # && = 字符 & 本身
                continue
            if i + 1 >= len(text):
                out.append(None)            # 悬空 &
                break
            out.append(text[i + 1])
            i += 2
            continue
        i += 1
    return out


def check_mnemonics(original: str, chinese: str, notes: str = ""):
    """逐条校验助记键。返回问题列表。

    规则:
        * 中文不得出现悬空 '&';
        * 助记键数量必须与原文一致 (可保留 '&X' 或改为 '中文(&X)' 形式);
        * 助记键字母改变时, Notes 必须非空 (留下记录)。
    """
    problems = []
    mo, mc = extract_mnemonics(original), extract_mnemonics(chinese)
    if None in mc:
        problems.append("中文含悬空 '&' (串尾孤立 &)")
    if len([m for m in mo if m is not None]) != len([m for m in mc if m is not None]):
        problems.append(f"助记键数量不一致: 原文 {mo} vs 中文 {mc}")
    lo = [m for m in mo if m is not None]
    lc = [m for m in mc if m is not None]
    if lo and lc and [c.upper() for c in lo] != [c.upper() for c in lc] and not notes.strip():
        problems.append(f"助记键字母改变 ({'&' + '/&'.join(lo)} → {'&' + '/&'.join(lc)}) 但 Notes 未记录")
    return problems


def sibling_mnemonic_conflicts(texts):
    """一组兄弟菜单项的助记键字母 → 出现次数 ≥2 的字母集合。"""
    from collections import Counter
    letters = []
    for t in texts:
        letters += [m.upper() for m in extract_mnemonics(t or "") if m is not None]
    return {l for l, n in Counter(letters).items() if n > 1}


def check_entry(original: str, chinese: str, notes: str = ""):
    """单条翻译的全部机械校验。返回问题列表 (空 = 通过)。"""
    problems = []
    problems += check_format_tokens(original, chinese)
    problems += check_shortcut_segments(original, chinese)
    problems += check_mnemonics(original, chinese, notes)
    return problems
