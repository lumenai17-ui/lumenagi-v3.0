#!/bin/bash
# Log maintenance script — rotates and archives logs

LOG_DIR="/home/lumen/.openclaw/workspace/logs"
ARCHIVE_DIR="/home/lumen/.openclaw/workspace/logs/archive"
MAX_SIZE_MB=50
MAX_DAYS=7

mkdir -p "$ARCHIVE_DIR"

# Archive old logs (> 7 days)
find "$LOG_DIR" -name "*.log" -type f -mtime +$MAX_DAYS -exec gzip {} \; -exec mv {}.gz "$ARCHIVE_DIR/" \;

# Check total size
SIZE_MB=$(du -sm "$LOG_DIR" | cut -f1)

if [ "$SIZE_MB" -gt "$MAX_SIZE_MB" ]; then
    echo "$(date): Log size ${SIZE_MB}MB exceeds ${MAX_SIZE_MB}MB, rotating..."
    # Archive largest files
    find "$LOG_DIR" -name "*.log" -type f -exec ls -l {} \; | sort -k5 -n -r | head -5 | awk '{print $9}' | while read file; do
        gzip "$file" && mv "$file.gz" "$ARCHIVE_DIR/"
    done
fi

echo "$(date): Log maintenance complete. Size: ${SIZE_MB}MB"
