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


PERIODS = [
    ("15d", "15 Days"),
    ("30d", "1 Month"),
    ("90d", "3 Months"),
    ("180d", "6 Months"),
]


def generate_graph():
    for period, title in PERIODS:
        subprocess.run(
            [
                "rrdtool",
                "graph",
                os.path.join(config.HTML_DIR, f"bugs_new_{period}.svg"),
                "--start",
                f"-{period}",
                "--title",
                f"New Bugs ({title})",
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
                os.path.join(config.HTML_DIR, f"bugs_delta_{period}.svg"),
                "--start",
                f"-{period}",
                "--title",
                f"Daily Bug Count Change ({title})",
                "--vertical-label",
                "Delta",
                "--width",
                "800",
                "--height",
                "200",
                f"DEF:bugs={config.RRD_FILE}:bugs:AVERAGE",
                "CDEF:delta=bugs,PREV(bugs),-",
                "CDEF:pos=delta,0,GT,delta,0,IF",
                "CDEF:neg=delta,0,LT,delta,0,IF",
                "AREA:pos#CC0000:Increase",
                "AREA:neg#00AA00:Decrease",
                "HRULE:0#000000",
            ],
            check=True,
        )
