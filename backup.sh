#!/bin/bash
# NexusClaw Backup Script
# Usage: ./backup.sh [--restore]

set -e
BACKUP_DIR="${NEXUS_BACKUP_DIR:-$HOME/NexusClaw/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M)
BACKUP_FILE="$BACKUP_DIR/nexusclaw_backup_$TIMESTAMP.tar.gz"

echo "⚡ NexusClaw Backup"
echo "=================="

mkdir -p "$BACKUP_DIR"

if [ "$1" = "--restore" ]; then
    echo "Available backups:"
    ls -1t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -5
    read -p "Backup file to restore: " BACKUP_FILE
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "File not found: $BACKUP_FILE"
        exit 1
    fi
    echo "Stopping services..."
    docker compose down 2>/dev/null || true
    
    tar -xzf "$BACKUP_FILE" -C ~/
    echo "✅ Restored from: $BACKUP_FILE"
    exit 0
fi

# Create backup
echo "Backing up to: $BACKUP_FILE"

# Files to back up
TAR_ARGS="-czf $BACKUP_FILE"
EXCLUDE="--exclude=*.pyc --exclude=__pycache__ --exclude=.git --exclude=node_modules --exclude=*.log --exclude=benchmark_results.json"

# Backup config files
echo "  → Config files"
tar $TAR_ARGS $EXCLUDE \
    ~/.nexusclaw/config.json \
    ~/.nexusclaw/soul.json \
    ~/.nexusclaw/webhooks.json \
    ~/.nexusclaw/costs.json \
    ~/.nexusclaw/rate_limits.json \
    ~/.nexusclaw/email_config.json \
    2>/dev/null || true

# Backup sessions DB
echo "  → Session database"
tar $TAR_ARGS ~/.nexusclaw/sessions.db 2>/dev/null || true

# Backup vector memory
echo "  → Vector memory"
tar $TAR_ARGS ~/.nexusclaw/memory/ 2>/dev/null || true

# Backup workspace
echo "  → Workspace"
tar $TAR_ARGS ~/.openclaw/workspace/memory/ 2>/dev/null || true

# Backup NexusClaw source
echo "  → NexusClaw source"
tar $TAR_ARGS -C "$(dirname $(find ~ -name nexusclaw -type d 2>/dev/null | head -1) 2>/dev/null || echo ".")" . 2>/dev/null || true

# Backup Docker volumes
echo "  → Docker volumes"
docker run --rm -v nexusclaw_qdrant_data:/data -v nexusclaw_redis_data:/redis alpine tar czf - -C /data . 2>/dev/null > "$BACKUP_DIR/qdrant_$TIMESTAMP.tar.gz" || true
docker run --rm -v nexusclaw_redis_data:/data alpine tar czf - -C /data . 2>/dev/null > "$BACKUP_DIR/redis_$TIMESTAMP.tar.gz" || true

echo ""
echo "✅ Backup complete: $BACKUP_FILE"
echo "📦 Size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo ""
echo "To restore: $0 --restore"
