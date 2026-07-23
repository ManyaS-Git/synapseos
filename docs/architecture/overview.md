# Architecture Overview

## System Architecture

SynapseOS follows a microservices-inspired monorepo architecture with clean separation of concerns.

### High-Level Design

TODO: Add architecture diagram

### Design Principles

1. **Privacy-First**: All data stored locally by default
2. **Clean Architecture**: Clear separation of concerns
3. **Domain-Driven Design**: Organized around business domains
4. **SOLID Principles**: Maintainable, extensible code
5. **Event-Driven**: Loosely coupled services via message passing

### Component Overview

#### Frontend Layer (`apps/web`)
- Next.js 14 with App Router
- Server and client components
- Real-time WebSocket updates
- React Flow for graph visualization

#### API Layer (`apps/api`)
- FastAPI with async support
- Pydantic validation
- SQLAlchemy async ORM
- RESTful + WebSocket endpoints

#### Service Layer (`services/`)
- Memory Engine: Long-term memory management
- Agent Runtime: Multi-agent orchestration
- RAG Pipeline: Retrieval-augmented generation
- Reflection Engine: Self-improvement
- Embeddings: Vector embedding generation
- LLM Router: Local/cloud model routing
- Connectors: External data ingestion
- Scheduler: Background task management

#### Data Layer
- PostgreSQL: Primary relational data
- Qdrant: Vector storage and search
- Neo4j: Knowledge graph storage
- Redis: Caching and message broker

### Communication Patterns

- **Synchronous**: REST API for request/response
- **Asynchronous**: WebSocket for real-time updates
- **Internal**: Direct function calls within services
- **Cross-service**: Redis pub/sub for event-driven communication

### Security Architecture

- JWT-based authentication
- Encryption at rest for sensitive data
- No telemetry without explicit opt-in
- Local-first data processing

TODO: Add detailed security architecture
