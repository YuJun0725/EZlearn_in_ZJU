from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
TIME_WINDOW_PATTERN = re.compile(
    r"^(?P<start_hour>\d{1,2}):(?P<start_minute>\d{2})-"
    r"(?P<end_hour>\d{1,2}):(?P<end_minute>\d{2})$"
)


def parse_bool(value: str, field_name: str) -> bool | None:
    normalized = value.strip().lower()
    if not normalized:
        return None
    if normalized in {"true", "1", "yes", "y", "是"}:
        return True
    if normalized in {"false", "0", "no", "n", "否"}:
        return False
    raise ValueError(f"{field_name} must be true/false")


def parse_float(value: str, field_name: str) -> float | None:
    normalized = value.strip()
    if not normalized:
        return None
    try:
        return float(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be numeric") from exc


def parse_positive_int(value: str, field_name: str) -> int | None:
    number = parse_float(value, field_name)
    if number is None:
        return None
    if not number.is_integer() or number <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return int(number)


def time_to_minutes(hour_text: str, minute_text: str) -> int:
    hour = int(hour_text)
    minute = int(minute_text)
    if hour == 24 and minute == 0:
        return 24 * 60
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("time must be between 00:00 and 24:00")
    return hour * 60 + minute


def parse_day_windows(value: str, field_name: str) -> list[dict[str, str]] | None:
    normalized = value.strip().lower()
    if not normalized:
        return None
    if normalized in {"closed", "close", "闭馆", "休息"}:
        return []

    windows: list[dict[str, str]] = []
    for raw_window in normalized.split("|"):
        raw_window = raw_window.strip()
        match = TIME_WINDOW_PATTERN.fullmatch(raw_window)
        if not match:
            raise ValueError(
                f"{field_name} must look like 09:00-17:00 or closed"
            )
        start_minutes = time_to_minutes(
            match.group("start_hour"), match.group("start_minute")
        )
        end_minutes = time_to_minutes(
            match.group("end_hour"), match.group("end_minute")
        )
        if start_minutes >= end_minutes:
            raise ValueError(f"{field_name} start time must be before end time")
        windows.append(
            {
                "open": f"{start_minutes // 60:02d}:{start_minutes % 60:02d}",
                "close": f"{end_minutes // 60:02d}:{end_minutes % 60:02d}",
            }
        )
    return windows


def split_tags(value: str) -> list[str]:
    tags: list[str] = []
    for tag in re.split(r"[|;,，、/]", value):
        tag = tag.strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def build_record(row: dict[str, str], line_number: int) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []

    def capture(function: Any, value: str, field_name: str) -> Any:
        try:
            return function(value, field_name)
        except ValueError as exc:
            issues.append(str(exc))
            return None

    longitude = capture(parse_float, row.get("longitude", ""), "longitude")
    latitude = capture(parse_float, row.get("latitude", ""), "latitude")
    ticket_price = capture(
        parse_float, row.get("ticket_price_yuan", ""), "ticket_price_yuan"
    )
    duration = capture(
        parse_positive_int,
        row.get("recommended_duration_min", ""),
        "recommended_duration_min",
    )
    indoor = capture(parse_bool, row.get("indoor", ""), "indoor")
    reservation = capture(
        parse_bool,
        row.get("requires_reservation", ""),
        "requires_reservation",
    )

    opening_hours: dict[str, list[dict[str, str]] | None] = {}
    for weekday in WEEKDAYS:
        opening_hours[weekday] = capture(
            parse_day_windows, row.get(weekday, ""), weekday
        )

    required_text_fields = ["id", "name", "category", "district", "address"]
    for field_name in required_text_fields:
        if not row.get(field_name, "").strip():
            issues.append(f"{field_name} is required")
    if longitude is None or latitude is None:
        issues.append("valid longitude and latitude are required")
    elif not (118.0 <= longitude <= 122.0 and 28.0 <= latitude <= 32.0):
        issues.append("coordinates are outside the expected Hangzhou area")
    if any(value is None for value in opening_hours.values()):
        issues.append("all seven weekday opening-hour fields are required")
    if ticket_price is None or ticket_price < 0:
        issues.append("ticket_price_yuan must be zero or a positive number")
    if duration is None:
        issues.append("recommended_duration_min is required")
    if indoor is None:
        issues.append("indoor is required")
    if reservation is None:
        issues.append("requires_reservation is required")

    walk_level_raw = row.get("walk_level", "").strip().lower()
    if walk_level_raw not in {"low", "medium", "high"}:
        issues.append("walk_level must be low, medium or high")
        walk_level = None
    else:
        walk_level = walk_level_raw

    official_url = row.get("official_url", "").strip()
    if official_url and not official_url.startswith(("http://", "https://")):
        issues.append("official_url must start with http:// or https://")

    record = {
        "id": row.get("id", "").strip(),
        "name": row.get("name", "").strip(),
        "category": row.get("category", "").strip(),
        "district": row.get("district", "").strip(),
        "address": row.get("address", "").strip(),
        "longitude": longitude,
        "latitude": latitude,
        "opening_hours": opening_hours,
        "opening_hours_raw": row.get("opening_hours_raw", "").strip(),
        "ticket_price_yuan": ticket_price,
        "recommended_duration_min": duration,
        "indoor": indoor,
        "requires_reservation": reservation,
        "walk_level": walk_level,
        "tags": split_tags(row.get("tags", "")),
        "official_url": official_url or None,
        "source_note": row.get("source_note", "").strip(),
        "planning_ready": not issues,
        "quality": {
            "status": "ready" if not issues else "incomplete",
            "issues": issues,
            "review_csv_line": line_number,
        },
        "source": {
            "provider": row.get("source_provider", "").strip(),
            "poi_id": row.get("source_id", "").strip(),
            "retrieved_at": row.get("retrieved_at", "").strip(),
        },
    }
    return record, issues


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the reviewed POI CSV and build the final JSONL dataset."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/review/hangzhou_poi_review.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/hangzhou_pois.jsonl"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/processed/validation_report.json"),
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Write incomplete records as planning_ready=false instead of failing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        print(f"Review CSV does not exist: {args.input}", file=sys.stderr)
        return 2

    records: list[dict[str, Any]] = []
    validation_errors: list[dict[str, Any]] = []
    with args.input.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            print("Review CSV has no header", file=sys.stderr)
            return 2
        missing_columns = set(["id", "include", "name", *WEEKDAYS]) - set(
            reader.fieldnames
        )
        if missing_columns:
            print(
                f"Review CSV misses columns: {sorted(missing_columns)}",
                file=sys.stderr,
            )
            return 2

        for line_number, row in enumerate(reader, start=2):
            include = row.get("include", "true").strip().lower()
            if include in {"false", "0", "no", "n", "否"}:
                continue
            record, issues = build_record(row, line_number)
            records.append(record)
            if issues:
                validation_errors.append(
                    {
                        "line": line_number,
                        "id": record["id"],
                        "name": record["name"],
                        "issues": issues,
                    }
                )

    report = {
        "input": str(args.input),
        "included_count": len(records),
        "ready_count": sum(record["planning_ready"] for record in records),
        "incomplete_count": len(validation_errors),
        "errors": validation_errors,
    }
    write_report(args.report, report)

    if validation_errors and not args.allow_incomplete:
        print(
            f"Validation failed for {len(validation_errors)} POIs. "
            f"See {args.report}. Use --allow-incomplete for a draft build.",
            file=sys.stderr,
        )
        return 1

    write_jsonl(args.output, records)
    print(f"Included POIs: {len(records)}")
    print(f"Planning-ready POIs: {report['ready_count']}")
    print(f"Incomplete POIs: {report['incomplete_count']}")
    print(f"Dataset: {args.output}")
    print(f"Validation report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
