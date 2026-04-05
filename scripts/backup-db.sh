#!/bin/bash
# Daily PostgreSQL backup for NetLedger
# Run via cron: 0 2 * * * /opt/netledger/scripts/backup-db.sh

BACKUP_DIR="/opt/netledger/backups"
CONTAINER="2maxnetbill-db-1"
DB_NAME="netbill"
DB_USER="netbill"
KEEP_DAYS=30

mkdir -p "$BACKUP_DIR"

FILENAME="netledger_$(date +%Y-%m-%d_%H%M%S).sql.gz"

# Dump and compress
docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$FILENAME"

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$BACKUP_DIR/$FILENAME" | cut -f1)
    echo "$(date): Backup successful - $FILENAME ($SIZE)"
else
    echo "$(date): BACKUP FAILED!"
    exit 1
fi

# Remove backups older than KEEP_DAYS
find "$BACKUP_DIR" -name "netledger_*.sql.gz" -mtime +$KEEP_DAYS -delete

echo "$(date): Cleanup done. Backups remaining: $(ls -1 $BACKUP_DIR/netledger_*.sql.gz 2>/dev/null | wc -l)"
