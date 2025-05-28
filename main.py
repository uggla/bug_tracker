import os
import time
import subprocess
from launchpadlib.launchpad import Launchpad

PROJECT = "nova"
DATA_DIR = "data"
HTML_DIR = "html"
RRD_FILE = os.path.join(DATA_DIR, "bugs_new.rrd")
GRAPH_FILE = os.path.join(HTML_DIR, "bugs_new.png")
HTML_FILE = os.path.join(HTML_DIR, "index.html")
CACHE_DIR = os.path.expanduser("~/.launchpadlib/cache")

def get_bug_count():
    lp = Launchpad.login_anonymously("bug-stats", "production", CACHE_DIR)
    project = lp.projects[PROJECT]
    tasks = project.searchTasks(status=["New"])
    return len(tasks)

def ensure_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(HTML_DIR, exist_ok=True)

def create_rrd():
    if os.path.exists(RRD_FILE):
        return
    subprocess.run([
        "rrdtool", "create", RRD_FILE,
        "--step", "3600",                          # 1 point/hour
        "DS:bugs:GAUGE:172800:0:10000",            # GAUGE, max 2 days gap
        "RRA:AVERAGE:0.5:1:8760"                   # 1 year of hourly data
    ], check=True)

def update_rrd(count):
    subprocess.run([
        "rrdtool", "update", RRD_FILE, f"N:{count}"
    ], check=True)

def generate_graph():
    subprocess.run([
        "rrdtool", "graph", GRAPH_FILE,
        "--start", "-30d",
        "--title", f"New Bugs on Launchpad ({PROJECT})",
        "--vertical-label", "Bugs",
        "--width", "800",
        "--height", "300",
        f"DEF:bugs={RRD_FILE}:bugs:AVERAGE",
        "LINE2:bugs#FF0000:New Bugs"
    ], check=True)

def generate_html():
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Launchpad New Bugs - {PROJECT}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: sans-serif; background: #f5f5f5; text-align: center; margin: 2em; }}
    img {{ max-width: 100%; height: auto; border: 1px solid #ccc; background: #fff; padding: 10px; }}
  </style>
</head>
<body>
  <h1>New Bugs on Launchpad: <code>{PROJECT}</code></h1>
  <p>Data from the last 30 days</p>
  <img src="bugs_new.png" alt="New Bugs Graph">
</body>
</html>"""
    with open(HTML_FILE, "w") as f:
        f.write(html)

def main():
    ensure_directories()
    create_rrd()
    count = get_bug_count()
    print(f"New bugs for project '{PROJECT}': {count}")
    update_rrd(count)
    generate_graph()
    generate_html()
    print(f"Dashboard generated: {HTML_FILE}")

if __name__ == "__main__":
    main()
