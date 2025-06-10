import os
import time
from datetime import date
from pathlib import Path
from bs4 import BeautifulSoup
from bug_tracker.html import generate_html
from bug_tracker import config


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

    generate_html(fake_latest_bugs, fake_hottest_bugs)
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
