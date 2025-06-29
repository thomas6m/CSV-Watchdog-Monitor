# CSV Watchdog Monitor - Code Explanation

This script monitors a folder for new CSV files, ensures they're stable and valid, and merges them into a master dataset. It also:

- Archives processed files
- Cleans obsolete fields  
- Validates UTF-8 encoding
- Supports dry runs
- Outputs a metadata file

## 🔰 Header

```python
#!/usr/bin/env python3
"""
CSV Watchdog Monitor - Enhanced

Monitors a directory for new CSV files, ensures stability,
merges them into a master file, dynamically updates schema,
and archives input. Includes dry-run, metadata output, and UTF-8 validation.

Safe for periodic execution (e.g., cron or scheduler).
"""
```

This declares the script's purpose and ensures it runs using Python 3 via the OS's env. The docstring explains it's designed for production use with cron jobs or schedulers.

## 📦 Imports

```python
import os, sys, json, time, shutil, tempfile, hashlib, logging, argparse
import pandas as pd
from datetime import datetime
from filelock import FileLock
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional, Sequence
from collections.abc import Mapping
```

These are standard and third-party libraries used for:
- **File I/O**: `os`, `shutil`, `tempfile`
- **JSON parsing**: `json`
- **Logging**: `logging`, `RotatingFileHandler`
- **CSV and DataFrame operations**: `pandas`
- **Locking the output file during writing**: `FileLock`
- **Type hints**: `typing`, `collections.abc`
- **File integrity**: `hashlib` for checksums
- **Time operations**: `time`, `datetime`

## ❗ Custom Exceptions

```python
class CSVMonitorError(Exception): pass
class ConfigurationError(CSVMonitorError): pass
class FileProcessingError(CSVMonitorError): pass
class DataValidationError(CSVMonitorError): pass
```

These define custom exception types for clear, categorized error handling:
- **CSVMonitorError**: Base exception for all script errors
- **ConfigurationError**: Invalid configuration settings
- **FileProcessingError**: Problems reading or processing files
- **DataValidationError**: Data doesn't meet requirements

## ⚙️ Configuration Loading

```python
def load_config() -> Mapping[str, Any]:
    default_config = {
        "watch_dir": "csv_inbox",
        "archive_dir": "csv_archive",
        "merged_file": "final_clusters_data.csv",
        "key_column": "cluster_name",
        ...
    }
```

This function:
- **Loads settings** from `config.json`
- **Applies environment override** via `CSV_MONITOR_CONFIG`
- **Fills in defaults** for missing values
- **Validates the result** before returning

✅ **Key Configs:**
- `watch_dir`: folder to monitor for new CSV files
- `merged_file`: the main merged CSV output file
- `key_column`: the unique ID column (e.g., "cluster_name")
- `required_columns`: columns that must exist in all files
- `log_level`, `log_max_bytes`: logging configuration
- `checksum_wait_seconds`: stability check timing
- `max_file_size_mb`: prevent processing huge files

## ✅ Configuration Validation

```python
def _validate_config(config: Dict[str, Any]) -> None:
    if not config["key_column"]:
        raise ConfigurationError("Missing key_column")
    if not all(ext.startswith('.') for ext in config["supported_extensions"]):
        raise ConfigurationError("Extensions must start with '.'")
```

Ensures:
- **Required values are present** (like `key_column`)
- **File extensions start with `.`** (proper format)
- **Config structure is valid** before proceeding

## 📌 Assign Config Values

```python
cfg = load_config()
WATCH_DIR = cfg["watch_dir"]
ARCHIVE_DIR = cfg["archive_dir"]
MERGED_FILE = cfg["merged_file"]
KEY_COLUMN = cfg["key_column"]
...
```

Loads values from the config dictionary into module-level constants for easy access throughout the script.

## 📝 Logging Setup

```python
handlers = [RotatingFileHandler(cfg["log_file"], 
                               maxBytes=cfg["log_max_bytes"], 
                               backupCount=cfg["log_backup_count"])]
if cfg.get("log_to_console"):
    handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=getattr(logging, cfg.get("log_level", "INFO").upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=handlers
)
```

This sets up **rotating file logs** that prevent log file bloat:
- **Rotates logs** when they reach max size
- **Keeps backup copies** (configurable count)
- **Optional console output** for debugging
- **Configurable log levels** (DEBUG, INFO, WARNING, ERROR)

## 📁 Ensure Directories Exist

```python
os.makedirs(WATCH_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)
```

Creates the watch and archive folders if they don't exist. `exist_ok=True` prevents errors if folders already exist.

## 🧮 Checksum Calculation

```python
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
```

Generates an **MD5 hash** of the file content to:
- **Determine file stability** over time
- **Check for file size limits** before processing
- **Read in chunks** to handle large files efficiently
- **Handle errors gracefully** and return None on failure

## 📂 Stable File Detection

```python
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
```

Detects files whose **checksum doesn't change** after a short wait:
- **First pass**: Calculate checksums for all CSV files
- **Wait period**: Allow any writing operations to complete
- **Second pass**: Recalculate checksums
- **Stable files**: Only process files with matching checksums
- **Prevents processing** of files still being written

## 🧪 UTF-8 Validation

```python
def validate_utf8(filepath: str) -> None:
    try:
        with open(filepath, 'rb') as f:
            f.read().decode(CSV_ENCODING)
    except Exception:
        raise FileProcessingError(f"File is not valid {CSV_ENCODING}: {filepath}")
```

Ensures the file can be **decoded using the expected encoding** (default UTF-8):
- **Reads entire file** in binary mode
- **Attempts to decode** with specified encoding
- **Raises error** if decoding fails
- **Prevents processing** of corrupted or wrong-encoding files

## 📋 DataFrame Validation

```python
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
```

Checks that:
- **DataFrame is not empty** (has data)
- **Key column exists** (for merging)
- **Required columns exist** (configurable requirements)
- **Key column has no null values** (prevents merge issues)

## 🔁 The Main Processor Class

```python
class CSVWatchdogMonitor:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
```

Wraps the core logic for processing files:
- **`dry_run`**: Skips writing to disk or archiving (for testing)
- **Encapsulates behavior** in a class for better organization

### 🔄 process_all()

```python
def process_all(self):
    for fpath in get_stable_files():
        try:
            self.process_file(fpath)
        except Exception as e:
            logging.error("Error: %s", e)
```

Processes **all stable files** by:
- **Getting stable file list** from the watch directory
- **Processing each file** individually
- **Continuing on errors** (doesn't stop entire batch)
- **Logging errors** for troubleshooting

## 🔄 process_file() - The Heart of the System

```python
def process_file(self, filepath: str):
    logging.info("Processing: %s", filepath)
    validate_utf8(filepath)
    
    try:
        new_df = pd.read_csv(filepath, delimiter=CSV_DELIMITER, encoding=CSV_ENCODING)
    except Exception as e:
        raise FileProcessingError(f"CSV load failed: {e}")
    
    validate_dataframe(new_df, filepath)
```

The **core processing logic**:

### 🔒 File Locking

```python
with FileLock(LOCK_FILE, timeout=LOCK_TIMEOUT_SECONDS):
```

**Prevents concurrent access** to the merged file:
- **Acquires exclusive lock** before writing
- **Prevents data corruption** from multiple processes
- **Times out** if lock can't be acquired
- **Automatically releases** lock when done

### 📊 Data Merging Logic

```python
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
```

**Sophisticated merging process**:
1. **Load existing data** (or create empty DataFrame)
2. **Identify new keys** from incoming file
3. **Align columns** between old and new data
4. **Remove existing rows** with matching keys (updates)
5. **Concatenate** old and new data
6. **Handle schema evolution** automatically

### 🧹 Obsolete Column Removal

```python
for col in set(base_df.columns) - set(new_df.columns) - {KEY_COLUMN}:
    if merged[merged[KEY_COLUMN].isin(new_keys)][col].isna().all():
        merged.drop(columns=col, inplace=True)
        logging.info("Dropped obsolete column: %s", col)
```

**Cleans up obsolete columns**:
- **Identifies columns** that exist in old data but not new data
- **Checks if obsolete** for all updated records
- **Removes columns** that are completely NaN for new data
- **Preserves columns** that still have data in updated records

### 💾 Atomic File Writing

```python
if not self.dry_run:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", dir=".").name
    merged.to_csv(tmp, index=False, encoding=CSV_ENCODING)
    os.replace(tmp, MERGED_FILE)
```

**Ensures data integrity**:
- **Writes to temporary file** first
- **Atomically replaces** original file
- **Prevents corruption** if process is interrupted
- **Skips in dry-run mode** for testing

## 📦 _archive_file()

```python
def _archive_file(self, src: str, df: pd.DataFrame):
    ts = datetime.now().strftime("%Y%m%dT%H%M%S.%f")[:-3]
    dst = os.path.join(ARCHIVE_DIR, f"{os.path.basename(src)}.{ts}")
    shutil.move(src, dst)
    
    clusters = df[KEY_COLUMN].unique()
    display = ", ".join(sorted(map(str, clusters[:MAX_CLUSTERS_IN_LOG])))
    if len(clusters) > MAX_CLUSTERS_IN_LOG:
        display += f"... ({len(clusters)} total)"
    logging.info("Archived: %s → %s | Clusters: %s", src, dst, display)
```

Archives the processed file:
- **Adds timestamp suffix** to prevent name conflicts
- **Moves file** to archive directory
- **Logs affected clusters** (with limits for readability)
- **Preserves original filename** for traceability

## 📄 _save_metadata()

```python
def _save_metadata(self, df: pd.DataFrame):
    meta = {
        "last_updated": datetime.now().isoformat(),
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns)
    }
    with open(METADATA_FILE, "w") as f:
        json.dump(meta, f, indent=2)
```

Outputs a **simple metadata JSON**:
```json
{
  "last_updated": "2025-06-29T10:30:45.123456",
  "row_count": 1234,
  "column_count": 8,
  "columns": ["cluster_name", "id", "name", "value"]
}
```

**Useful for monitoring**:
- **Track when data was last updated**
- **Monitor dataset size growth**
- **Verify expected columns are present**
- **External systems can check metadata**

## 🚀 Main Entrypoint

```python
def main():
    parser = argparse.ArgumentParser(description="CSV Watchdog Monitor")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Simulate only (no writing or archiving)")
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
```

**Command-line interface**:
- **Parses `--dry-run`** from CLI arguments
- **Creates monitor instance** with appropriate settings
- **Runs the processing** with comprehensive error handling
- **Returns appropriate exit codes** (0 = success, 1 = error)
- **Logs start/completion** for monitoring

## ✅ Execution Block

```python
if __name__ == "__main__":
    sys.exit(main())
```

Ensures this **only runs if the script is executed directly**:
- **Prevents execution** when imported as module
- **Exits with proper code** for shell scripts
- **Standard Python pattern** for executable scripts

## 🧪 Example Usage

```bash
# Basic execution
python csv_watchdog.py

# Dry run (test without changes)
python csv_watchdog.py --dry-run

# With custom configuration
export CSV_MONITOR_CONFIG=my_config.json
python csv_watchdog.py

# Scheduled execution (crontab)
*/5 * * * * /usr/bin/python3 /path/to/csv_watchdog.py
```

## 🔧 Key Features Summary

- **🔄 Automatic Processing**: Monitors directory continuously
- **⚡ File Stability**: Ensures files are completely written
- **🔒 Thread Safety**: File locking prevents corruption
- **📊 Smart Merging**: Updates existing records, adds new ones
- **🧹 Schema Evolution**: Handles new columns automatically
- **📦 Archiving**: Preserves processed files with timestamps
- **🧪 Testing**: Dry-run mode for safe testing
- **📝 Logging**: Comprehensive logging with rotation
- **⚙️ Configurable**: JSON-based configuration system
- **🛡️ Robust**: Extensive error handling and validation
