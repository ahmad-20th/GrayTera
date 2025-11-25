"""
Results Viewer for Nikto SQLite Output
-------------------------------------
This file lets you read the SQLite scan results:
    - list scans
    - list findings per scan
"""

import sqlite3
import json
import sys
from tabulate import tabulate


def list_scans(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, target, run_at, xml_path FROM scans ORDER BY id DESC")
    rows = cur.fetchall()

    conn.close()
    return rows


def list_findings(db_path: str, scan_id: int):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, uri, description, metadata FROM findings WHERE scan_id = ?",
        (scan_id,)
    )
    rows = cur.fetchall()

    conn.close()
    return rows


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 results_viewer.py data/nikto_results.db")
        print("  python3 results_viewer.py data/nikto_results.db --scan 1")
        sys.exit(0)

    db_path = sys.argv[1]

    if len(sys.argv) == 2:
        scans = list_scans(db_path)
        print("\n=== Available Scans ===\n")
        print(tabulate(scans, headers=["ID", "Target", "Run At", "XML Path"], tablefmt="grid"))
        return

    if "--scan" in sys.argv:
        try:
            scan_id = int(sys.argv[sys.argv.index("--]()))
