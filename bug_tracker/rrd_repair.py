import argparse
import shutil
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def fill_missing_rows(root: ET.Element) -> int:
    filled = 0
    for database in root.findall("./rra/database"):
        last_known = None
        for row in database.findall("row"):
            value = row.find("v")
            if value is None or value.text is None:
                continue

            current = value.text.strip()
            if current.lower() == "nan":
                if last_known is not None:
                    value.text = last_known
                    filled += 1
                continue

            last_known = current

    return filled


def set_heartbeat(root: ET.Element, heartbeat: int) -> None:
    for node in root.findall("./ds/minimal_heartbeat"):
        node.text = str(heartbeat)


def repair_rrd_file(
    rrd_path: Path,
    heartbeat: int | None = None,
    backup_suffix: str | None = None,
) -> tuple[int, Path | None]:
    rrd_path = rrd_path.resolve()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        xml_path = tmpdir_path / "dump.xml"
        restored_path = tmpdir_path / "restored.rrd"

        dump = subprocess.run(
            ["rrdtool", "dump", str(rrd_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        xml_path.write_text(dump.stdout, encoding="utf-8")

        tree = ET.parse(xml_path)
        root = tree.getroot()
        filled = fill_missing_rows(root)
        if heartbeat is not None:
            set_heartbeat(root, heartbeat)

        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        subprocess.run(
            ["rrdtool", "restore", str(xml_path), str(restored_path)],
            check=True,
        )

        backup_path = None
        if backup_suffix:
            backup_path = rrd_path.with_name(f"{rrd_path.name}{backup_suffix}")
            shutil.copy2(rrd_path, backup_path)
        shutil.move(restored_path, rrd_path)

    return filled, backup_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repair an RRD file by forward-filling missing NaN values."
    )
    parser.add_argument("rrd_file", type=Path, help="Path to the RRD file")
    parser.add_argument(
        "--heartbeat",
        type=int,
        default=None,
        help="Optional heartbeat in seconds to write back into the RRD metadata",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a backup copy before replacing the RRD",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    backup_suffix = None if args.no_backup else f".bak.{int(time.time())}"
    filled, backup_path = repair_rrd_file(
        args.rrd_file, heartbeat=args.heartbeat, backup_suffix=backup_suffix
    )
    print(f"Filled {filled} missing rows in {args.rrd_file}")
    if backup_path is not None:
        print(f"Backup written to {backup_path}")


if __name__ == "__main__":
    main()
