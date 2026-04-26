# NexusClaw API Reference v0.19

Base URL: `http://localhost:8080`

## Authentication

All endpoints (except `/health` and `/v1/auth/*`) require `Authorization: Bearer <token>` header.

### Register
```bash
POST /v1/auth/register
Content-Type: application/json
{"email": "user@example.com", "password": "pass123", "displayName": "User"}
```
**Response:** `{token, user, workspace}`

### Login
```bash
POST /v1/auth/login
Content-Type: application/json
{"email": "user@example.com", "password": "pass123"}
```
**Response:** `{token, user, workspace}`

## Chat

### Create Session
```bash
POST /v1/chat/sessions
Authorization: Bearer <token>
{"title": "My Chat"}
```
**Response:** `{id, userId, title, messages, createdAt}`

### List Sessions
```bash
GET /v1/chat/sessions
Authorization: Bearer <token>
```

### Stream Chat
```bash
POST /v1/chat/answer/stream
Authorization: Bearer <token>
Content-Type: application/json
{"sessionId": "uuid", "message": "Hello", "provider": "ollama", "model": "llama3.2"}
```
**Response:** SSE stream with `data: {"type":"chunk","content":"..."}` events.

## Files

### Upload
```bash
POST /v1/files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
file=@document.pdf
```
**Response:** `{ok: true, fileId: "uuid", status: "queued"}`

### List Files
```bash
GET /v1/files
Authorization: Bearer <token>
```

## Autonomy

### Create Goal
```bash
POST /v1/autonomy/goals
Authorization: Bearer <token>
{"title": "Research AI", "objective": "search for latest AI news; summarize findings"}
```

### List Goals
```bash
GET /v1/autonomy/goals
Authorization: Bearer <token>
```

### Approve Goal
```bash
POST /v1/autonomy/goals/<goal_id>/approve
Authorization: Bearer <token>
```

### Kill All Goals (Kill Switch)
```bash
POST /v1/autonomy/kill
Authorization: Bearer <token>
```
**Response:** `{ok: true, killed: N}`

## WebSocket

Connect to `/ws/<session_id>` for real-time streaming.

```javascript
const ws = new WebSocket("ws://localhost:8080/ws/main");
ws.send(JSON.stringify({type: "chat", content: "Hello", provider: "ollama", model: "llama3.2"}));
ws.onmessage = e => console.log(JSON.parse(e.data));
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXUS_SECRET` | `nexusclaw-dev-...` | JWT signing secret |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `MINIMAXI_API_KEY` | - | Minimaxi API key |
| `BRAVE_API_KEY` | - | Brave Search API |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant vector DB |
