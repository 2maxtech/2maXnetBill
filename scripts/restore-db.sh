#!/bin/bash
# Restore PostgreSQL backup for NetLedger
# Usage: ./restore-db.sh /opt/netledger/backups/netledger_2026-04-05_020000.sql.gz

CONTAINER="2maxnetbill-db-1"
DB_NAME="netbill"
DB_USER="netbill"

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh /opt/netledger/backups/netledger_*.sql.gz 2>/dev/null
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "File not found: $1"
    exit 1
fi

echo "WARNING: This will REPLACE ALL DATA in $DB_NAME with the backup."
echo "Backup file: $1"
read -p "Type 'yes' to confirm: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "Stopping app containers..."
docker compose stop backend celery-worker celery-beat

echo "Restoring database..."
gunzip -c "$1" | docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" --single-transaction

if [ $? -eq 0 ]; then
    echo "Restore successful!"
else
    echo "RESTORE FAILED!"
fi

echo "Starting app containers..."
docker compose start backend celery-worker celery-beat

echo "Done."
