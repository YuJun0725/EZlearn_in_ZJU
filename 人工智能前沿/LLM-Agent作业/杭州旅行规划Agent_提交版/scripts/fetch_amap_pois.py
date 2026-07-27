from __future__ import annotations

import argparse
import csv
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


AMAP_PLACE_TEXT_URL = "https://restapi.amap.com/v5/place/text"
DEFAULT_CONFIG = Path("config/amap_keywords.json")
DEFAULT_RAW_OUTPUT = Path("data/raw/amap_pois.json")
DEFAULT_DRAFT_OUTPUT = Path("data/processed/hangzhou_pois_draft.jsonl")
DEFAULT_REVIEW_OUTPUT = Path("data/review/hangzhou_poi_review.csv")

WEEKDAY_COLUMNS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
REVIEW_COLUMNS = [
    "id",
    "include",
    "name",
    "category",
    "district",
    "address",
    "longitude",
    "latitude",
    *WEEKDAY_COLUMNS,
    "opening_hours_raw",
    "ticket_price_yuan",
    "recommended_duration_min",
    "indoor",
    "requires_reservation",
    "walk_level",
    "tags",
    "official_url",
    "source_note",
    "source_provider",
    "source_id",
    "retrieved_at",
]


class AmapError(RuntimeError):
    pass


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def load_keyword_config(path: Path) -> list[dict[str, Any]]:
    items = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(items, list) or not items:
        raise ValueError(f"Keyword config must be a non-empty JSON list: {path}")

    required = {"keyword", "category", "recommended_duration_min", "indoor"}
    for index, item in enumerate(items, start=1):
        missing = required - set(item)
        if missing:
            raise ValueError(f"Keyword config item {index} misses: {sorted(missing)}")
    return items


def filter_keyword_config(
    configured: list[dict[str, Any]], keyword_override: str | None
) -> list[dict[str, Any]]:
    if not keyword_override:
        return configured

    by_keyword = {str(item["keyword"]): item for item in configured}
    selected: list[dict[str, Any]] = []
    for keyword in (part.strip() for part in keyword_override.split(",")):
        if not keyword:
            continue
        selected.append(
            by_keyword.get(
                keyword,
                {
                    "keyword": keyword,
                    "category": "attraction",
                    "recommended_duration_min": 120,
                    "indoor": None,
                },
            )
        )
    if not selected:
        raise ValueError("--keywords did not contain a usable keyword")
    return selected


def request_json(
    endpoint: str,
    params: dict[str, Any],
    timeout: float,
    max_retries: int,
    ssl_context: ssl.SSLContext,
) -> dict[str, Any]:
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "HangzhouTravelAgentDataset/1.0"},
    )

    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(
                request, timeout=timeout, context=ssl_context
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            raise AmapError(f"Amap HTTP error: status {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, ssl.SSLCertVerificationError):
                raise AmapError(
                    "TLS certificate verification failed. Install certifi or "
                    "pass a valid CA file with --ca-bundle. Do not disable SSL "
                    "verification."
                ) from exc
            if attempt >= max_retries:
                detail = reason or "network request failed"
                raise AmapError(f"Amap network error: {detail}") from exc
            time.sleep(1.0 * (attempt + 1))
    else:
        raise AmapError("Amap request failed without a response")

    if str(payload.get("status")) != "1":
        info = payload.get("info", "unknown API error")
        infocode = payload.get("infocode", "unknown")
        raise AmapError(f"Amap API error {infocode}: {info}")
    return payload


def resolve_ca_bundle(explicit_path: Path | None = None) -> Path | None:
    if explicit_path is not None:
        path = explicit_path.expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"CA bundle does not exist: {path}")
        return path

    candidates: list[Path] = []
    for environment_name in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        value = os.environ.get(environment_name, "").strip()
        if value:
            candidates.append(Path(value).expanduser())

    try:
        import certifi  # type: ignore[import-not-found]

        candidates.append(Path(certifi.where()))
    except ImportError:
        pass

    prefix = Path(sys.prefix)
    candidates.extend(
        [
            prefix / "etc" / "ssl" / "cert.pem",
            prefix / "etc" / "ssl" / "certs" / "ca-bundle.crt",
            prefix.parent / "usr" / "ssl" / "cert.pem",
        ]
    )

    program_files = os.environ.get("ProgramFiles", "").strip()
    if program_files:
        candidates.extend(
            [
                Path(program_files)
                / "Git"
                / "mingw64"
                / "etc"
                / "ssl"
                / "certs"
                / "ca-bundle.crt",
                Path(program_files)
                / "Git"
                / "mingw64"
                / "etc"
                / "ssl"
                / "cert.pem",
            ]
        )

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def create_ssl_context(ca_bundle: Path | None) -> tuple[ssl.SSLContext, Path | None]:
    resolved_bundle = resolve_ca_bundle(ca_bundle)
    if resolved_bundle is not None:
        return ssl.create_default_context(cafile=str(resolved_bundle)), resolved_bundle
    return ssl.create_default_context(), None


def fetch_pois(
    api_key: str,
    city: str,
    region: str,
    keyword_config: list[dict[str, Any]],
    pages: int,
    page_size: int,
    delay: float,
    timeout: float,
    max_retries: int,
    ssl_context: ssl.SSLContext,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for config in keyword_config:
        keyword = str(config["keyword"])
        print(f"Fetching keyword: {keyword}")
        for page_num in range(1, pages + 1):
            payload = request_json(
                AMAP_PLACE_TEXT_URL,
                {
                    "key": api_key,
                    "keywords": keyword,
                    "region": region,
                    "city_limit": "true",
                    "page_size": page_size,
                    "page_num": page_num,
                    "show_fields": "business",
                },
                timeout=timeout,
                max_retries=max_retries,
                ssl_context=ssl_context,
            )
            page_records = payload.get("pois") or []
            if not isinstance(page_records, list):
                raise AmapError("Amap returned an unexpected 'pois' value")

            for rank, poi in enumerate(page_records, start=1):
                if not isinstance(poi, dict):
                    continue
                enriched = dict(poi)
                enriched["_collector"] = {
                    "keyword": keyword,
                    "category": config["category"],
                    "recommended_duration_min": config[
                        "recommended_duration_min"
                    ],
                    "indoor": config["indoor"],
                    "page": page_num,
                    "rank": rank,
                }
                records.append(enriched)

            if len(page_records) < page_size:
                break
            time.sleep(delay)
    return records


def text_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(item) for item in value if item is not None)
    return str(value).strip()


def poi_identity(poi: dict[str, Any]) -> str:
    poi_id = text_value(poi.get("id"))
    if poi_id:
        return f"id:{poi_id}"
    return "fallback:{name}|{location}".format(
        name=text_value(poi.get("name")),
        location=text_value(poi.get("location")),
    )


def deduplicate_pois(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for record in records:
        identity = poi_identity(record)
        collector = record.get("_collector") or {}
        if identity not in merged:
            copy = dict(record)
            copy["_collector"] = dict(collector)
            copy["_collector"]["keywords"] = [collector.get("keyword")]
            merged[identity] = copy
            order.append(identity)
            continue

        keywords = merged[identity]["_collector"].setdefault("keywords", [])
        keyword = collector.get("keyword")
        if keyword and keyword not in keywords:
            keywords.append(keyword)
    return [merged[identity] for identity in order]


def select_balanced_pois(
    records: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        collector = record.get("_collector") or {}
        category = str(collector.get("category") or "attraction")
        buckets.setdefault(category, []).append(record)

    selected: list[dict[str, Any]] = []
    while len(selected) < limit:
        added_in_round = False
        for bucket in buckets.values():
            if bucket:
                selected.append(bucket.pop(0))
                added_in_round = True
                if len(selected) >= limit:
                    break
        if not added_in_round:
            break
    return selected


def parse_location(raw_location: Any) -> tuple[float | None, float | None]:
    location = text_value(raw_location)
    if not location or "," not in location:
        return None, None
    longitude_text, latitude_text = location.split(",", 1)
    try:
        return float(longitude_text), float(latitude_text)
    except ValueError:
        return None, None


def numeric_value(value: Any) -> float | None:
    text = text_value(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def split_tags(*values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        for tag in re.split(r"[;,，、|/]", text_value(value)):
            tag = tag.strip()
            if tag and tag not in result:
                result.append(tag)
    return result


def normalize_poi(poi: dict[str, Any], retrieved_at: str) -> dict[str, Any]:
    collector = poi.get("_collector") or {}
    business = poi.get("business")
    if not isinstance(business, dict):
        business = {}
    longitude, latitude = parse_location(poi.get("location"))
    source_id = text_value(poi.get("id"))
    source_keywords = [
        keyword for keyword in collector.get("keywords", []) if keyword
    ]
    opening_hours_raw = text_value(
        business.get("opentime_week") or business.get("opentime_today")
    )

    return {
        "id": f"amap_{source_id}" if source_id else poi_identity(poi),
        "name": text_value(poi.get("name")),
        "category": collector.get("category", "attraction"),
        "amap_type": text_value(poi.get("type")),
        "amap_typecode": text_value(poi.get("typecode")),
        "province": text_value(poi.get("pname")),
        "city": text_value(poi.get("cityname")),
        "district": text_value(poi.get("adname")),
        "address": text_value(poi.get("address")),
        "longitude": longitude,
        "latitude": latitude,
        "opening_hours": None,
        "opening_hours_raw": opening_hours_raw,
        "ticket_price_yuan": None,
        "recommended_duration_min": collector.get("recommended_duration_min"),
        "indoor": collector.get("indoor"),
        "requires_reservation": None,
        "walk_level": None,
        "tags": split_tags(*source_keywords, business.get("tag")),
        "official_url": None,
        "source_note": "",
        "amap_rating": numeric_value(business.get("rating")),
        "amap_business_cost_yuan": numeric_value(business.get("cost")),
        "planning_ready": False,
        "source": {
            "provider": "amap",
            "poi_id": source_id,
            "keywords": source_keywords,
            "retrieved_at": retrieved_at,
        },
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def review_row(record: dict[str, Any]) -> dict[str, Any]:
    source = record["source"]
    row: dict[str, Any] = {
        "id": record["id"],
        "include": "true",
        "name": record["name"],
        "category": record["category"],
        "district": record["district"],
        "address": record["address"],
        "longitude": record["longitude"],
        "latitude": record["latitude"],
        "opening_hours_raw": record["opening_hours_raw"],
        "ticket_price_yuan": "",
        "recommended_duration_min": record["recommended_duration_min"],
        "indoor": (
            ""
            if record["indoor"] is None
            else str(record["indoor"]).lower()
        ),
        "requires_reservation": "",
        "walk_level": "",
        "tags": "|".join(record["tags"]),
        "official_url": "",
        "source_note": "",
        "source_provider": source["provider"],
        "source_id": source["poi_id"],
        "retrieved_at": source["retrieved_at"],
    }
    for weekday in WEEKDAY_COLUMNS:
        row[weekday] = ""
    return row


def write_review_csv(
    path: Path,
    records: list[dict[str, Any]],
    overwrite: bool,
) -> bool:
    if path.exists() and not overwrite:
        print(f"Review CSV already exists; keeping manual edits: {path}")
        print("Use --overwrite-review only when you intentionally want to replace it.")
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(review_row(record) for record in records)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and normalize Hangzhou POIs from Amap Web Service API."
    )
    parser.add_argument("--city", default="杭州市")
    parser.add_argument(
        "--region",
        default="330100",
        help="Amap adcode or region name. Default: Hangzhou adcode 330100.",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--keywords",
        help="Comma-separated keyword override, for example: 博物馆,美术馆",
    )
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--page-size", type=int, default=25)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument(
        "--ca-bundle",
        type=Path,
        help="Optional PEM CA bundle used for HTTPS certificate verification.",
    )
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_OUTPUT)
    parser.add_argument("--draft-output", type=Path, default=DEFAULT_DRAFT_OUTPUT)
    parser.add_argument("--review-output", type=Path, default=DEFAULT_REVIEW_OUTPUT)
    parser.add_argument("--overwrite-review", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.pages < 1 or args.page_size < 1 or args.limit < 1:
        print("pages, page-size and limit must all be positive", file=sys.stderr)
        return 2

    load_dotenv(args.env_file)
    api_key = os.environ.get("AMAP_API_KEY", "").strip()
    if not api_key or api_key == "replace_with_your_web_service_key":
        print(
            "AMAP_API_KEY is missing. Copy .env.example to .env and fill in the key.",
            file=sys.stderr,
        )
        return 2

    try:
        ssl_context, ca_bundle = create_ssl_context(args.ca_bundle)
        if ca_bundle is not None:
            print(f"Using CA bundle: {ca_bundle}")
        keyword_config = filter_keyword_config(
            load_keyword_config(args.config), args.keywords
        )
        fetched = fetch_pois(
            api_key=api_key,
            city=args.city,
            region=args.region,
            keyword_config=keyword_config,
            pages=args.pages,
            page_size=args.page_size,
            delay=args.delay,
            timeout=args.timeout,
            max_retries=args.max_retries,
            ssl_context=ssl_context,
        )
    except (AmapError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Collection failed: {exc}", file=sys.stderr)
        return 1

    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    deduplicated = deduplicate_pois(fetched)
    selected = select_balanced_pois(deduplicated, args.limit)
    normalized = [normalize_poi(poi, retrieved_at) for poi in selected]

    write_json(
        args.raw_output,
        {
            "metadata": {
                "provider": "amap",
                "api": "place/text-v5",
                "city": args.city,
                "region": args.region,
                "retrieved_at": retrieved_at,
                "keywords": [item["keyword"] for item in keyword_config],
                "fetched_count": len(fetched),
                "unique_count": len(deduplicated),
                "selected_count": len(selected),
                "api_key_stored": False,
            },
            "pois": selected,
        },
    )
    write_jsonl(args.draft_output, normalized)
    review_written = write_review_csv(
        args.review_output, normalized, args.overwrite_review
    )

    print(f"Fetched records: {len(fetched)}")
    print(f"Unique records written: {len(normalized)}")
    print(f"Raw snapshot: {args.raw_output}")
    print(f"Normalized draft: {args.draft_output}")
    if review_written:
        print(f"Manual review CSV: {args.review_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
