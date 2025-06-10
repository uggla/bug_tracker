import os
import subprocess

from bug_tracker import config


def create_rrd():
    if os.path.exists(config.RRD_FILE):
        return
    subprocess.run(
        [
            "rrdtool",
            "create",
            config.RRD_FILE,
            "--step",
            "3600",
            "DS:bugs:GAUGE:172800:0:10000",
            "RRA:AVERAGE:0.5:1:8760",
        ],
        check=True,
    )


def update_rrd(count):
    subprocess.run(
        ["rrdtool", "update", config.RRD_FILE, f"N:{count}"], check=True
    )


def generate_graph():
    subprocess.run(
        [
            "rrdtool",
            "graph",
            os.path.join(config.HTML_DIR, "bugs_new_30d.png"),
            "--start",
            "-30d",
            "--title",
            "New Bugs (Last 30 Days)",
            "--vertical-label",
            "Bugs",
            "--width",
            "800",
            "--height",
            "300",
            f"DEF:bugs={config.RRD_FILE}:bugs:AVERAGE",
            "LINE2:bugs#FF0000:New Bugs",
        ],
        check=True,
    )

    subprocess.run(
        [
            "rrdtool",
            "graph",
            os.path.join(config.HTML_DIR, "bugs_new_6mo.png"),
            "--start",
            "-180d",
            "--title",
            "New Bugs (Last 6 Months)",
            "--vertical-label",
            "Bugs",
            "--width",
            "800",
            "--height",
            "300",
            f"DEF:bugs={config.RRD_FILE}:bugs:AVERAGE",
            "LINE2:bugs#0000FF:New Bugs",
        ],
        check=True,
    )
