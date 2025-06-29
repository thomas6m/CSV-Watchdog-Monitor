#!/usr/bin/env python3
"""
CSV Watchdog Monitor - Enhanced

Monitors a directory for new CSV files, ensures stability,
merges them into a master file, dynamically updates schema,
and archives input. Includes dry-run, metadata output, and UTF-8 validation.

Safe for periodic execution (e.g., cron or scheduler).
"""

import os
import sys
import json
import time
import shutil
import tempfile
import hashlib
import logging
import argparse
import pandas as pd
from datetime import datetime
from filelock import FileLock
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional, Sequence
from collections.abc import Mapping


# === Exception Classes ===
class CSVMonitorError(Exception): pass
class ConfigurationError(CSVMonitorError): pass
class FileProcessingError(CSVMonitorError): pass
class DataValidationError(CSVMonitorError): pass


# === Load Configuration ===
def load_config() -> Mapping[str, Any]:
    default_config = {
        "watch_dir": "csv_inbox",
        "archive_dir": "csv_archive",
        "merged_file": "final_clusters_data.csv",
        "metadata_file": "merged_metadata.json",
        "key_column": "cluster_name",
        "required_columns": [],
        "checksum_wait_seconds": 5,
        "chunk_size": 4096,
        "max_file_size_mb": 500,
        "supported_extensions": [".csv"],
        "log_file": "csv_watchdog.log",
        "log_level": "INFO",
        "log_to_console": False,
        "log_max_bytes": 1048576,
        "log_backup_count": 5,
        "lock_timeout_seconds": 30,
        "max_clusters_in_log": 20,
        "csv_delimiter": ",",
        "csv_encoding": "utf-8"
    }

    config_path = os.getenv("CSV_MONITOR_CONFIG", "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            user_config = json.load(f)
        config = {**default_config, **user_config}
    else:
        config = default_config

    _validate_config(config)
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    if not config["key_column"]:
        raise ConfigurationError("Missing key_column")
    if not all(ext.startswith('.') for ext in config["supported_extensions"]):
        raise ConfigurationError("Extensions must start with '.'")


cfg = load_config()

WATCH_DIR = cfg["watch_dir"]
ARCHIVE_DIR = cfg["archive_dir"]
MERGED_FILE = cfg["merged_file"]
METADATA_FILE = cfg["metadata_file"]
LOCK_FILE = MERGED_FILE + ".lock"
KEY_COLUMN = cfg["key_column"]
REQUIRED_COLUMNS = cfg["required_columns"]
CSV_DELIMITER = cfg["csv_delimiter"]
CSV_ENCODING = cfg["csv_encoding"]
MAX_FILE_SIZE_MB = cfg["max_file_size_mb"]
CHUNK_SIZE = cfg["chunk_size"]
SUPPORTED_EXTENSIONS = cfg["supported_extensions"]
CHECKSUM_WAIT_SECONDS = cfg["checksum_wait_seconds"]
LOCK_TIMEOUT_SECONDS = cfg["lock_timeout_seconds"]
MAX_CLUSTERS_IN_LOG = cfg["max_clusters_in_log"]

# === Logging Setup ===
handlers = [RotatingFileHandler(cfg["log_file"], maxBytes=cfg["log_max_bytes"], backupCount=cfg["log_backup_count"])]
if cfg.get("log_to_console"):
    handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=getattr(logging, cfg.get("log_level", "INFO").upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=handlers
)

os.makedirs(WATCH_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)


# === Utility Functions ===
def calculate_md5(filepath: str) -> Optional[str]:
    try:
        if os.path.getsize(filepath) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise FileProcessingError(f"File too large: {filepath}")
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logging.error("Checksum error: %s", e)
        return None


def get_stable_files() -> Sequence[str]:
    logging.info("Scanning for stable CSVs...")
    files = {
        f: calculate_md5(os.path.join(WATCH_DIR, f))
        for f in os.listdir(WATCH_DIR)
        if any(f.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)
    }

    time.sleep(CHECKSUM_WAIT_SECONDS)

    stable = []
    for fname, cksum in files.items():
        path = os.path.join(WATCH_DIR, fname)
        if cksum and cksum == calculate_md5(path):
            stable.append(path)
        else:
            logging.warning("Unstable or unreadable: %s", fname)

    return stable


def validate_utf8(filepath: str) -> None:
    try:
        with open(filepath, 'rb') as f:
            f.read().decode(CSV_ENCODING)
    except Exception:
        raise FileProcessingError(f"File is not valid {CSV_ENCODING}: {filepath}")


def validate_dataframe(df: pd.DataFrame, path: str) -> None:
    if df.empty:
        raise DataValidationError(f"Empty: {path}")
    if KEY_COLUMN not in df.columns:
        raise DataValidationError(f"Missing key: {KEY_COLUMN}")
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise DataValidationError(f"Missing required cols in {path}: {missing}")
    if df[KEY_COLUMN].isna().any():
        raise DataValidationError(f"Null key values in {path}")


# === Main Monitor Class ===
class CSVWatchdogMonitor:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

    def process_all(self):
        for fpath in get_stable_files():
            try:
                self.process_file(fpath)
            except Exception as e:
                logging.error("Error: %s", e)

    def process_file(self, filepath: str):
        logging.info("Processing: %s", filepath)
        validate_utf8(filepath)
        try:
            new_df = pd.read_csv(filepath, delimiter=CSV_DELIMITER, encoding=CSV_ENCODING)
        except Exception as e:
            raise FileProcessingError(f"CSV load failed: {e}")
        validate_dataframe(new_df, filepath)

        with FileLock(LOCK_FILE, timeout=LOCK_TIMEOUT_SECONDS):
            if os.path.exists(MERGED_FILE):
                try:
                    base_df = pd.read_csv(MERGED_FILE, delimiter=CSV_DELIMITER, encoding=CSV_ENCODING)
                except Exception:
                    base_df = pd.DataFrame(columns=new_df.columns)
            else:
                base_df = pd.DataFrame(columns=new_df.columns)

            new_keys = new_df[KEY_COLUMN].unique()
            all_cols = sorted(set(base_df.columns).union(set(new_df.columns)))
            base_df = base_df.reindex(columns=all_cols)
            new_df = new_df.reindex(columns=all_cols)

            base_df = base_df[~base_df[KEY_COLUMN].isin(new_keys)]
            merged = pd.concat([base_df, new_df], ignore_index=True)

            for col in set(base_df.columns) - set(new_df.columns) - {KEY_COLUMN}:
                if merged[merged[KEY_COLUMN].isin(new_keys)][col].isna().all():
                    merged.drop(columns=col, inplace=True)
                    logging.info("Dropped obsolete column: %s", col)

            if not self.dry_run:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", dir=".").name
                merged.to_csv(tmp, index=False, encoding=CSV_ENCODING)
                os.replace(tmp, MERGED_FILE)

                self._save_metadata(merged)
                self._archive_file(filepath, new_df)
            else:
                logging.info("Dry run: skipping file save and archive.")

    def _archive_file(self, src: str, df: pd.DataFrame):
        ts = datetime.now().strftime("%Y%m%dT%H%M%S.%f")[:-3]
        dst = os.path.join(ARCHIVE_DIR, f"{os.path.basename(src)}.{ts}")
        shutil.move(src, dst)
        clusters = df[KEY_COLUMN].unique()
        display = ", ".join(sorted(map(str, clusters[:MAX_CLUSTERS_IN_LOG])))
        if len(clusters) > MAX_CLUSTERS_IN_LOG:
            display += f"... ({len(clusters)} total)"
        logging.info("Archived: %s → %s | Clusters: %s", src, dst, display)

    def _save_metadata(self, df: pd.DataFrame):
        meta = {
            "last_updated": datetime.now().isoformat(),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns)
        }
        with open(METADATA_FILE, "w") as f:
            json.dump(meta, f, indent=2)


# === Main Entrypoint ===
def main():
    parser = argparse.ArgumentParser(description="CSV Watchdog Monitor")
    parser.add_argument("--dry-run", action="store_true", help="Simulate only (no writing or archiving)")
    args = parser.parse_args()

    logging.info("=== Monitor Start ===")
    monitor = CSVWatchdogMonitor(dry_run=args.dry_run)
    try:
        monitor.process_all()
    except Exception as e:
        logging.exception("Fatal error: %s", e)
        return 1
    logging.info("=== Monitor Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
