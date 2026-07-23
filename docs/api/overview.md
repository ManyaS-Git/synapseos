# API Documentation

## Overview

The SynapseOS API is built with FastAPI and provides RESTful endpoints with WebSocket support.

## Base URL

```
http://localhost:8000
```

## Authentication

TODO: Document authentication flow

## Endpoints

### Health
- `GET /health` — Basic health check
- `GET /health/detailed` — Detailed health with service status

### Memory
- `GET /api/v1/memory` — List memories
- `POST /api/v1/memory` — Create memory
- `GET /api/v1/memory/{id}` — Get memory
- `PUT /api/v1/memory/{id}` — Update memory
- `DELETE /api/v1/memory/{id}` — Delete memory
- `POST /api/v1/memory/search` — Semantic search

### Agents
- `GET /api/v1/agents` — List agents
- `POST /api/v1/agents/message` — Send message to agent
- `GET /api/v1/agents/{id}/status` — Get agent status

### Graph
- `GET /api/v1/graph/nodes` — Get graph nodes
- `GET /api/v1/graph/nodes/{id}/edges` — Get node edges
- `GET /api/v1/graph/search` — Search graph

### Settings
- `GET /api/v1/settings` — Get settings
- `PUT /api/v1/settings` — Update settings

## WebSocket

TODO: Document WebSocket endpoints for real-time updates

## Rate Limiting

TODO: Document rate limiting policies

## Error Responses

TODO: Document error response format
