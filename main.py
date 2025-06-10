import os
from bug_tracker import config
from bug_tracker.html import generate_html
from bug_tracker.launchpad import get_bug_data
from bug_tracker.rrd import create_rrd, update_rrd, generate_graph


def ensure_directories():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.HTML_DIR, exist_ok=True)
    os.makedirs(config.TEMPLATE_DIR, exist_ok=True)


def main():
    ensure_directories()
    create_rrd()
    count, latest_bugs, hottest_bugs = get_bug_data()
    print(f"New bugs for project '{config.PROJECT}': {count}")
    update_rrd(count)
    generate_graph()
    generate_html(latest_bugs, hottest_bugs)
    print(f"Dashboard generated: {config.HTML_FILE}")


if __name__ == "__main__":
    main()
