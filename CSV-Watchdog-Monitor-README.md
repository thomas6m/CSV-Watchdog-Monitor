# CSV Watchdog Monitor - Configuration Documentation

This document provides comprehensive documentation for all configuration options available in the CSV Watchdog Monitor.

## Configuration File Format

The configuration file uses JSON format and should be saved as `config.json` (or specify a custom path with `--config-path`).

## Configuration Sections

### Core Settings

#### Directory Configuration
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `watch_dir` | string | `"csv_inbox"` | Directory to monitor for new CSV files |
| `archive_dir` | string | `"csv_archive"` | Directory where processed files are moved |
| `backup_dir` | string | `"csv_backups"` | Directory for automatic backups of master file |

**Example:**
```json
{
  "watch_dir": "/data/incoming/csv",
  "archive_dir": "/data/processed/csv",
  "backup_dir": "/data/backups/csv"
}
```

#### File Processing Settings
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `merged_file` | string | `"final_clusters_data.csv"` | Path to the master merged CSV file |
| `key_column` | string | `"cluster_name"` | Column name used as primary key for merging |
| `supported_extensions` | array | `[".csv"]` | List of file extensions to process |
| `max_file_size_mb` | number | `500` | Maximum file size in MB to process |
| `required_columns` | array | `[]` | List of columns that must exist in input files |

**Example:**
```json
{
  "merged_file": "master_data.csv",
  "key_column": "id",
  "supported_extensions": [".csv", ".tsv"],
  "max_file_size_mb": 1000,
  "required_columns": ["id", "name", "status"]
}
```

### Performance & Reliability Settings

#### File Stability & Processing
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `checksum_wait_seconds` | number | `5` | Seconds to wait between checksum calculations |
| `chunk_size` | number | `4096` | Bytes to read at once for checksum calculation |
| `lock_timeout_seconds` | number | `30` | Maximum seconds to wait for file lock |

**Example:**
```json
{
  "checksum_wait_seconds": 10,
  "chunk_size": 8192,
  "lock_timeout_seconds": 60
}
```

**Notes:**
- `checksum_wait_seconds`: Increase for slower filesystems or network drives
- `chunk_size`: Larger values use more memory but may be faster for large files
- `lock_timeout_seconds`: Increase if you have slow disk I/O or competing processes

### CSV Processing Options

#### Data Handling
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `auto_detect_encoding` | boolean | `true` | Automatically detect file encoding |
| `csv_delimiter` | string | `","` | CSV delimiter character |
| `sort_output` | boolean | `false` | Sort final output by key column |

**Example:**
```json
{
  "auto_detect_encoding": true,
  "csv_delimiter": ";",
  "sort_output": true
}
```

**Encoding Detection:**
- When `true`: Uses `chardet` library to detect encoding
- When `false`: Uses UTF-8 encoding
- Fallback to UTF-8 if detection confidence is low

**Common Delimiters:**
- `","` - Comma (standard CSV)
- `";"` - Semicolon (European CSV)
- `"\t"` - Tab (TSV files)
- `"|"` - Pipe delimiter

### Backup Management

#### Backup Settings
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `backup_count` | number | `5` | Number of backup files to retain |

**Example:**
```json
{
  "backup_count": 10
}
```

**Backup Behavior:**
- Creates timestamped backups before modifying master file
- Format: `filename_YYYYMMDD_HHMMSS.csv`
- Automatically removes old backups beyond the specified count
- Set to `0` to disable backup cleanup (keep all backups)

### Logging Configuration

#### Log Settings
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `log_file` | string | `"csv_watchdog.log"` | Path to log file |
| `log_level` | string | `"INFO"` | Logging level |
| `log_to_console` | boolean | `false` | Also output logs to console |
| `max_clusters_in_log` | number | `20` | Maximum cluster names to log per file |

**Example:**
```json
{
  "log_file": "/var/log/csv_monitor.log",
  "log_level": "DEBUG",
  "log_to_console": true,
  "max_clusters_in_log": 50
}
```

**Log Levels (in order of verbosity):**
- `"DEBUG"` - Detailed debugging information
- `"INFO"` - General informational messages
- `"WARNING"` - Warning messages
- `"ERROR"` - Error messages
- `"CRITICAL"` - Critical error messages

### Operational Modes

#### Runtime Behavior
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `dry_run` | boolean | `false` | Process files but don't write changes |
| `show_progress` | boolean | `false` | Display progress information |

**Example:**
```json
{
  "dry_run": true,
  "show_progress": true
}
```

### Email Notifications

#### Notification Configuration
The notification system supports email alerts for processing events.

**Main Settings:**
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `notification.enabled` | boolean | `false` | Enable email notifications |
| `notification.notify_on_error` | boolean | `true` | Send emails for errors |
| `notification.notify_on_success` | boolean | `false` | Send emails for successful completion |

**SMTP Settings:**
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `notification.smtp_server` | string | `""` | SMTP server hostname |
| `notification.smtp_port` | number | `587` | SMTP server port |
| `notification.username` | string | `""` | SMTP authentication username |
| `notification.password` | string | `""` | SMTP authentication password |

**Email Settings:**
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `notification.from_email` | string | `""` | Sender email address |
| `notification.to_emails` | array | `[]` | List of recipient email addresses |

**Complete Notification Example:**
```json
{
  "notification": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "monitoring@company.com",
    "password": "your-app-password",
    "from_email": "monitoring@company.com",
    "to_emails": [
      "admin@company.com",
      "devops@company.com"
    ],
    "notify_on_error": true,
    "notify_on_success": false
  }
}
```

### Provider-Specific SMTP Settings

#### Gmail Configuration
```json
{
  "notification": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-16-character-app-password"
  }
}
```

**Gmail Setup:**
1. Enable 2-factor authentication
2. Generate an app-specific password
3. Use the app password, not your regular password

#### Outlook/Hotmail Configuration
```json
{
  "notification": {
    "smtp_server": "smtp-mail.outlook.com",
    "smtp_port": 587,
    "username": "your-email@outlook.com",
    "password": "your-password"
  }
}
```

#### Yahoo Mail Configuration
```json
{
  "notification": {
    "smtp_server": "smtp.mail.yahoo.com",
    "smtp_port": 587,
    "username": "your-email@yahoo.com",
    "password": "your-app-password"
  }
}
```

#### Corporate Exchange Server
```json
{
  "notification": {
    "smtp_server": "mail.company.com",
    "smtp_port": 587,
    "username": "your-username",
    "password": "your-password"
  }
}
```

## Complete Configuration Examples

### Minimal Configuration
```json
{
  "key_column": "customer_id",
  "merged_file": "customer_data.csv"
}
```

### Development Configuration
```json
{
  "watch_dir": "./dev_inbox",
  "archive_dir": "./dev_archive",
  "backup_dir": "./dev_backups",
  "merged_file": "dev_master.csv",
  "key_column": "id",
  "log_level": "DEBUG",
  "log_to_console": true,
  "dry_run": true,
  "show_progress": true,
  "backup_count": 3
}
```

### Production Configuration
```json
{
  "watch_dir": "/data/csv/inbox",
  "archive_dir": "/data/csv/archive",
  "backup_dir": "/data/csv/backups",
  "merged_file": "/data/csv/master_clusters.csv",
  "key_column": "cluster_name",
  "log_file": "/var/log/csv_watchdog.log",
  "log_level": "INFO",
  "checksum_wait_seconds": 10,
  "max_file_size_mb": 1000,
  "required_columns": ["cluster_name", "status", "last_updated"],
  "lock_timeout_seconds": 60,
  "backup_count": 10,
  "sort_output": true,
  "auto_detect_encoding": true,
  "notification": {
    "enabled": true,
    "smtp_server": "smtp.company.com",
    "smtp_port": 587,
    "username": "csv-monitor@company.com",
    "password": "secure-password",
    "from_email": "csv-monitor@company.com",
    "to_emails": ["admin@company.com", "alerts@company.com"],
    "notify_on_error": true,
    "notify_on_success": false
  }
}
```

### High-Volume Processing Configuration
```json
{
  "watch_dir": "/fast_storage/csv/inbox",
  "archive_dir": "/archive_storage/csv",
  "backup_dir": "/backup_storage/csv",
  "merged_file": "/fast_storage/csv/master.csv",
  "key_column": "transaction_id",
  "checksum_wait_seconds": 2,
  "chunk_size": 16384,
  "max_file_size_mb": 2000,
  "lock_timeout_seconds": 120,
  "backup_count": 20,
  "log_level": "WARNING",
  "max_clusters_in_log": 5,
  "show_progress": true
}
```

## Configuration Validation

The application validates all configuration values on startup:

### Validation Rules
- `checksum_wait_seconds` must be ≥ 0
- `chunk_size` must be > 0
- `max_file_size_mb` must be > 0
- `key_column` cannot be empty
- `backup_count` must be ≥ 0
- File extensions must start with '.' and be at least 2 characters
- No duplicate extensions allowed
- Boolean values must be true or false

### Error Handling
- Invalid configuration values cause startup failure
- Unknown configuration keys generate warnings but don't stop execution
- Missing configuration file uses all default values

## Environment Variables

While not directly supported, you can use environment variable substitution in your deployment scripts:

**Shell Script Example:**
```bash
#!/bin/bash
export SMTP_PASSWORD="your-secure-password"
export WATCH_DIR="/data/csv/inbox"

# Create config with environment variables
cat > config.json << EOF
{
  "watch_dir": "$WATCH_DIR",
  "notification": {
    "password": "$SMTP_PASSWORD"
  }
}
EOF

python csv_watchdog.py
```

## Security Considerations

### Sensitive Data
- Store SMTP passwords securely
- Consider using app-specific passwords
- Restrict file system permissions on config files
- Use environment variables for sensitive settings in production

### File Permissions
Recommended permissions:
- Config file: `600` (owner read/write only)
- Script file: `755` (owner read/write/execute, others read/execute)
- Data directories: `755` (owner full access, others read/execute)
- Log files: `644` (owner read/write, others read)

### Network Security
- Ensure SMTP connections use TLS/SSL
- Consider firewall rules for SMTP traffic
- Use secure passwords and 2FA where possible

## Troubleshooting Configuration

### Common Configuration Errors

**JSON Syntax Errors:**
```
Configuration error: Failed to load config.json: Expecting ',' delimiter: line 5 column 25 (char 123)
```
- Check for missing commas, quotes, or brackets
- Validate JSON syntax with online validators

**Invalid Values:**
```
Configuration error: checksum_wait_seconds must be non-negative
```
- Check that numeric values meet minimum requirements
- Ensure boolean values are `true` or `false` (lowercase)

**File Path Issues:**
```
Watch directory error: [Errno 2] No such file or directory: '/invalid/path'
```
- Verify directory paths exist or can be created
- Check file system permissions

### Testing Configuration

**Validate Config Only:**
```bash
python -c "
import json
from csv_watchdog import load_config
try:
    config = load_config()
    print('Configuration is valid')
    print(json.dumps(config, indent=2))
except Exception as e:
    print(f'Configuration error: {e}')
"
```

**Test with Dry Run:**
```bash
python csv_watchdog.py --dry-run --log-to-console
```

This will validate the configuration and show what would happen without making any changes.