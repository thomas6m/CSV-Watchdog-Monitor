# CSV Watchdog Monitor

A robust Python application that monitors directories for new CSV files, validates their stability, and dynamically merges cluster data into a master file. Designed for safe periodic execution via cron jobs or task schedulers.

## Features

- **File Stability Verification**: Uses MD5 checksums to ensure files are completely written before processing
- **Dynamic Schema Management**: Automatically adds new columns and removes obsolete ones
- **Atomic Operations**: Safe file handling with locks and temporary files
- **Backup System**: Automatic backups with configurable retention
- **Encoding Detection**: Automatic detection and handling of various file encodings
- **Progress Reporting**: Optional progress display for batch operations
- **Email Notifications**: Configurable email alerts for errors and completion
- **Dry Run Mode**: Test processing without making changes
- **Comprehensive Logging**: Detailed logging with configurable levels

## Installation

### Requirements

- Python 3.7+
- Required packages:

```bash
pip install pandas filelock chardet
```

### Quick Start

1. Clone or download the script
2. Create the required directories (or let the script create them):
   ```bash
   mkdir csv_inbox csv_archive csv_backups
   ```
3. Run the monitor:
   ```bash
   python csv_watchdog.py
   ```

## Usage

### Command Line Options

```bash
python csv_watchdog.py [OPTIONS]

Options:
  --dry-run           Process files but don't write or archive
  --log-to-console    Also log to console (in addition to file)
  --sort-output       Sort output by cluster key column
  --config-path FILE  Path to config file (default: config.json)
  --backup-count N    Number of backup files to keep
  --progress          Show progress for file processing
  -h, --help          Show help message
```

### Basic Examples

```bash
# Standard operation
python csv_watchdog.py

# Dry run to test without changes
python csv_watchdog.py --dry-run --log-to-console

# Show progress and keep 10 backups
python csv_watchdog.py --progress --backup-count 10

# Use custom configuration
python csv_watchdog.py --config-path production.json
```

### Scheduled Execution

**Linux/macOS (crontab):**
```bash
# Run every 15 minutes
*/15 * * * * /usr/bin/python3 /path/to/csv_watchdog.py

# Run hourly with logging
0 * * * * /usr/bin/python3 /path/to/csv_watchdog.py --log-to-console >> /var/log/csv_watchdog_cron.log 2>&1
```

**Windows (Task Scheduler):**
- Create a new task
- Set trigger to run every 15 minutes
- Set action to run: `python.exe C:\path\to\csv_watchdog.py`

## Configuration

The application uses a JSON configuration file (`config.json` by default). All settings have sensible defaults.

### Basic Configuration

```json
{
  "watch_dir": "csv_inbox",
  "archive_dir": "csv_archive",
  "backup_dir": "csv_backups",
  "merged_file": "final_clusters_data.csv",
  "key_column": "cluster_name",
  "log_file": "csv_watchdog.log",
  "log_level": "INFO"
}
```

### Complete Configuration Example

```json
{
  "watch_dir": "csv_inbox",
  "archive_dir": "csv_archive",
  "backup_dir": "csv_backups",
  "merged_file": "final_clusters_data.csv",
  "key_column": "cluster_name",
  "log_file": "csv_watchdog.log",
  "checksum_wait_seconds": 5,
  "chunk_size": 4096,
  "supported_extensions": [".csv"],
  "max_file_size_mb": 500,
  "required_columns": ["cluster_name", "status"],
  "lock_timeout_seconds": 30,
  "max_clusters_in_log": 20,
  "log_level": "INFO",
  "log_to_console": false,
  "sort_output": false,
  "dry_run": false,
  "backup_count": 5,
  "show_progress": false,
  "auto_detect_encoding": true,
  "csv_delimiter": ",",
  "notification": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "monitoring@company.com",
    "password": "your-app-password",
    "from_email": "monitoring@company.com",
    "to_emails": ["admin@company.com", "devops@company.com"],
    "notify_on_error": true,
    "notify_on_success": false
  }
}
```

## How It Works

### Processing Flow

1. **File Discovery**: Scans the watch directory for supported file types
2. **Stability Check**: Calculates MD5 checksums, waits, then rechecks to ensure files are stable
3. **Validation**: Validates file structure and required columns
4. **Backup**: Creates timestamped backup of existing master file
5. **Merging**: Intelligently merges new data with existing data:
   - Replaces rows with matching key values
   - Adds new columns from incoming data
   - Removes obsolete columns (when safe)
6. **Atomic Save**: Uses temporary files and atomic moves for safe updates
7. **Archiving**: Moves processed files to archive directory with timestamps

### Data Merging Logic

- **Key-based Updates**: Rows with matching key column values are replaced entirely
- **Column Addition**: New columns from incoming files are automatically added
- **Column Removal**: Columns that exist in master but not in new data are removed IF they contain only null values for the affected clusters
- **Schema Evolution**: The master file schema evolves dynamically while preserving data integrity

## Directory Structure

```
project/
├── csv_watchdog.py          # Main script
├── config.json              # Configuration file
├── csv_watchdog.log         # Log file
├── final_clusters_data.csv  # Master merged file
├── csv_inbox/               # Drop new CSV files here
├── csv_archive/             # Processed files stored here
└── csv_backups/             # Automatic backups
```

## Logging

The application provides comprehensive logging with configurable levels:

- **DEBUG**: Detailed operational information
- **INFO**: General operational messages (default)
- **WARNING**: Important notices (file instability, etc.)
- **ERROR**: Error conditions that don't stop execution
- **CRITICAL**: Serious errors that may stop execution

Log files are UTF-8 encoded and include timestamps, log levels, and detailed messages.

## Error Handling

The application handles various error conditions gracefully:

- **File Access Errors**: Logs errors and continues with other files
- **Data Validation Errors**: Skips invalid files but continues processing
- **Network Issues**: For email notifications, logs errors but doesn't fail
- **Disk Space**: Monitors file sizes and prevents processing oversized files
- **Encoding Issues**: Automatic fallback encoding handling

## Email Notifications

Configure email notifications for:
- Processing errors
- Successful completions
- Critical failures

Supports SMTP with STARTTLS (Gmail, Outlook, etc.).

### Gmail Configuration Example

1. Enable 2-factor authentication in Gmail
2. Generate an app-specific password
3. Use these settings:
   ```json
   "notification": {
     "enabled": true,
     "smtp_server": "smtp.gmail.com",
     "smtp_port": 587,
     "username": "your-email@gmail.com",
     "password": "your-16-char-app-password",
     "from_email": "your-email@gmail.com",
     "to_emails": ["recipient@company.com"]
   }
   ```

## Performance Considerations

- **Memory Usage**: Loads entire CSV files into memory; monitor usage with large files
- **File Locking**: Uses file locks to prevent concurrent access issues
- **Checksum Calculation**: May be slow for very large files
- **Backup Storage**: Monitor backup directory size with high-frequency processing

## Troubleshooting

### Common Issues

**Files not being processed:**
- Check file permissions in watch directory
- Verify file extensions match `supported_extensions`
- Check log file for stability warnings

**Memory errors with large files:**
- Reduce `max_file_size_mb` setting
- Process files in smaller batches
- Monitor system memory usage

**Email notifications not working:**
- Verify SMTP settings
- Check firewall/network restrictions
- Use app-specific passwords for Gmail/Outlook
- Test SMTP connection separately

**Lock timeout errors:**
- Increase `lock_timeout_seconds`
- Check for competing processes
- Verify filesystem supports file locking

### Debug Mode

Run with debug logging for detailed troubleshooting:

```json
{
  "log_level": "DEBUG",
  "log_to_console": true
}
```

Or via command line:
```bash
python csv_watchdog.py --log-to-console
```

## Security Considerations

- **File Permissions**: Ensure appropriate read/write permissions on directories
- **Email Credentials**: Store SMTP passwords securely (consider environment variables)
- **Log Files**: May contain sensitive data; secure appropriately
- **Network Access**: SMTP notifications require outbound network access

## License

This software is provided as-is for educational and commercial use. Modify and distribute freely.

## Contributing

When contributing:
1. Maintain backward compatibility
2. Add comprehensive tests for new features
3. Update documentation
4. Follow existing code style
5. Add logging for new operations

## Support

For issues and questions:
1. Check the log files first
2. Review configuration settings
3. Test with `--dry-run` and `--log-to-console`
4. Verify file permissions and directory structure
