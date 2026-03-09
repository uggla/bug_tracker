from datetime import date, timedelta

from bug_tracker import config
from jinja2 import Environment, FileSystemLoader


def is_current_week(date_str):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    try:
        d = date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return False
    return monday <= d <= sunday


def _mark_current_week(bugs):
    for bug in bugs:
        bug["is_current_week"] = is_current_week(bug.get("date", ""))
    return bugs


def generate_html(latest_bugs, hottest_bugs):
    env = Environment(loader=FileSystemLoader(config.TEMPLATE_DIR))
    template = env.get_template("index.html.j2")

    _mark_current_week(latest_bugs)
    _mark_current_week(hottest_bugs)

    periods = [
        {"key": "15d", "label": "15 Days"},
        {"key": "30d", "label": "1 Month"},
        {"key": "90d", "label": "3 Months"},
        {"key": "180d", "label": "6 Months"},
    ]

    html_content = template.render(
        project=config.PROJECT,
        periods=periods,
        latest_bugs=latest_bugs,
        hottest_bugs=hottest_bugs,
    )
    with open(config.HTML_FILE, "w") as f:
        f.write(html_content)
