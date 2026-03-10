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
