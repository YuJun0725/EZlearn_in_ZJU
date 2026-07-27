from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "review" / "hangzhou_poi_review.csv"
DEFAULT_REPORT = (
    PROJECT_ROOT / "data" / "processed" / "opening_hours_prefill_report.json"
)
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DAY_NAMES = ("一", "二", "三", "四", "五", "六", "日")
DAY_TO_INDEX = {name: index for index, name in enumerate(DAY_NAMES)}
TIME_WINDOW = r"\d{1,2}:\d{2}\s*[-－—–]\s*\d{1,2}:\d{2}"
DAY_PART = r"周?[一二三四五六日天](?:\s*(?:至|[-－—–])\s*周?[一二三四五六日天])?"
DAY_EXPRESSION = rf"周[一二三四五六日天](?:\s*(?:至|[-－—–])\s*周?[一二三四五六日天])?(?:\s*[,，、]\s*{DAY_PART})*"
SCHEDULE_PATTERN = re.compile(
    rf"(?P<days>{DAY_EXPRESSION})\s*[:：]?\s*(?P<window>{TIME_WINDOW})"
)
CLOSED_PATTERN = re.compile(
    rf"(?P<days>{DAY_EXPRESSION})\s*(?:全天)?\s*(?:关闭|不开放|闭馆|休息)"
)
MULTI_VENUE_PATTERN = re.compile(r"(?:杭州馆|安吉馆|[\u4e00-\u9fff]{1,8}馆区)\s*[:：]")
SEASON_PATTERN = re.compile(r"夏令时|冬令时")


@dataclass(frozen=True, slots=True)
class ParseResult:
    weekly: dict[str, str] | None
    reason: str
    inferred_closed: tuple[str, ...] = ()


def _parse_days(expression: str) -> tuple[int, ...]:
    normalized = expression.replace("天", "日").replace("周", "")
    parts = re.split(r"[,，、]", normalized)
    indexes: list[int] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        range_parts = re.split(r"至|[-－—–]", part)
        if len(range_parts) == 1:
            indexes.append(DAY_TO_INDEX[range_parts[0]])
            continue
        if len(range_parts) != 2:
            raise ValueError(f"unsupported weekday expression: {expression}")
        start, end = DAY_TO_INDEX[range_parts[0]], DAY_TO_INDEX[range_parts[1]]
        if start > end:
            raise ValueError(f"reversed weekday range: {expression}")
        indexes.extend(range(start, end + 1))
    return tuple(dict.fromkeys(indexes))


def _normalize_window(raw: str) -> str:
    normalized = re.sub(r"\s+", "", raw)
    normalized = re.sub(r"[-－—–]", "-", normalized)
    start, end = normalized.split("-", 1)

    def normalize_clock(value: str, *, allow_24: bool) -> tuple[str, int]:
        hour_text, minute_text = value.split(":", 1)
        hour, minute = int(hour_text), int(minute_text)
        if hour == 24 and minute == 0 and allow_24:
            return "24:00", 24 * 60
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"invalid clock time: {value}")
        return f"{hour:02d}:{minute:02d}", hour * 60 + minute

    start_text, start_minutes = normalize_clock(start, allow_24=False)
    end_text, end_minutes = normalize_clock(end, allow_24=True)
    if start_minutes >= end_minutes:
        raise ValueError(f"opening time must be before closing time: {raw}")
    return f"{start_text}-{end_text}"


def parse_opening_hours_raw(raw: str) -> ParseResult:
    text = raw.strip()
    if not text:
        return ParseResult(None, "opening_hours_raw is empty")
    if MULTI_VENUE_PATTERN.search(text):
        return ParseResult(None, "multiple venues or venue areas share one raw value")
    if SEASON_PATTERN.search(text):
        return ParseResult(None, "summer and winter schedules differ")

    assignments: dict[int, str] = {}
    try:
        schedules = list(SCHEDULE_PATTERN.finditer(text))
        closures = list(CLOSED_PATTERN.finditer(text))
        if not schedules:
            return ParseResult(None, "no explicit weekday schedule found")

        for match in schedules:
            window = _normalize_window(match.group("window"))
            for day_index in _parse_days(match.group("days")):
                existing = assignments.get(day_index)
                if existing is not None and existing != window:
                    return ParseResult(
                        None,
                        "the same weekday has multiple seasonal or conflicting schedules",
                    )
                assignments[day_index] = window

        for match in closures:
            for day_index in _parse_days(match.group("days")):
                existing = assignments.get(day_index)
                if existing is not None and existing != "closed":
                    return ParseResult(
                        None,
                        "the same weekday is both open and closed in the raw value",
                    )
                assignments[day_index] = "closed"
    except (KeyError, ValueError) as exc:
        return ParseResult(None, str(exc))

    inferred_closed_indexes = tuple(
        index for index in range(7) if index not in assignments
    )
    for index in inferred_closed_indexes:
        assignments[index] = "closed"
    weekly = {WEEKDAYS[index]: assignments[index] for index in range(7)}
    inferred_closed = tuple(WEEKDAYS[index] for index in inferred_closed_indexes)
    reason = "parsed weekly schedule"
    if inferred_closed:
        reason += "; omitted weekdays inferred as closed"
    return ParseResult(weekly, reason, inferred_closed)


def prefill_rows(
    rows: list[dict[str, str]],
    *,
    overwrite_existing: bool = False,
) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    report: list[dict[str, object]] = []
    for line_number, row in enumerate(rows, start=2):
        existing = [row.get(day, "").strip() for day in WEEKDAYS]
        if any(existing) and not overwrite_existing:
            report.append(
                {
                    "line": line_number,
                    "id": row.get("id", ""),
                    "name": row.get("name", ""),
                    "status": "preserved",
                    "reason": "at least one weekday was already filled",
                }
            )
            continue
        parsed = parse_opening_hours_raw(row.get("opening_hours_raw", ""))
        if parsed.weekly is None:
            report.append(
                {
                    "line": line_number,
                    "id": row.get("id", ""),
                    "name": row.get("name", ""),
                    "status": "skipped",
                    "reason": parsed.reason,
                }
            )
            continue
        for weekday, value in parsed.weekly.items():
            row[weekday] = value
        report.append(
            {
                "line": line_number,
                "id": row.get("id", ""),
                "name": row.get("name", ""),
                "status": "filled",
                "reason": parsed.reason,
                "inferred_closed": list(parsed.inferred_closed),
                "weekly": parsed.weekly,
            }
        )
    return rows, report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Conservatively prefill weekday columns from opening_hours_raw."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--apply", action="store_true", help="Write changes to the CSV")
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Replace rows that already contain weekday values",
    )
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("review CSV has no header")
        fieldnames = list(reader.fieldnames)
        missing = set(WEEKDAYS).difference(fieldnames)
        if missing:
            raise ValueError("review CSV is missing weekday columns: " + ", ".join(missing))
        rows = list(reader)

    rows, entries = prefill_rows(
        rows, overwrite_existing=args.overwrite_existing
    )
    counts = {
        status: sum(entry["status"] == status for entry in entries)
        for status in ("filled", "preserved", "skipped")
    }
    report_payload = {
        "input": str(args.input),
        "applied": args.apply,
        "overwrite_existing": args.overwrite_existing,
        "counts": counts,
        "entries": entries,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.apply:
        archive_directory = PROJECT_ROOT / "data" / "archive"
        archive_directory.mkdir(parents=True, exist_ok=True)
        backup = archive_directory / (
            args.input.stem + ".before_opening_prefill.csv"
        )
        if not backup.exists():
            shutil.copy2(args.input, backup)
        temporary = args.input.with_suffix(args.input.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        temporary.replace(args.input)

    mode = "Applied" if args.apply else "Dry run"
    print(f"{mode}: filled={counts['filled']}, preserved={counts['preserved']}, skipped={counts['skipped']}")
    print(f"Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
