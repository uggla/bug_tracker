import json
import os
import time
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from bs4 import BeautifulSoup
from bug_tracker.html import generate_html, is_less_than_one_week
from bug_tracker.launchpad import _load_cache, _save_cache
from bug_tracker.rrd_backfill import (
    rebuild_missing_rows,
    replace_rows_in_dump,
    task_to_events,
)
from bug_tracker.rrd import PERIODS, generate_graph
from bug_tracker.rrd_repair import fill_missing_rows, set_heartbeat
from bug_tracker import config
import xml.etree.ElementTree as ET


def assertRecentFile(path, filetype):
    directory = Path(path)
    html_files = list(directory.glob(filetype))
    assert html_files

    latest_file = max(html_files, key=os.path.getctime)
    created_time = os.path.getctime(latest_file)

    assert (time.time() - created_time) < 60


def assertHTMLTables(file, expected_headers, expected_rows):
    with open(file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    headers = [th.text.strip() for th in soup.select("table th")]
    assert headers == expected_headers

    rows = [td.text.strip() for td in soup.select("tr td")]
    assert rows == expected_rows


def test_fake():
    assert 1 == 1


def test_generate_html():
    fake_latest_bugs = [
        {
            "id": "2112811",
            "title": "This is a fake bug",
            "link": "https://bugs.launchpad.net/bugs/2112811",
            "date": date.today().isoformat(),
            "heat": 12,
        },
        {
            "id": "2112810",
            "title": "This is a second fake bug",
            "link": "https://bugs.launchpad.net/bugs/2112810",
            "date": "2025-06-07",
            "heat": 11,
        },
        {
            "id": "2112808",
            "title": "nova-compute restart breaks queued live migration objects",
            "link": "https://bugs.launchpad.net/bugs/2112808",
            "date": "2025-06-06",
            "heat": 6,
        },
    ]

    fake_hottest_bugs = [
        {
            "id": "2051907",
            "title": "Failed to live migrate instance to another host",
            "link": "https://bugs.launchpad.net/bugs/2051907",
            "date": "2024-02-01",
            "heat": 54,
        }
    ]

    generate_html(3, fake_latest_bugs, fake_hottest_bugs)
    assertRecentFile(config.HTML_DIR, "index.html")
    expected_headers = [
        "ID",
        "Title",
        "Date",
        "Heat",
        "ID",
        "Title",
        "Date",
        "Heat",
    ]
    expected_rows = [
        "#2112811",
        "This is a fake bug",
        date.today().isoformat(),
        "12",
        "#2112810",
        "This is a second fake bug",
        "2025-06-07",
        "11",
        "#2112808",
        "nova-compute restart breaks queued live migration objects",
        "2025-06-06",
        "6",
        "#2051907",
        "Failed to live migrate instance to another host",
        "2024-02-01",
        "54",
    ]

    assertHTMLTables(config.HTML_FILE, expected_headers, expected_rows)

    with open(config.HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    assert "bugs_new_30d.svg" in html
    assert "bugs_delta_30d.svg" in html


FAKE_DATA = {
    "count": 42,
    "latest_bugs": [{"id": 1, "title": "bug1", "link": "#", "date": "2025-01-01", "heat": 10}],
    "hottest_bugs": [{"id": 2, "title": "bug2", "link": "#", "date": "2025-01-02", "heat": 99}],
}


def test_cache_returns_data_when_fresh(tmp_path, monkeypatch):
    cache_file = tmp_path / "bug_cache.json"
    monkeypatch.setattr(config, "BUG_CACHE_FILE", str(cache_file))

    _save_cache(FAKE_DATA)
    result = _load_cache()

    assert result is not None
    assert result["count"] == 42
    assert result["latest_bugs"][0]["id"] == 1
    assert result["hottest_bugs"][0]["id"] == 2


def test_cache_returns_none_when_expired(tmp_path, monkeypatch):
    cache_file = tmp_path / "bug_cache.json"
    monkeypatch.setattr(config, "BUG_CACHE_FILE", str(cache_file))

    cache = {"timestamp": time.time() - 1300, "data": FAKE_DATA}
    with open(cache_file, "w") as f:
        json.dump(cache, f)

    result = _load_cache()
    assert result is None


def test_cache_returns_none_when_no_file(tmp_path, monkeypatch):
    cache_file = tmp_path / "bug_cache.json"
    monkeypatch.setattr(config, "BUG_CACHE_FILE", str(cache_file))

    result = _load_cache()
    assert result is None


def test_is_less_than_one_week_today():
    assert is_less_than_one_week(date.today().isoformat()) is True


def test_is_less_than_one_week_3_days_ago():
    three_days_ago = (date.today() - timedelta(days=3)).isoformat()
    assert is_less_than_one_week(three_days_ago) is True


def test_is_less_than_one_week_old_date():
    assert is_less_than_one_week("2020-01-01") is False


def test_current_week_bugs_have_class():
    fake_latest_bugs = [
        {
            "id": "2112811",
            "title": "This is a fake bug",
            "link": "https://bugs.launchpad.net/bugs/2112811",
            "date": date.today().isoformat(),
            "heat": 12,
        },
        {
            "id": "2112810",
            "title": "This is a second fake bug",
            "link": "https://bugs.launchpad.net/bugs/2112810",
            "date": "2025-06-07",
            "heat": 11,
        },
        {
            "id": "2112808",
            "title": "nova-compute restart breaks queued live migration objects",
            "link": "https://bugs.launchpad.net/bugs/2112808",
            "date": "2025-06-06",
            "heat": 6,
        },
    ]

    fake_hottest_bugs = [
        {
            "id": "2051907",
            "title": "Failed to live migrate instance to another host",
            "link": "https://bugs.launchpad.net/bugs/2051907",
            "date": "2024-02-01",
            "heat": 54,
        }
    ]

    generate_html(3, fake_latest_bugs, fake_hottest_bugs)

    with open(config.HTML_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    rows = soup.select("table tbody tr")
    # First bug has today's date, should have current-week class
    assert "current-week" in rows[0].get("class", [])
    # Other bugs have old dates, should not have current-week class
    assert "current-week" not in rows[1].get("class", [])
    assert "current-week" not in rows[2].get("class", [])
    assert "current-week" not in rows[3].get("class", [])


def test_generate_graph_outputs_svg(monkeypatch, tmp_path):
    commands = []

    def fake_run(cmd, check):
        commands.append((cmd, check))

    monkeypatch.setattr(config, "HTML_DIR", str(tmp_path))
    monkeypatch.setattr(config, "RRD_FILE", str(tmp_path / "bugs_new.rrd"))
    monkeypatch.setattr("bug_tracker.rrd.subprocess.run", fake_run)

    generate_graph()

    assert len(commands) == len(PERIODS) * 2

    output_files = [cmd[2] for cmd, check in commands]
    assert all(check is True for _, check in commands)
    assert all(path.endswith(".svg") for path in output_files)
    assert any(path.endswith("bugs_new_30d.svg") for path in output_files)
    assert any(path.endswith("bugs_delta_30d.svg") for path in output_files)
    assert all("--imgformat" in cmd for cmd, _ in commands)
    assert all("SVG" in cmd for cmd, _ in commands)


def test_fill_missing_rows_forward_fills_internal_nan_values():
    root = ET.fromstring(
        """
        <rrd>
          <rra>
            <database>
              <row><v>NaN</v></row>
              <row><v>1.9200000000e+02</v></row>
              <row><v>NaN</v></row>
              <row><v>NaN</v></row>
              <row><v>2.0100000000e+02</v></row>
            </database>
          </rra>
        </rrd>
        """
    )

    filled = fill_missing_rows(root)
    values = [node.text for node in root.findall("./rra/database/row/v")]

    assert filled == 2
    assert values == [
        "NaN",
        "1.9200000000e+02",
        "1.9200000000e+02",
        "1.9200000000e+02",
        "2.0100000000e+02",
    ]


def test_set_heartbeat_updates_rrd_metadata():
    root = ET.fromstring(
        """
        <rrd>
          <ds>
            <minimal_heartbeat>172800</minimal_heartbeat>
          </ds>
        </rrd>
        """
    )

    set_heartbeat(root, 1209600)

    assert root.findtext("./ds/minimal_heartbeat") == "1209600"


def test_task_to_events_uses_launchpad_dates():
    task = SimpleNamespace(
        date_created="2026-04-22T10:15:00+00:00",
        date_left_new="2026-04-24T09:00:00+00:00",
        date_left_closed=None,
        status="Confirmed",
    )

    events = task_to_events(task, 1776800000, 1777000000)

    assert [(event.ts, event.delta) for event in events] == [
        (1776852900, 1),
        (1777021200, -1),
    ]


def test_rebuild_missing_rows_applies_reverse_events():
    rows = [
        (200, None),
        (300, None),
        (400, 10.0),
    ]
    events = [
        SimpleNamespace(ts=250, delta=1),
        SimpleNamespace(ts=350, delta=-1),
    ]

    rebuilt = rebuild_missing_rows(rows, events, anchor_count=10, step=100)

    assert rebuilt == {
        400: 10.0,
        300: 10.0,
        200: 11.0,
    }


def test_replace_rows_in_dump_updates_selected_timestamps_and_heartbeat():
    dump = """
<rrd>
  <ds><minimal_heartbeat>172800</minimal_heartbeat></ds>
  <rra><database>
    <!-- 2026-04-22 04:00:00 CEST / 1776823200 --> <row><v>NaN</v></row>
    <!-- 2026-04-22 05:00:00 CEST / 1776826800 --> <row><v>NaN</v></row>
  </database></rra>
</rrd>
"""

    updated, replaced = replace_rows_in_dump(
        dump,
        {1776823200: 183.0, 1776826800: 184.0},
        heartbeat=172800,
    )

    assert replaced == 2
    assert "1.8300000000e+02" in updated
    assert "1.8400000000e+02" in updated
    assert "<minimal_heartbeat>172800</minimal_heartbeat>" in updated
