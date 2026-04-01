---
name: agentic-devops
description: Production-grade DevOps toolkit for your homelab — Docker management, process monitoring, log analysis, and health checks. Works with your existing freaked/Greench/Aspire setup.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - docker
        - systemctl
        - ss
---

# Agentic DevOps

Full DevOps toolkit for managing your homelab services.
Docker, processes, logs, health — all via natural language.
Configured for your homelab: freaked (192.168.178.90), Greench (192.168.178.76), Aspire (192.168.178.96).

## Usage

```
Check all services are running
What's running on freaked?
Restart the greenchclaw gateway
Check Docker containers
Show logs for nexusclaw
Is port 50420 open?
Health check all machines
How much RAM is freaked using?
```

## Machine inventory

```
freaked  = 192.168.178.90  (Docker, crypto bots, various services)
Greench  = 192.168.178.76  (Win11, ComfyUI, OpenClaw Desktop)
Aspire   = 192.168.178.96  (Docker, MCP, Local services)
```

## Commands

### Docker management
```bash
# List all containers
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Container logs (last 50 lines)
docker logs --tail 50 {container_name}

# Restart container
docker restart {container_name}

# Container resource usage
docker stats --no-stream
```

### Process management
```bash
# Check if service is running
systemctl --user status {service}

# Restart user service
systemctl --user restart {service}

# All running user services
systemctl --user list-units --state=running
```

### Port checking
```bash
# Is port open?
ss -tlnp | grep :{port}

# All listening ports
ss -tlnp
```

### System resources
```bash
# CPU and memory
top -bn1 | head -20

# Disk usage
df -h

# Memory details
free -h
```

### Remote machine check (via SSH)
```bash
ssh greench@192.168.178.90 "docker ps && df -h && free -h"
```

## Service registry

Key services to monitor:

| Service | Machine | Port | Check |
|---------|---------|------|-------|
| greenchclaw-gateway | Greench | 50420 | systemctl --user status greenchclaw-gateway |
| nexusclaw-gateway | Greench | 19789 | systemctl --user status nexusclaw-gateway |
| Library browser | freaked | ? | curl http://library.greench-ai.net/ |
| ComfyUI | Greench | 8188 | curl http://192.168.178.76:8188/ |

## Health report format

```
🏥 Homelab Health Check — April 1, 2026 09:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🖥️ Greench (192.168.178.76)
  ✅ greenchclaw-gateway  running on :50420
  ✅ nexusclaw-gateway    running on :19789
  ✅ ComfyUI             running on :8188
  💾 Disk: 234GB free | 🧠 RAM: 12GB free

🖥️ freaked (192.168.178.90)
  ✅ NexHub              running
  ✅ Library             running
  ✅ SOLHUNTER           running
  💾 Disk: 89GB free | 🧠 RAM: 4GB free

⚠️ Issues found: 0
```

## Smart responses

- If a service is down: suggest restart command automatically
- If disk <10%: warn immediately
- If a port is blocked: suggest firewall check
- Always show the exact command you're running before running it
