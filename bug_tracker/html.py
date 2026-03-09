from bug_tracker import config
from jinja2 import Environment, FileSystemLoader


def generate_html(latest_bugs, hottest_bugs):
    env = Environment(loader=FileSystemLoader(config.TEMPLATE_DIR))
    template = env.get_template("index.html.j2")

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
