# CSV Watchdog Monitor

A robust Python script that monitors a directory for new CSV files, validates them, merges them into a master dataset, and archives the processed files. Designed for production use with comprehensive error handling, logging, and safety features.

## Features

- **Automatic CSV Detection**: Monitors a watch directory for new CSV files
- **File Stability Verification**: Uses MD5 checksums to ensure files are completely written
- **Safe Merging**: Uses file locking to prevent concurrent access issues
- **Dynamic Schema Updates**: Automatically handles new columns in incoming CSV files
- **UTF-8 Validation**: Ensures all files are properly encoded
- **Comprehensive Logging**: Rotating logs with configurable levels
- **Dry-Run Mode**: Test operations without making changes
- **Metadata Tracking**: Maintains information about merged datasets
- **Automatic Archiving**: Moves processed files to archive with timestamps
- **Configurable**: JSON-based configuration with sensible defaults

## Installation

### Requirements

```bash
pip install pandas filelock
```

### Dependencies

- Python 3.7+
- pandas
- filelock

## Quick Start

1. **Basic usage** (uses default configuration):
   ```bash
   python csv_watchdog.py
   ```

2. **Test run** (see what would happen without making changes):
   ```bash
   python csv_watchdog.py --dry-run
   ```

3. **With custom configuration**:
   ```bash
   export CSV_MONITOR_CONFIG=my_config.json
   python csv_watchdog.py
   ```

## Configuration

Create a `config.json` file to customize behavior:

```json
{
  "watch_dir": "csv_inbox",
  "archive_dir": "csv_archive", 
  "merged_file": "final_clusters_data.csv",
  "metadata_file": "merged_metadata.json",
  "key_column": "cluster_name",
  "required_columns": ["id", "name"],
  "checksum_wait_seconds": 5,
  "max_file_size_mb": 500,
  "csv_delimiter": ",",
  "csv_encoding": "utf-8",
  "log_level": "INFO",
  "log_to_console": true
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `watch_dir` | "csv_inbox" | Directory to monitor for new CSV files |
| `archive_dir` | "csv_archive" | Directory to store processed files |
| `merged_file` | "final_clusters_data.csv" | Output file containing merged data |
| `metadata_file` | "merged_metadata.json" | Metadata about the merged dataset |
| `key_column` | "cluster_name" | Column used as unique identifier for merging |
| `required_columns` | `[]` | List of columns that must be present in all files |
| `checksum_wait_seconds` | 5 | Time to wait between checksum calculations |
| `max_file_size_mb` | 500 | Maximum file size to process |
| `csv_delimiter` | "," | CSV delimiter character |
| `csv_encoding` | "utf-8" | Character encoding for CSV files |
| `log_level` | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `log_to_console` | false | Whether to output logs to console |
| `log_file` | "csv_watchdog.log" | Log file path |
| `lock_timeout_seconds` | 30 | File lock timeout |

## How It Works

1. **File Discovery**: Scans the watch directory for CSV files
2. **Stability Check**: Calculates MD5 checksums, waits, then recalculates to ensure files are stable
3. **Validation**: Checks UTF-8 encoding, required columns, and data integrity
4. **Merging Logic**: 
   - Loads existing merged file (if exists)
   - Removes rows with matching key column values
   - Adds new data from incoming file
   - Handles schema changes (new columns)
   - Removes obsolete columns when appropriate
5. **Safe Writing**: Uses atomic file operations and locking
6. **Archiving**: Moves processed files to archive with timestamps
7. **Metadata**: Updates information about the merged dataset

## Directory Structure

```
project/
├── csv_watchdog.py          # Main script
├── config.json              # Configuration (optional)
├── csv_inbox/               # Watch directory (created automatically)
├── csv_archive/             # Archive directory (created automatically)
├── final_clusters_data.csv  # Merged output file
├── merged_metadata.json     # Dataset metadata
├── csv_watchdog.log         # Log file
└── final_clusters_data.csv.lock  # Lock file (temporary)
```

## Usage Examples

### Basic Monitoring
Place CSV files in the `csv_inbox` directory and run:
```bash
python csv_watchdog.py
```

### Scheduled Execution
Add to crontab for periodic execution:
```bash
# Run every 5 minutes
*/5 * * * * /usr/bin/python3 /path/to/csv_watchdog.py

# Run every hour
0 * * * * /usr/bin/python3 /path/to/csv_watchdog.py
```

### Custom Configuration
```bash
# Use custom config file
export CSV_MONITOR_CONFIG=/path/to/my_config.json
python csv_watchdog.py

# Dry run with custom config
CSV_MONITOR_CONFIG=test_config.json python csv_watchdog.py --dry-run
```

## File Processing Rules

### Merging Logic
- Files are merged based on the `key_column` (default: "cluster_name")
- Existing rows with matching keys are replaced by new data
- New columns are automatically added to the schema
- Obsolete columns are removed if they're empty for all new records

### File Requirements
- Must be valid CSV format
- Must be UTF-8 encoded
- Must contain the key column
- Must contain any required columns (if specified)
- Must be under the size limit

## Error Handling

The script handles various error conditions gracefully:

- **File corruption**: Skips corrupted files and logs errors
- **Encoding issues**: Validates UTF-8 encoding before processing
- **Missing columns**: Checks for required columns
- **Large files**: Enforces size limits
- **Concurrent access**: Uses file locking to prevent conflicts
- **Unstable files**: Waits for files to finish writing

## Logging

Logs are written to `csv_watchdog.log` by default with rotation:
- Maximum size: 1MB per file
- Keeps 5 backup files
- Configurable log levels
- Optional console output

### Log Levels
- **DEBUG**: Detailed processing information
- **INFO**: Normal operations (default)
- **WARNING**: Non-fatal issues
- **ERROR**: Processing failures

## Monitoring and Maintenance

### Metadata File
The `merged_metadata.json` file contains:
```json
{
  "last_updated": "2025-06-29T10:30:45.123456",
  "row_count": 15420,
  "column_count": 8,
  "columns": ["cluster_name", "id", "name", "value", "timestamp"]
}
```

### Archive Management
Processed files are moved to the archive directory with timestamps:
```
csv_archive/
├── data_batch1.csv.20250629T103045.123
├── data_batch2.csv.20250629T104512.456
└── data_batch3.csv.20250629T105030.789
```

## Troubleshooting

### Common Issues

**Files not being processed:**
- Check file permissions
- Verify UTF-8 encoding
- Ensure files contain required columns
- Check file size limits

**Lock timeout errors:**
- Another instance may be running
- Increase `lock_timeout_seconds`
- Check for stale lock files

**Memory issues with large files:**
- Reduce `max_file_size_mb`
- Process files in smaller batches
- Monitor system memory usage

### Debug Mode
Enable debug logging to see detailed processing information:
```json
{
  "log_level": "DEBUG",
  "log_to_console": true
}
```

## Security Considerations

- Input validation prevents processing of malformed files
- File size limits prevent resource exhaustion
- UTF-8 validation prevents encoding attacks
- File locking prevents race conditions
- Atomic file operations prevent data corruption

## Performance Notes

- Processing time scales with file size and number of columns
- Memory usage is proportional to dataset size
- Checksum calculation adds slight overhead but ensures reliability
- File locking may create brief delays during concurrent access

## License

This script is provided as-is. Modify and distribute as needed for your use case.

## Contributing

When modifying the script:
1. Maintain backward compatibility with existing configurations
2. Add appropriate error handling for new features
3. Update logging for new operations
4. Test with various CSV formats and sizes
5. Update this README for any new configuration options
