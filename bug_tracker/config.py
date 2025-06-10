import os

PROJECT = "nova"
DATA_DIR = "data"
HTML_DIR = "html"
TEMPLATE_DIR = "templates"
RRD_FILE = os.path.join(DATA_DIR, "bugs_new.rrd")
GRAPH_FILE = os.path.join(HTML_DIR, "bugs_new.png")
HTML_FILE = os.path.join(HTML_DIR, "index.html")
CACHE_DIR = os.path.expanduser("~/.launchpadlib/cache")
