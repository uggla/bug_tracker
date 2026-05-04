# 📊 Launchpad Bug Tracker (RRD-based)

This project tracks the number of **"New" bugs** for a Launchpad project (e.g., `nova`) and stores the count daily in a **Round-Robin Database (RRD)**. It then:

- Generates **SVG graphs** of the last 30 days
- Creates a simple **HTML dashboard** to view the graph

---

## 🚀 Features

- Accesses Launchpad bug tracker using `launchpadlib`
- Stores historical data using `rrdtool` (command-line)
- Graphs daily bug counts over time
- Produces a clean HTML5 dashboard

---

## ⚡️ Quickstart with [`uv`](https://github.com/astral-sh/uv)

> Requires Python ≥ 3.12 and [`uv`](https://github.com/astral-sh/uv)

### 1. Install system dependencies

Make sure `rrdtool` is available on your system:

```bash
# On Debian/Ubuntu
sudo apt install rrdtool
```

## Repair a damaged RRD

If a full filesystem or a long outage caused `NaN` gaps in `data/bugs_new.rrd`,
you can rebuild the file by forward-filling missing values from the last known
sample and increase the heartbeat:

```bash
uv run python -m bug_tracker.rrd_repair data/bugs_new.rrd --heartbeat 172800
```

This command writes a backup copy next to the original RRD before replacing it.

If you want a better reconstruction than a simple forward-fill, you can
rebuild missing rows from Launchpad task dates:

```bash
uv run python -m bug_tracker.rrd_backfill data/bugs_new.rrd --start 1776819600 --end 1777914009 --heartbeat 172800
```

This backfill uses Launchpad task dates such as creation time and the date a
task left the `New` status. It is more faithful than forward-filling, but it
remains a best-effort reconstruction for bugs that were reopened multiple
times during the missing window.
