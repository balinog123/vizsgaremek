#!/bin/bash
SRC="/srv/backup"
DST1="backupwin@192.168.130.100:/home/backupwin/backup"
DST2="backupwin@192.168.120.100:/home/backupwin/backup"
LOG="/var/log/rsync_daily_backup.log"
KEY="/home/backupwin/.ssh/rsync_key"

echo "=== $(date) ===" >> "$LOG"

# Loop through both destinations
for DST in "$DST1" "$DST2"; do
    echo "Syncing to $DST..." >> "$LOG"
    
    rsync -avz --delete \
        -e "ssh -i $KEY -o StrictHostKeyChecking=accept-new" \
        "$SRC" "$DST" >> "$LOG" 2>&1

    if [ $? -eq 0 ]; then
        echo "OK: $DST" >> "$LOG"
    else
        echo "HIBA!: $DST" >> "$LOG"
    fi
done