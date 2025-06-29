# CSV Watchdog Monitor - Runbook

## Overview
This runbook provides step-by-step instructions for setting up and running the CSV Watchdog Monitor, a Python-based tool for monitoring CSV files and processing them automatically.

## Prerequisites
- Python 3.6 or higher
- Terminal/Command line access
- Write permissions to the target directories

## Setup Instructions

### 1. Prepare Python Virtual Environment
Create a dedicated virtual environment for the CSV Watchdog Monitor:

```bash
mkdir -p CSV_Watchdog_Monitor/python-env
python3 -m venv CSV_Watchdog_Monitor/python-env
source CSV_Watchdog_Monitor/python-env/bin/activate
```

### 2. Create requirements.txt
Create a file `CSV_Watchdog_Monitor/requirements.txt` with the following dependencies:

```txt
pandas>=1.0.0
filelock>=3.0.0
```

> **Note:** This configuration uses only pandas and filelock dependencies. Previous versions included polars, psutil, and PyYAML, but these are no longer required.

### 3. Install Dependencies
Install the required Python packages:

```bash
pip install --upgrade pip
pip install -r CSV_Watchdog_Monitor/requirements.txt
pip freeze > CSV_Watchdog_Monitor/requirements.lock.txt
```

### 4. Create Configuration File
Create `CSV_Watchdog_Monitor/config.json` with the following configuration:

```json
{
  "watch_dir": "csv_inbox",
  "archive_dir": "csv_archive",
  "merged_file": "final_clusters_data.csv",
  "metadata_file": "merged_metadata.json",
  "key_column": "cluster_name",
  "required_columns": ["cluster_name", "data_column1", "data_column2"],
  "checksum_wait_seconds": 5,
  "chunk_size": 4096,
  "max_file_size_mb": 500,
  "supported_extensions": [".csv"],
  "log_file": "csv_watchdog.log",
  "log_level": "INFO",
  "log_to_console": true,
  "log_max_bytes": 1048576,
  "log_backup_count": 5,
  "lock_timeout_seconds": 30,
  "max_clusters_in_log": 20,
  "csv_delimiter": ",",
  "csv_encoding": "utf-8"
}
```

### 5. Prepare Directory Structure
Create the necessary directories for file monitoring and archiving:

```bash
mkdir -p csv_inbox csv_archive
```

### 6. Place the Script
Create `CSV_Watchdog_Monitor/csv_watchdog_monitor.py` with the full updated code (this should be provided separately).

## Running the Monitor

### Basic Execution
To run the monitor in normal mode:

```bash
python3 CSV_Watchdog_Monitor/csv_watchdog_monitor.py
```

### Dry Run Mode
To simulate processing without actually writing files or archiving (useful for testing):

```bash
python3 CSV_Watchdog_Monitor/csv_watchdog_monitor.py --dry-run
```

### Using Custom Configuration (Optional)
If you need to use a different configuration file location, set the environment variable before running:

```bash
export CSV_MONITOR_CONFIG=/path/to/your/custom_config.json
python3 CSV_Watchdog_Monitor/csv_watchdog_monitor.py
```

## Configuration Parameters

| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `watch_dir` | Directory to monitor for new CSV files | `"csv_inbox"` |
| `archive_dir` | Directory to move processed files | `"csv_archive"` |
| `merged_file` | Output file for merged data | `"final_clusters_data.csv"` |
| `metadata_file` | JSON file for processing metadata | `"merged_metadata.json"` |
| `key_column` | Primary key column for data merging | `"cluster_name"` |
| `required_columns` | List of required columns in CSV files | `["cluster_name", "data_column1", "data_column2"]` |
| `checksum_wait_seconds` | Wait time for file stability check | `5` |
| `max_file_size_mb` | Maximum allowed file size in MB | `500` |
| `log_level` | Logging level (DEBUG, INFO, WARNING, ERROR) | `"INFO"` |
| `log_to_console` | Enable console logging | `true` |
| `lock_timeout_seconds` | File lock timeout in seconds | `30` |

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure you have write permissions to the target directories
2. **Module Not Found**: Verify the virtual environment is activated and dependencies are installed
3. **Config File Not Found**: Check the configuration file path and ensure it exists
4. **CSV Processing Errors**: Verify CSV files contain the required columns as specified in the configuration

### Log Files
Monitor the log file `csv_watchdog.log` for detailed information about processing status and any errors encountered.

## Maintenance

### Updating Dependencies
To update the dependencies:

```bash
pip install --upgrade -r CSV_Watchdog_Monitor/requirements.txt
pip freeze > CSV_Watchdog_Monitor/requirements.lock.txt
```

### Log Rotation
The system automatically rotates log files when they exceed the configured size limit (`log_max_bytes`). Old log files are kept according to the `log_backup_count` setting.

## Security Considerations

- Ensure the monitor runs with appropriate user permissions
- Regularly monitor log files for suspicious activity
- Keep the Python environment and dependencies updated
- Restrict access to configuration files containing sensitive paths