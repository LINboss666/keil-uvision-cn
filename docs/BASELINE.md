# 基线 — Keil µVision UV4.exe (PHASE 0 固化)

> 本文件只记录**元数据与哈希**，用于验证"用户当前 UV4.exe 是否为
> 本项目开发时对应的那个版本"。绝不存储任何 Keil 二进制。

## 原版信息

| 项目 | 值 |
|---|---|
| Product | µVision IDE（Keil MDK，ARM Limited） |
| FileVersion | 5.43.1.0 |
| ProductVersion | 5.43.1.0 |
| 原始路径 | `C:\Keil_v5\UV4\UV4.exe` |
| File Size | 12,765,464 bytes |
| SHA256 | `428baf13d15e6760af1618def9c9815c97f0321cc5e459ec7adc4dde41c42f89` |
| PE 架构 | PE32（32 位 x86），GUI 子系统，ImageBase 0x400000 |
| 数字签名 | Valid — CN=Arm Limited（GlobalSign GCC R45 EV CodeSigning CA 2020 签发，2025-01-05 ~ 2027-02-05） |
| 链接时间 | 2025-08-19 19:15:41 UTC |
| 同机工具链 | MDK-ARM Plus 5.43.0.0，ArmClang/Armasm/ArmLink/ArmAr/FromElf 6.24 |

## 备份位置（均在本机，不上传）

| 位置 | 文件 |
|---|---|
| `C:\Keil_v5\UV4\Backup_Original\` | `UV4_5.43.1.0_ORIGINAL.exe` + `UV4_5.43.1.0_ORIGINAL.sha256.txt` |
| 本项目 `backup/`（gitignored） | `UV4_5.43.1.0_ORIGINAL.exe` |

## 校验方法

```bash
certutil -hashfile "C:\Keil_v5\UV4\UV4.exe" SHA256
# 或
python scripts/verify.py backup/UV4_5.43.1.0_ORIGINAL.exe
```

SHA256 与上表一致 ⇒ 用户当前程序与本项目分析基线相同，可应用翻译数据。
不一致 ⇒ 版本已更新，必须重新走 PHASE 0 提取/diff 流程，不得直接套用。
