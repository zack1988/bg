# 工作总结生成器

一个简单的命令行脚本，用于记录每日工作并自动生成日报、周报、月报，以及学年总结，同时根据问题给出改进建议。

## 快速开始

1. 记录今日工作：

```bash
python work_summary.py add \
  --accomplishment "完成用户权限接口" \
  --challenge "时间紧张导致联调延误" \
  --note "梳理了接口调用链"
```

2. 生成总结：

- 日报（默认今天）：

```bash
python work_summary.py summary --period daily
```

- 周报（以周一为起点）：

```bash
python work_summary.py summary --period weekly --date 2024-11-18
```

- 月报：

```bash
python work_summary.py summary --period monthly --date 2024-11-01
```

- 学年总结（默认每年 9 月 1 日开始）：

```bash
python work_summary.py summary --period academic --date 2024-11-01
```

## 生成逻辑

- 数据默认存储在 `work_log.json`，可用 `--storage` 切换文件。
- 周报以周一至周日为一个周期；月报以当月 1 日至最后一天；学年周期默认 9 月 1 日开始，可在代码中调整。
- 改进建议根据记录的“问题与阻塞”关键词生成，若无匹配则提供通用回顾建议。
