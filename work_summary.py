"""Work summary tracker.

Provides CLI to record daily work entries and generate period summaries
(daily, weekly, monthly, academic-year). Suggestions are derived from
logged challenges to highlight improvement areas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


@dataclass
class WorkEntry:
    """A single day's work log."""

    date: date
    accomplishments: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "date": self.date.isoformat(),
            "accomplishments": self.accomplishments,
            "challenges": self.challenges,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, object]) -> "WorkEntry":
        return cls(
            date=datetime.strptime(str(raw["date"]), "%Y-%m-%d").date(),
            accomplishments=list(raw.get("accomplishments", [])),
            challenges=list(raw.get("challenges", [])),
            notes=list(raw.get("notes", [])),
        )


class WorkLog:
    """Collection of entries persisted to JSON."""

    def __init__(self, storage_path: Path | str = "work_log.json") -> None:
        self.storage_path = Path(storage_path)
        self.entries: List[WorkEntry] = []
        if self.storage_path.exists():
            with self.storage_path.open("r", encoding="utf-8") as handle:
                raw_entries = json.load(handle)
            self.entries = [WorkEntry.from_dict(item) for item in raw_entries]

    def add_entry(
        self,
        entry_date: date,
        accomplishments: Sequence[str],
        challenges: Sequence[str],
        notes: Sequence[str],
    ) -> WorkEntry:
        entry = WorkEntry(
            date=entry_date,
            accomplishments=list(accomplishments),
            challenges=list(challenges),
            notes=list(notes),
        )
        self.entries.append(entry)
        self.save()
        return entry

    def save(self) -> None:
        payload = [entry.to_dict() for entry in self.entries]
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def entries_between(self, start: date, end: date) -> List[WorkEntry]:
        return [entry for entry in self.entries if start <= entry.date <= end]


def _monday_of_week(any_date: date) -> date:
    return any_date - timedelta(days=any_date.weekday())


def _month_bounds(any_date: date) -> tuple[date, date]:
    first = any_date.replace(day=1)
    if any_date.month == 12:
        next_month = any_date.replace(year=any_date.year + 1, month=1, day=1)
    else:
        next_month = any_date.replace(month=any_date.month + 1, day=1)
    last = next_month - timedelta(days=1)
    return first, last


def _academic_year_bounds(any_date: date, start_month: int = 9) -> tuple[date, date]:
    if any_date.month >= start_month:
        start = any_date.replace(month=start_month, day=1)
        end = start.replace(year=start.year + 1) - timedelta(days=1)
    else:
        start = any_date.replace(year=any_date.year - 1, month=start_month, day=1)
        end = start.replace(year=start.year + 1) - timedelta(days=1)
    return start, end


def _aggregate_lines(entries: Iterable[WorkEntry], attribute: str) -> List[str]:
    items: List[str] = []
    for entry in entries:
        items.extend(getattr(entry, attribute))
    return items


def _suggestions_from_challenges(challenges: Iterable[str]) -> List[str]:
    suggestions: List[str] = []
    rules = [
        ("沟通", "与利益相关者建立每日同步，提前澄清需求并共享风险。"),
        ("时间", "将任务拆分为半天的子目标，使用番茄钟跟踪进度。"),
        ("延误", "每天下班前更新进度板，标记阻塞项并主动寻求帮助。"),
        ("文档", "为复杂流程补充简短操作手册，复盘后沉淀成知识库。"),
        ("质量", "为高风险改动补充单元测试和检查清单，发布前进行自测。"),
        ("效率", "批量处理重复性工作，能脚本化的任务优先自动化。"),
    ]
    normalized = " ".join(challenges)
    for keyword, tip in rules:
        if keyword in normalized:
            suggestions.append(tip)
    if not suggestions:
        suggestions.append("保持每日记录，并在周五回顾一周的亮点与改进点。")
    return suggestions


def generate_summary(entries: Iterable[WorkEntry], label: str) -> Dict[str, object]:
    accomplishments = _aggregate_lines(entries, "accomplishments")
    challenges = _aggregate_lines(entries, "challenges")
    notes = _aggregate_lines(entries, "notes")
    return {
        "period": label,
        "accomplishments": accomplishments,
        "challenges": challenges,
        "notes": notes,
        "suggestions": _suggestions_from_challenges(challenges),
    }


def summarize_period(work_log: WorkLog, period: str, anchor: date | None = None) -> Dict[str, object]:
    anchor = anchor or date.today()
    if period == "daily":
        start = end = anchor
        label = anchor.isoformat()
    elif period == "weekly":
        start = _monday_of_week(anchor)
        end = start + timedelta(days=6)
        label = f"{start.isoformat()} 至 {end.isoformat()}"
    elif period == "monthly":
        start, end = _month_bounds(anchor)
        label = f"{start.strftime('%Y-%m')}"
    elif period == "academic":
        start, end = _academic_year_bounds(anchor)
        label = f"学年 {start.year}-{end.year}"
    else:
        raise ValueError("period must be one of: daily, weekly, monthly, academic")

    entries = work_log.entries_between(start, end)
    return generate_summary(entries, label)


def _print_summary(summary: Dict[str, object]) -> None:
    print(f"总结周期：{summary['period']}")
    for section in ("accomplishments", "challenges", "notes", "suggestions"):
        title = {
            "accomplishments": "完成与亮点",
            "challenges": "问题与阻塞",
            "notes": "知识沉淀",
            "suggestions": "改进建议",
        }[section]
        print(f"\n{title}:")
        values = summary.get(section) or []
        if not values:
            print("- 暂无记录")
            continue
        for item in values:
            print(f"- {item}")


def _parse_args() -> Dict[str, object]:
    import argparse

    parser = argparse.ArgumentParser(description="记录工作并生成自动总结")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="记录一天的工作")
    add_parser.add_argument("--date", dest="date", default=date.today().isoformat())
    add_parser.add_argument("--accomplishment", action="append", default=[])
    add_parser.add_argument("--challenge", action="append", default=[])
    add_parser.add_argument("--note", action="append", default=[])
    add_parser.add_argument("--storage", default="work_log.json")

    summary_parser = subparsers.add_parser("summary", help="生成总结")
    summary_parser.add_argument("--period", choices=["daily", "weekly", "monthly", "academic"], required=True)
    summary_parser.add_argument("--date", dest="date", default=date.today().isoformat())
    summary_parser.add_argument("--storage", default="work_log.json")

    args = parser.parse_args()
    return vars(args)


def _main() -> None:
    args = _parse_args()
    command = args["command"]
    anchor = datetime.strptime(args["date"], "%Y-%m-%d").date()
    work_log = WorkLog(args["storage"])

    if command == "add":
        entry = work_log.add_entry(
            entry_date=anchor,
            accomplishments=args["accomplishment"],
            challenges=args["challenge"],
            notes=args["note"],
        )
        print(f"已记录 {entry.date.isoformat()} 的工作。")
    else:
        summary = summarize_period(work_log, args["period"], anchor=anchor)
        _print_summary(summary)


if __name__ == "__main__":
    _main()
