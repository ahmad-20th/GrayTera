"""
Nikto Scanner Integration for GrayTera
--------------------------------------
- Runs Nikto scanner
- Saves XML output
- Parses vulnerabilities from XML
- Supports JSON + SQLite persistence
"""

import os
import shutil
import subprocess
import json
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    from core.target import Vulnerability
except Exception:
    Vulnerability = None


# fallback BaseScanner if GrayTera base is not available
try:
    from scanners.base_scanner import BaseScanner
except Exception:
    class BaseScanner:
        def __init__(self, name: str):
            self.name = name


class NiktoScanner(BaseScanner):
    def __init__(
        self,
        nikto_path: Optional[str] = None,
        persist: Optional[str] = None,
        db_path: Optional[str] = None
    ):
        """
        persist: None | "json" | "sqlite"
        """
        super().__init__("Nikto Scanner")

        self.nikto_cmd = nikto_path or self._find_nikto()
        self._missing = not bool(self.nikto_cmd)

        self.persist = persist
        self.db_path = db_path or "data/nikto_results.db"

        if persist == "sqlite":
            self._init_sqlite_db()

    # ---------------------------------------------------------
    # Find Nikto in system PATH
    # ---------------------------------------------------------
    def _find_nikto(self) -> Optional[str]:
        for name in ("nikto", "nikto.pl"):
            path = shutil.which(name)
            if path:
                return path
        return None

    # ---------------------------------------------------------
    # Initialize SQLite database
    # ---------------------------------------------------------
    def _init_sqlite_db(self):
        os.makedirs("data", exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            run_at TEXT,
            xml_path TEXT
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER,
            name TEXT,
            uri TEXT,
            description TEXT,
            metadata TEXT,
            FOREIGN KEY(scan_id) REFERENCES scans(id)
        );
        """)

        conn.commit()
        conn.close()

    # ---------------------------------------------------------
    # Save JSON file
    # ---------------------------------------------------------
    def _save_json(self, target: str, ts: str, findings: List[Dict], xml_path: str):
        os.makedirs("data", exist_ok=True)
        out = f"data/nikto-{target}-{ts}.json"

        with open(out, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "target": target,
                    "timestamp": ts,
                    "xml": xml_path,
                    "findings": findings,
                },
                fh,
                indent=2
            )
        return out

    # ---------------------------------------------------------
    # Save SQLite data
    # ---------------------------------------------------------
    def _save_sqlite(self, target: str, ts: str, data: List[Dict], xml_path: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO scans (target, run_at, xml_path) VALUES (?, ?, ?)",
            (target, ts, xml_path)
        )
        scan_id = cur.lastrowid

        for f in data:
            cur.execute(
                """
                INSERT INTO findings (scan_id, name, uri, description, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    f["name"],
                    f.get("uri"),
                    f["description"],
                    json.dumps(f["metadata"]),
                )
            )

        conn.commit()
        conn.close()

    # ---------------------------------------------------------
    # Build Nikto command
    # ---------------------------------------------------------
    def _build_cmd(self, target: str, xml_path: str) -> List[str]:
        return [
            self.nikto_cmd,
            "-h", target,
            "-o", xml_path,
            "-Format", "xml"
        ]

    # ---------------------------------------------------------
    # Parse XML
    # ---------------------------------------------------------
    def _parse_xml(self, xml_file: str):
        findings = []

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for item in root.findall(".//item"):
                desc = item.findtext("description") or item.findtext("name") or "Nikto Finding"
                uri = item.findtext("uri") or item.findtext("cgi")
                metadata = {child.tag: child.text for child in item}

                record = {
                    "name": desc,
                    "description": desc,
                    "uri": uri,
                    "metadata": metadata
                }

                # Wrap into Vulnerability class if available
                if Vulnerability:
                    try:
                        findings.append(Vulnerability(
                            name=record["name"],
                            description=record["description"],
                            uri=record["uri"],
                            metadata=record["metadata"]
                        ))
                    except:
                        findings.append(record)
                else:
                    findings.append(record)

        except Exception as e:
            print("XML Parser Error:", e)

        return findings

    # ---------------------------------------------------------
    # MAIN SCAN FUNCTION
    # ---------------------------------------------------------
    def scan(self, target_url: str):
        if self._missing:
            print("Nikto not found in PATH.")
            return []

        os.makedirs("data", exist_ok=True)

        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        safe = target_url.replace("://", "_").replace("/", "_")

        xml_output = f"data/nikto-{safe}-{ts}.xml"

        cmd = self._build_cmd(target_url, xml_output)

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except Exception as e:
            print("Error executing Nikto:", e)
            return []

        if not os.path.exists(xml_output):
            print("Nikto did not generate XML output.")
            return []

        findings = self._parse_xml(xml_output)

        cleaned = [
            {
                "name": getattr(f, "name", f["name"]),
                "description": getattr(f, "description", f["description"]),
                "uri": getattr(f, "uri", f.get("uri")),
                "metadata": getattr(f, "metadata", f.get("metadata")),
            }
            for f in findings
        ]

        if self.persist == "json":
            self._save_json(safe, ts, cleaned, xml_output)

        if self.persist == "sqlite":
            self._save_sqlite(safe, ts, cleaned, xml_output)

        return findings
