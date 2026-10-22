# SynapseOS Deployment & Operations Guide

**Version**: 0.2.0  
**Target Environment**: Linux VM / Docker Compose / Kubernetes  

This guide provides instructions for deploying SynapseOS in production or staging environments.

---

## 1. Prerequisites

- **Host Specifications**: Minimum 4 CPU cores, 8GB RAM, 20GB SSD storage.
- **Operating System**: Ubuntu 22.04 LTS / Debian 12 / macOS / Windows Server.
- **Software**:
  - Docker 24+ & Docker Compose v2.20+
  - Node.js 20+ & Python 3.12+ (for standalone host deployment)
  - Reverse proxy: Nginx or Caddy with valid SSL/TLS certificates.

---

## 2. Docker Compose Deployment (Recommended)

### Step 1: Clone Repository & Setup Environment
```bash
git clone https://github.com/ManyaS-Git/synapseos.git
cd synapseos
cp .env.example .env
```

### Step 2: Configure Production Variables in `.env`
```env
# Application Core
APP_ENV=production
APP_SECRET_KEY=generate_a_64_character_random_hex_string
JWT_SECRET_KEY=generate_another_64_character_random_hex_string

# Nebius Token Factory
NEBIUS_API_KEY=your_live_nebius_api_key
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1/
NEBIUS_MODEL=nvidia/nemotron-4-340b-instruct
PRIVACY_MODE=hybrid

# Database Credentials
POSTGRES_USER=synapseos_prod
POSTGRES_PASSWORD=strong_unique_postgres_password
POSTGRES_DB=synapseos
NEO4J_PASSWORD=strong_unique_neo4j_password
```

### Step 3: Launch Services
```bash
docker compose up -d
```

### Step 4: Verify Service Health
```bash
docker compose ps
curl http://localhost:8000/health
```

---

## 3. Standalone Host Deployment

### Backend (FastAPI):
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Production server via Uvicorn with workers
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
```

### Frontend (Next.js):
```bash
cd apps/web
npm install
npm run build
npm start -- -p 3000
```

---

## 4. Reverse Proxy & SSL Configuration (Nginx)

```nginx
server {
    listen 80;
    server_name synapseos.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name synapseos.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/synapseos.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/synapseos.yourdomain.com/privkey.pem;

    # Frontend routes
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API routes
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 15M; # Support document uploads up to 10MB
    }

    # API docs & health
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

---

## 5. Health Monitoring & Recovery

- **Liveness probe**: `GET /health/liveness` returns `{"status": "alive"}`.
- **Deep Health probe**: `GET /health` tests PostgreSQL, Redis, Qdrant, Neo4j, and Nebius Token Factory connectivity.
- **Backups**:
  - PostgreSQL database dump: `pg_dump -U synapseos synapseos > backup_$(date +%F).sql`
  - Qdrant snapshots: Create collection snapshots via Qdrant snapshot API.
