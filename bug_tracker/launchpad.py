from bug_tracker import config
from launchpadlib.launchpad import Launchpad


def get_bug_data():
    lp = Launchpad.login_anonymously(
        "bug-stats", "production", config.CACHE_DIR
    )
    project = lp.projects[config.PROJECT]
    tasks = project.searchTasks(status=["New"])
    bugs = []

    for task in tasks:
        bug = task.bug
        bugs.append(
            {
                "id": bug.id,
                "title": bug.title,
                "link": bug.web_link,
                "date": bug.date_created,
                "heat": bug.heat,
            }
        )

    filtered_bugs = sorted(bugs, key=lambda x: x["date"], reverse=True)[:5]

    latest_bugs = []
    for bug in filtered_bugs:
        latest_bugs.append(
            {
                "id": bug["id"],
                "title": bug["title"],
                "link": bug["link"],
                "date": str(bug["date"])[:10],
                "heat": bug["heat"],
            }
        )

    filtered_bugs = sorted(bugs, key=lambda x: x["heat"], reverse=True)[:2]

    hottest_bugs = []
    for bug in filtered_bugs:
        hottest_bugs.append(
            {
                "id": bug["id"],
                "title": bug["title"],
                "link": bug["link"],
                "date": str(bug["date"])[:10],
                "heat": bug["heat"],
            }
        )

    return len(tasks), latest_bugs, hottest_bugs
