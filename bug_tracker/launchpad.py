import json
import os
import time

from bug_tracker import config
from launchpadlib.launchpad import Launchpad


def _extract_bugs(tasks, limit):
    bugs = []
    for task in tasks[:limit]:
        bug = task.bug
        bugs.append(
            {
                "id": bug.id,
                "title": bug.title,
                "link": bug.web_link,
                "date": str(bug.date_created)[:10],
                "heat": bug.heat,
            }
        )
    return bugs


def _load_cache():
    if not os.path.exists(config.BUG_CACHE_FILE):
        return None
    with open(config.BUG_CACHE_FILE, "r") as f:
        cache = json.load(f)
    if time.time() - cache["timestamp"] > config.BUG_CACHE_TTL:
        return None
    return cache["data"]


def _save_cache(data):
    cache = {"timestamp": time.time(), "data": data}
    with open(config.BUG_CACHE_FILE, "w") as f:
        json.dump(cache, f)


def _fetch_bug_data():
    lp = Launchpad.login_anonymously(
        "bug-stats", "production", config.CACHE_DIR
    )
    project = lp.projects[config.PROJECT]

    all_tasks = project.searchTasks(status=["New"])
    count = all_tasks.total_size

    latest_tasks = project.searchTasks(
        status=["New"], order_by="-datecreated"
    )
    latest_bugs = _extract_bugs(latest_tasks, 5)

    hottest_tasks = project.searchTasks(
        status=["New"], order_by="-heat"
    )
    hottest_bugs = _extract_bugs(hottest_tasks, 2)

    return {"count": count, "latest_bugs": latest_bugs, "hottest_bugs": hottest_bugs}


def get_bug_data():
    cached = _load_cache()
    if cached:
        print("Using cached bug data.")
        return cached["count"], cached["latest_bugs"], cached["hottest_bugs"]

    print("Fetching bug data from Launchpad...")
    data = _fetch_bug_data()
    _save_cache(data)
    return data["count"], data["latest_bugs"], data["hottest_bugs"]
