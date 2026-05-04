import argparse
import re
import shutil
import subprocess
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from bug_tracker import config
from launchpadlib.launchpad import Launchpad


ROW_RE = re.compile(
    r"(<!-- .* / (?P<ts>\d+) -->\s*<row><v>)(?P<value>[^<]+)(</v></row>)"
)
HEARTBEAT_RE = re.compile(
    r"(<minimal_heartbeat>)(\d+)(</minimal_heartbeat>)"
)


@dataclass(frozen=True)
class Event:
    ts: int
    delta: int


def parse_lp_datetime(value) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return int(value.timestamp())

    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    return int(datetime.fromisoformat(text).timestamp())


def ceil_step(ts: int, step: int) -> int:
    return ((ts + step - 1) // step) * step


def task_to_events(task, start_ts: int, end_ts: int) -> list[Event]:
    created = parse_lp_datetime(getattr(task, "date_created", None))
    left_new = parse_lp_datetime(getattr(task, "date_left_new", None))
    left_closed = parse_lp_datetime(getattr(task, "date_left_closed", None))
    status = getattr(task, "status", None)

    events = []
    if created is not None and start_ts < created <= end_ts:
        events.append(Event(created, 1))
    if left_new is not None and start_ts < left_new <= end_ts:
        events.append(Event(left_new, -1))
    if (
        status == "New"
        and left_closed is not None
        and start_ts < left_closed <= end_ts
        and (left_new is None or left_closed > left_new)
    ):
        events.append(Event(left_closed, 1))
    return events


def reverse_adjustments(events: list[Event], step: int) -> dict[int, int]:
    adjustments = defaultdict(int)
    for event in events:
        adjustments[ceil_step(event.ts, step)] -= event.delta
    return dict(adjustments)


def rebuild_missing_rows(
    rows: list[tuple[int, float | None]],
    events: list[Event],
    anchor_count: int,
    step: int,
) -> dict[int, float]:
    adjustments = reverse_adjustments(events, step)
    rebuilt = {}

    current_ts, current_count = rows[-1][0], anchor_count
    rebuilt[current_ts] = float(current_count)
    for ts, value in reversed(rows[:-1]):
        current_count += adjustments.get(current_ts, 0)
        if value is None:
            rebuilt[ts] = float(current_count)
        else:
            current_count = round(value)
            rebuilt[ts] = float(current_count)
        current_ts = ts
    return rebuilt


def parse_fetch_output(output: str) -> list[tuple[int, float | None]]:
    rows = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line == "bugs" or ":" not in line:
            continue
        ts_text, value_text = line.split(":", 1)
        ts = int(ts_text.strip())
        raw = value_text.strip().split()[0]
        if raw.lower() == "-nan":
            rows.append((ts, None))
        else:
            rows.append((ts, float(raw)))
    return rows


def fetch_rows(rrd_path: Path, start_ts: int, end_ts: int) -> list[tuple[int, float | None]]:
    result = subprocess.run(
        [
            "rrdtool",
            "fetch",
            str(rrd_path),
            "AVERAGE",
            "--start",
            str(start_ts),
            "--end",
            str(end_ts),
            "--resolution",
            "3600",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_fetch_output(result.stdout)


def replace_rows_in_dump(
    dump_text: str, replacements: dict[int, float], heartbeat: int | None = None
) -> tuple[str, int]:
    replaced = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal replaced
        ts = int(match.group("ts"))
        if ts not in replacements:
            return match.group(0)
        replaced += 1
        value = f"{replacements[ts]:.10e}"
        return f"{match.group(1)}{value}{match.group(4)}"

    dump_text = ROW_RE.sub(repl, dump_text)
    if heartbeat is not None:
        dump_text = HEARTBEAT_RE.sub(rf"\g<1>{heartbeat}\g<3>", dump_text)
    return dump_text, replaced


def collect_launchpad_events(start_ts: int, end_ts: int) -> list[Event]:
    lp = Launchpad.login_anonymously(
        "bug-stats", "production", config.CACHE_DIR
    )
    project = lp.projects[config.PROJECT]
    modified_since = datetime.fromtimestamp(start_ts, UTC).isoformat()
    tasks = project.searchTasks(modified_since=modified_since)

    events = []
    for task in tasks:
        events.extend(task_to_events(task, start_ts, end_ts))
    return events


def restore_rebuilt_rrd(
    rrd_path: Path, dump_text: str, backup_suffix: str | None
) -> Path | None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        xml_path = tmpdir_path / "dump.xml"
        restored_path = tmpdir_path / "restored.rrd"
        xml_path.write_text(dump_text, encoding="utf-8")
        subprocess.run(
            ["rrdtool", "restore", str(xml_path), str(restored_path)],
            check=True,
        )

        backup_path = None
        if backup_suffix:
            backup_path = rrd_path.with_name(f"{rrd_path.name}{backup_suffix}")
            shutil.copy2(rrd_path, backup_path)
        shutil.move(restored_path, rrd_path)
        return backup_path


def backfill_from_launchpad(
    rrd_path: Path, start_ts: int, end_ts: int, heartbeat: int | None = None
) -> tuple[int, Path | None]:
    rows = fetch_rows(rrd_path, start_ts, end_ts)
    if not rows:
        return 0, None

    anchor_count = None
    for _, value in reversed(rows):
        if value is not None:
            anchor_count = round(value)
            break
    if anchor_count is None:
        raise ValueError("No known data point found in the requested range.")

    events = collect_launchpad_events(start_ts, end_ts)
    replacements = rebuild_missing_rows(rows, events, anchor_count, 3600)

    dump = subprocess.run(
        ["rrdtool", "dump", str(rrd_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    updated_dump, replaced = replace_rows_in_dump(
        dump.stdout, replacements, heartbeat=heartbeat
    )
    backup_path = restore_rebuilt_rrd(
        rrd_path, updated_dump, f".bak.{int(time.time())}"
    )
    return replaced, backup_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Best-effort RRD backfill from Launchpad task dates."
    )
    parser.add_argument("rrd_file", type=Path, help="Path to the RRD file")
    parser.add_argument(
        "--start",
        type=int,
        required=True,
        help="Start timestamp (Unix seconds) for the reconstruction window",
    )
    parser.add_argument(
        "--end",
        type=int,
        required=True,
        help="End timestamp (Unix seconds) for the reconstruction window",
    )
    parser.add_argument(
        "--heartbeat",
        type=int,
        default=None,
        help="Optional heartbeat in seconds to write back into the RRD metadata",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    replaced, backup_path = backfill_from_launchpad(
        args.rrd_file, args.start, args.end, heartbeat=args.heartbeat
    )
    print(f"Backfilled {replaced} rows in {args.rrd_file}")
    if backup_path is not None:
        print(f"Backup written to {backup_path}")


if __name__ == "__main__":
    main()
