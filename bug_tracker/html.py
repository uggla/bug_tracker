from bug_tracker import config
from jinja2 import Environment, FileSystemLoader


def generate_html(latest_bugs, hottest_bugs):
    env = Environment(loader=FileSystemLoader(config.TEMPLATE_DIR))
    template = env.get_template("index.html.j2")

    html_content = template.render(
        project=config.PROJECT,
        graph_30d="bugs_new_30d.png",
        graph_6mo="bugs_new_6mo.png",
        latest_bugs=latest_bugs,
        hottest_bugs=hottest_bugs,
    )
    with open(config.HTML_FILE, "w") as f:
        f.write(html_content)
