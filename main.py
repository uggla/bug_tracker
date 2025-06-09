import os
import subprocess
from launchpadlib.launchpad import Launchpad
from jinja2 import Environment, FileSystemLoader

PROJECT = "nova"
DATA_DIR = "data"
HTML_DIR = "html"
TEMPLATE_DIR = "templates"
RRD_FILE = os.path.join(DATA_DIR, "bugs_new.rrd")
GRAPH_FILE = os.path.join(HTML_DIR, "bugs_new.png")
HTML_FILE = os.path.join(HTML_DIR, "index.html")
CACHE_DIR = os.path.expanduser("~/.launchpadlib/cache")


def get_bug_data():
    lp = Launchpad.login_anonymously("bug-stats", "production", CACHE_DIR)
    project = lp.projects[PROJECT]
    tasks = project.searchTasks(
        status=["New"]
    )
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

    hotest_bugs = []
    for bug in filtered_bugs:
        hotest_bugs.append(
            {
                "id": bug["id"],
                "title": bug["title"],
                "link": bug["link"],
                "date": str(bug["date"])[:10],
                "heat": bug["heat"],
            }
        )

    return len(tasks), latest_bugs, hotest_bugs


def ensure_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(HTML_DIR, exist_ok=True)
    os.makedirs(TEMPLATE_DIR, exist_ok=True)


def create_rrd():
    if os.path.exists(RRD_FILE):
        return
    subprocess.run(
        [
            "rrdtool",
            "create",
            RRD_FILE,
            "--step",
            "3600",
            "DS:bugs:GAUGE:172800:0:10000",
            "RRA:AVERAGE:0.5:1:8760",
        ],
        check=True,
    )


def update_rrd(count):
    subprocess.run(["rrdtool", "update", RRD_FILE, f"N:{count}"], check=True)


def generate_graph():
    subprocess.run(
        [
            "rrdtool",
            "graph",
            os.path.join(HTML_DIR, "bugs_new_30d.png"),
            "--start",
            "-30d",
            "--title",
            f"New Bugs (Last 30 Days)",
            "--vertical-label",
            "Bugs",
            "--width",
            "800",
            "--height",
            "300",
            f"DEF:bugs={RRD_FILE}:bugs:AVERAGE",
            "LINE2:bugs#FF0000:New Bugs",
        ],
        check=True,
    )

    subprocess.run(
        [
            "rrdtool",
            "graph",
            os.path.join(HTML_DIR, "bugs_new_6mo.png"),
            "--start",
            "-180d",
            "--title",
            f"New Bugs (Last 6 Months)",
            "--vertical-label",
            "Bugs",
            "--width",
            "800",
            "--height",
            "300",
            f"DEF:bugs={RRD_FILE}:bugs:AVERAGE",
            "LINE2:bugs#0000FF:New Bugs",
        ],
        check=True,
    )


def generate_html(latest_bugs, hotest_bugs):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("index.html.j2")

    html_content = template.render(
        project=PROJECT,
        graph_30d="bugs_new_30d.png",
        graph_6mo="bugs_new_6mo.png",
        latest_bugs=latest_bugs,
        hotest_bugs=hotest_bugs,
    )
    with open(HTML_FILE, "w") as f:
        f.write(html_content)


def main():
    ensure_directories()
    create_rrd()
    count, latest_bugs, hotest_bugs = get_bug_data()
    print(f"New bugs for project '{PROJECT}': {count}")
    update_rrd(count)
    generate_graph()
    generate_html(latest_bugs, hotest_bugs)
    print(f"Dashboard generated: {HTML_FILE}")


if __name__ == "__main__":
    main()
