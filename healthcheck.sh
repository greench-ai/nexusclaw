#!/bin/bash
# NexusClaw System Health Check
echo "⚡ NexusClaw Health Check"
echo "========================"

check() {
    if $1; then
        echo "  ✅ $2"
    else
        echo "  ❌ $2"
    fi
}

# Docker
check "docker info >/dev/null 2>&1" "Docker daemon"

# Docker Compose
check "docker compose version >/dev/null 2>&1" "Docker Compose"

# Python
check "python3 --version >/dev/null 2>&1" "Python 3"

# Ports
check "curl -s http://localhost:8080/health >/dev/null 2>&1" "API (port 8080)"
check "curl -s http://localhost:11434/api/tags >/dev/null 2>&1" "Ollama (port 11434)"
check "curl -s http://localhost:6333 >/dev/null 2>&1" "Qdrant (port 6333)"

# Containers
echo ""
echo "Containers:"
for c in $(docker ps --format '{{.Names}}' 2>/dev/null | grep -E "nexusclaw|ollama|qdrant|redis"); do
    echo "  ✅ $c ($(docker ps --filter name=$c --format '{{.Status}}' | head -1))"
done

# BTC containers
BTC_COUNT=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E "hungry|sharp|relaxed|cool|btcrecover" | wc -l)
echo "  ⚡ BTC attack containers: $BTC_COUNT/8 running"

# BTC sync
SYNC=$(bitcoin-cli getblockchaininfo 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{d[\"verificationprogress\"]*100:.1f}%')" || echo "unknown")
echo "  ₿ Bitcoin Core sync: $SYNC"

echo ""
echo "========================"
