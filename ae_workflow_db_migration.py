#!/usr/bin/env python3
"""
================================================================================
AutomationEdge Workflow Database Connection Migration Utility
================================================================================
Purpose:
  Batch-updates AutomationEdge Process Studio workflows (.psw) and processes (.psp)
  to mitigate Database Idle Timeout issues (e.g. IDFC FIRST Bank UATRPA2 issue).

Features Configured:
  1. Keep Alive Interval (seconds):
     Keeps database connections alive by sending periodic heartbeat queries.
     (Default: 900 seconds / 15 minutes for a 30-minute DB IDLE_TIME limit).
  2. Lazy Connect (checkbox):
     Defers establishing database connections until the step actually executes.
     (Applied to all DB steps EXCEPT 'Database Join' as per product design).

Supported Database Dialects:
  - Oracle
  - PostgreSQL
  - MS SQL Server / Generic JDBC

Usage:
  python ae_workflow_db_migration.py --path "E:/Workflows/IDFC_Repayment"
  python ae_workflow_db_migration.py --path "./workflows" --keep-alive 900 --dry-run
================================================================================
"""

import os
import sys
import glob
import shutil
import logging
import argparse
import datetime
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple, Any

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AE_DB_Migrator")

# ANSI Color Codes for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Steps that MUST be excluded from Lazy Connect
EXCLUDED_LAZY_CONNECT_STEP_TYPES = [
    "databasejoin",
    "dbjoin",
    "database_join"
]

# Standard Database Step Types in Process Studio
KNOWN_DB_STEP_TYPES = [
    "tableinput",
    "tableoutput",
    "execsql",
    "executesqlscript",
    "dblookup",
    "databaselookup",
    "insertupdate",
    "update",
    "delete",
    "calldbprocedure",
    "dbproc",
    "synchronizeaftermerge",
    "dimensionlookup",
    "combinationlookup",
    "databasejoin",
    "dbjoin"
]

class WorkflowMigrator:
    def __init__(self, target_path: str, keep_alive_seconds: int = 900, lazy_connect: bool = True, dry_run: bool = False, create_backup: bool = True):
        self.target_path = Path(target_path).resolve()
        self.keep_alive_seconds = keep_alive_seconds
        self.lazy_connect = lazy_connect
        self.dry_run = dry_run
        self.create_backup = create_backup
        
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.target_path / f"backup_pre_migration_{self.timestamp}" if self.target_path.is_dir() else self.target_path.parent / f"backup_pre_migration_{self.timestamp}"
        
        self.summary = {
            "scanned_files": 0,
            "modified_files": 0,
            "skipped_files": 0,
            "total_connections_updated": 0,
            "total_db_steps_inspected": 0,
            "database_join_skipped_count": 0,
            "file_details": []
        }

    def run(self) -> Dict[str, Any]:
        """Execute batch scan and migration across workflow files."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}============================================================================={Colors.END}")
        print(f"{Colors.BOLD}  AUTOMATIONEDGE DATABASE CONNECTION MIGRATION UTILITY{Colors.END}")
        print(f"{Colors.CYAN}============================================================================={Colors.END}")
        print(f"  • Target Path:         {self.target_path}")
        print(f"  • Keep-Alive Interval: {self.keep_alive_seconds}s (Heartbeat query interval)")
        print(f"  • Lazy Connect:        {'ENABLED (Y)' if self.lazy_connect else 'DISABLED (N)'}")
        print(f"  • Mode:                {Colors.YELLOW + 'DRY-RUN (Simulated)' + Colors.END if self.dry_run else Colors.GREEN + 'LIVE MIGRATION' + Colors.END}")
        print(f"  • Auto-Backup:         {'YES -> ' + str(self.backup_dir) if self.create_backup and not self.dry_run else 'NO'}")
        print(f"{Colors.CYAN}=============================================================================\n{Colors.END}")

        if not self.target_path.exists():
            logger.error(f"Target path does not exist: {self.target_path}")
            return self.summary

        # Find all .psw and .psp files
        files_to_process = []
        if self.target_path.is_file():
            if self.target_path.suffix.lower() in [".psw", ".psp", ".xml", ".ktr", ".kjb"]:
                files_to_process.append(self.target_path)
        else:
            for ext in ["*.psw", "*.psp", "*.xml", "*.ktr", "*.kjb"]:
                files_to_process.extend(self.target_path.rglob(ext))

        self.summary["scanned_files"] = len(files_to_process)
        if not files_to_process:
            logger.warning("No Process Studio workflow (.psw) or process (.psp) files found.")
            return self.summary

        logger.info(f"Discovered {len(files_to_process)} workflow file(s). Processing...")

        for file_path in files_to_process:
            self._process_workflow_file(file_path)

        self._print_summary_report()
        self._export_json_report()
        return self.summary

    def _process_workflow_file(self, file_path: Path):
        """Parse XML workflow and inject keep_alive and lazy_connect attributes."""
        rel_path = file_path.name
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception as e:
                logger.warning(f"Could not read {file_path.name} (possibly binary/encrypted): {e}")
                self.summary["skipped_files"] += 1
                return

        # Handle XML Parsing
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            logger.warning(f"Skipping {file_path.name}: Not valid unencrypted XML ({e})")
            self.summary["skipped_files"] += 1
            return

        file_modified = False
        conns_updated = 0
        db_steps_found = 0
        db_joins_skipped = 0
        inspected_steps = []

        # 1. Update Global / Embedded <connection> blocks
        for conn_elem in root.findall(".//connection"):
            conn_name = conn_elem.findtext("name", default="Unnamed Connection")
            conn_type = conn_elem.findtext("type", default="GENERIC").upper()
            
            # Ensure <attributes> container exists
            attr_container = conn_elem.find("attributes")
            if attr_container is None:
                attr_container = ET.SubElement(conn_elem, "attributes")

            # Update or create Keep Alive Interval attribute
            keep_alive_updated = self._set_or_update_attribute(
                attr_container,
                code="KEEP_ALIVE_INTERVAL",
                value=str(self.keep_alive_seconds),
                attr_tag="keep_alive_interval"
            )

            # Update or create Lazy Connect attribute
            lazy_connect_val = "Y" if self.lazy_connect else "N"
            lazy_updated = self._set_or_update_attribute(
                attr_container,
                code="LAZY_CONNECT",
                value=lazy_connect_val,
                attr_tag="lazy_connect"
            )

            # Also ensure direct XML tags if Process Studio uses root connection tags
            self._ensure_direct_tag(conn_elem, "keep_alive_interval", str(self.keep_alive_seconds))
            self._ensure_direct_tag(conn_elem, "lazy_connect", lazy_connect_val)

            if keep_alive_updated or lazy_updated:
                file_modified = True
                conns_updated += 1
                logger.info(f"  [DB Connection] -> Configured '{conn_name}' (Type: {conn_type}) with KeepAlive={self.keep_alive_seconds}s, LazyConnect={lazy_connect_val}")

        # 2. Inspect and tag step-level database configurations
        for step_elem in root.findall(".//step"):
            step_name = step_elem.findtext("name", default="Unnamed Step")
            step_type = (step_elem.findtext("type", default="") or "").lower().strip()

            if any(k in step_type for k in KNOWN_DB_STEP_TYPES) or step_elem.find("connection") is not None:
                db_steps_found += 1
                is_db_join = any(ex in step_type for ex in EXCLUDED_LAZY_CONNECT_STEP_TYPES)

                if is_db_join:
                    db_joins_skipped += 1
                    # Database Join steps only get Keep-Alive, Lazy Connect remains disabled
                    self._ensure_direct_tag(step_elem, "lazy_connect", "N")
                    self._ensure_direct_tag(step_elem, "keep_alive_interval", str(self.keep_alive_seconds))
                    inspected_steps.append({"step": step_name, "type": step_type, "lazy_connect": "N (EXCLUDED)", "keep_alive": self.keep_alive_seconds})
                    logger.info(f"  [DB Step: Join] -> '{step_name}': Lazy Connect EXCLUDED (KeepAlive={self.keep_alive_seconds}s)")
                else:
                    self._ensure_direct_tag(step_elem, "lazy_connect", "Y" if self.lazy_connect else "N")
                    self._ensure_direct_tag(step_elem, "keep_alive_interval", str(self.keep_alive_seconds))
                    inspected_steps.append({"step": step_name, "type": step_type, "lazy_connect": "Y", "keep_alive": self.keep_alive_seconds})
                    logger.info(f"  [DB Step]       -> '{step_name}' ({step_type}): Lazy Connect ENABLED")

                file_modified = True

        # Save changes if modified
        if file_modified:
            self.summary["modified_files"] += 1
            self.summary["total_connections_updated"] += conns_updated
            self.summary["total_db_steps_inspected"] += db_steps_found
            self.summary["database_join_skipped_count"] += db_joins_skipped

            if not self.dry_run:
                if self.create_backup:
                    self._backup_file(file_path)

                # Write updated XML
                try:
                    xml_str = ET.tostring(root, encoding="utf-8", method="xml")
                    # Prepend XML declaration
                    final_output = b'<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
                    with open(file_path, "wb") as f:
                        f.write(final_output)
                    logger.info(f" {Colors.GREEN}[SAVED]{Colors.END} {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed writing updated file {file_path.name}: {e}")
            else:
                logger.info(f" {Colors.YELLOW}[DRY-RUN MATCH]{Colors.END} {file_path.name} would be updated.")

            self.summary["file_details"].append({
                "file": str(file_path),
                "connections_updated": conns_updated,
                "db_steps_count": db_steps_found,
                "db_joins_skipped": db_joins_skipped,
                "steps": inspected_steps
            })

    def _set_or_update_attribute(self, attr_container: ET.Element, code: str, value: str, attr_tag: str) -> bool:
        """Helper to find or create attribute in Process Studio <attributes> container."""
        # Check existing <attribute><code>CODE</code><attribute>VAL</attribute></attribute>
        found = False
        for attr in attr_container.findall("attribute"):
            code_el = attr.find("code")
            if code_el is not None and code_el.text == code:
                val_el = attr.find("attribute")
                if val_el is None:
                    val_el = ET.SubElement(attr, "attribute")
                val_el.text = str(value)
                found = True
                break

        if not found:
            new_attr = ET.SubElement(attr_container, "attribute")
            code_el = ET.SubElement(new_attr, "code")
            code_el.text = code
            val_el = ET.SubElement(new_attr, "attribute")
            val_el.text = str(value)

        return True

    def _ensure_direct_tag(self, parent_elem: ET.Element, tag_name: str, value: str):
        """Helper to ensure a direct tag like <keep_alive_interval> exists with desired value."""
        el = parent_elem.find(tag_name)
        if el is None:
            el = ET.SubElement(parent_elem, tag_name)
        el.text = str(value)

    def _backup_file(self, file_path: Path):
        """Create a safe backup of the original workflow file."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        dest = self.backup_dir / file_path.name
        shutil.copy2(file_path, dest)

    def _print_summary_report(self):
        """Print colored summary statistics."""
        print(f"\n{Colors.GREEN}{Colors.BOLD}============================================================================={Colors.END}")
        print(f"{Colors.BOLD}                    MIGRATION RUN COMPLETED{Colors.END}")
        print(f"{Colors.GREEN}============================================================================={Colors.END}")
        print(f"  • Total Workflow Files Scanned:       {self.summary['scanned_files']}")
        print(f"  • Total Workflow Files Modified:      {Colors.BOLD}{self.summary['modified_files']}{Colors.END}")
        print(f"  • Skipped / Unencrypted Files:        {self.summary['skipped_files']}")
        print(f"  • Database Connections Configured:    {self.summary['total_connections_updated']}")
        print(f"  • Database Steps Configured:          {self.summary['total_db_steps_inspected']}")
        print(f"  • Database Join Steps (Lazy Excluded):{Colors.YELLOW}{self.summary['database_join_skipped_count']}{Colors.END}")
        if self.create_backup and not self.dry_run and self.summary['modified_files'] > 0:
            print(f"  • Backup Folder:                      {self.backup_dir}")
        print(f"{Colors.GREEN}=============================================================================\n{Colors.END}")

    def _export_json_report(self):
        """Write report to JSON for auditing."""
        report_file = self.target_path / f"migration_report_{self.timestamp}.json" if self.target_path.is_dir() else self.target_path.parent / f"migration_report_{self.timestamp}.json"
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(self.summary, f, indent=2)
            logger.info(f"Audit log generated: {report_file}")
        except Exception as e:
            logger.warning(f"Could not write audit report: {e}")

# ----------------------------------------------------------------------
# CLI Entry Point
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="AutomationEdge Workflow DB Connection Migration Utility (IDFC Idle Timeout Fix)"
    )
    parser.add_argument(
        "-p", "--path",
        default=".",
        help="Path to workflow directory or single .psw/.psp file (default: current directory)"
    )
    parser.add_argument(
        "-k", "--keep-alive",
        type=int,
        default=900,
        help="Keep alive interval in seconds (default: 900s / 15 mins for 30m IDLE_TIME)"
    )
    parser.add_argument(
        "--no-lazy-connect",
        action="store_true",
        help="Disable Lazy Connect modification"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate changes without modifying files on disk"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create backup files before modifying"
    )

    args = parser.parse_args()

    migrator = WorkflowMigrator(
        target_path=args.path,
        keep_alive_seconds=args.keep_alive,
        lazy_connect=not args.no_lazy_connect,
        dry_run=args.dry_run,
        create_backup=not args.no_backup
    )

    migrator.run()

if __name__ == "__main__":
    main()
