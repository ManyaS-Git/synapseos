# Contributing to SynapseOS

Thank you for your interest in contributing to SynapseOS! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Branch Strategy](#branch-strategy)
- [Naming Conventions](#naming-conventions)
- [Folder Conventions](#folder-conventions)
- [Commit Style](#commit-style)
- [Code Review Checklist](#code-review-checklist)
- [Documentation Requirements](#documentation-requirements)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/synapseos.git`
3. Create a branch from `main` or `develop`
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.12+
- Git

### Quick Start

```bash
# Clone and setup
git clone https://github.com/your-username/synapseos.git
cd synapseos
cp .env.example .env
docker compose up -d
```

### IDE Setup

We recommend VS Code with the following extensions:

- ESLint
- Prettier
- Python
- Pylance
- Tailwind CSS IntelliSense
- EditorConfig
- GitLens

## Branch Strategy

We follow a simplified Git Flow model:

```
main          ← Production-ready code
  └── develop ← Integration branch
       ├── feature/xxx  ← New features
       ├── fix/xxx      ← Bug fixes
       ├── refactor/xxx ← Code refactoring
       ├── docs/xxx     ← Documentation changes
       └── test/xxx     ← Test additions/fixes
```

### Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/<short-description>` | `feature/memory-engine-v2` |
| Bug Fix | `fix/<short-description>` | `fix/vector-search-timeout` |
| Refactor | `refactor/<short-description>` | `refactor/agent-runtime` |
| Documentation | `docs/<short-description>` | `docs/api-reference` |
| Test | `test/<short-description>` | `test/memory-integration` |

## Naming Conventions

### TypeScript/JavaScript

| Element | Convention | Example |
|---------|-----------|---------|
| Variables | camelCase | `memoryStore` |
| Functions | camelCase | `getContext()` |
| Components | PascalCase | `MemoryPanel` |
| Files | kebab-case | `memory-panel.tsx` |
| Types/Interfaces | PascalCase | `MemoryEntry` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRY_COUNT` |
| CSS Classes | Tailwind utility classes | `bg-primary text-white` |

### Python

| Element | Convention | Example |
|---------|-----------|---------|
| Variables | snake_case | `memory_store` |
| Functions | snake_case | `get_context()` |
| Classes | PascalCase | `MemoryEngine` |
| Files | snake_case | `memory_engine.py` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Private | Leading underscore | `_internal_method()` |

### Database

| Element | Convention | Example |
|---------|-----------|---------|
| Tables | snake_case, plural | `memory_entries` |
| Columns | snake_case | `created_at` |
| Indexes | `idx_<table>_<column>` | `idx_memory_entries_user_id` |

## Folder Conventions

### Frontend (`apps/web/src/`)

```
features/
  memory/
    components/     # React components
    hooks/          # Custom React hooks
    services/       # API client functions
    store/          # Zustand stores
    types/          # TypeScript types
    utils/          # Utility functions
    index.ts        # Public exports
```

### Backend (`apps/api/app/`)

```
routers/        # FastAPI route handlers
models/         # SQLAlchemy models
schemas/        # Pydantic schemas
services/       # Business logic
repositories/   # Data access layer
agents/         # AI agent implementations
utils/          # Utility functions
```

### Services (`services/<name>/src/`)

```
__init__.py
main.py         # Service entry point
config.py       # Configuration
models/         # Data models
services/       # Business logic
utils/          # Utilities
tests/          # Service-specific tests
```

## Commit Style

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code style changes (formatting, etc.) |
| `refactor` | Code refactoring |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvements |
| `ci` | CI/CD changes |
| `build` | Build system changes |

### Examples

```
feat(memory): add long-term memory compression
fix(rag): resolve embedding dimension mismatch
docs(api): update endpoint documentation
refactor(agent): simplify routing logic
test(memory): add memory persistence tests
chore(deps): update Python dependencies
```

### Scopes

| Scope | Description |
|-------|------------|
| `memory` | Memory Engine |
| `agent` | Agent Runtime |
| `rag` | RAG Pipeline |
| `graph` | Knowledge Graph |
| `embed` | Embeddings Service |
| `llm` | LLM Router |
| `api` | FastAPI Backend |
| `web` | Next.js Frontend |
| `desktop` | Desktop Application |
| `sdk` | JavaScript SDK |
| `infra` | Infrastructure/Docker |
| `docs` | Documentation |

## Code Review Checklist

Before submitting a PR, ensure:

- [ ] Code follows the project's style guidelines
- [ ] No commented-out code or debug statements
- [ ] All new code has corresponding tests
- [ ] Existing tests still pass
- [ ] Documentation is updated if needed
- [ ] No secrets or credentials are committed
- [ ] Error handling is appropriate
- [ ] Type safety is maintained (no `any` types)
- [ ] Performance implications are considered
- [ ] Breaking changes are documented
- [ ] Commit messages follow Conventional Commits

## Documentation Requirements

### Code Documentation

- **Functions**: Docstrings for all public functions/methods
- **Classes**: Class-level docstrings explaining purpose
- **Modules**: Module-level docstrings for non-obvious modules
- **Types**: JSDoc comments for complex TypeScript types

### API Documentation

- All endpoints must have OpenAPI descriptions
- Request/response schemas must be documented
- Error responses must be documented

### Architecture Documentation

- Major changes require architecture documentation updates
- New services require a design document
- Diagrams should be updated when relationships change

## Pull Request Process

1. **Create a descriptive PR title** following commit conventions
2. **Fill out the PR template** completely
3. **Link related issues** using GitHub keywords
4. **Request review** from at least one maintainer
5. **Respond to review comments** promptly
6. **Squash and merge** once approved

### PR Size Guidelines

- **Small** (< 200 lines): Quick review
- **Medium** (200-500 lines): Standard review
- **Large** (500+ lines): Consider splitting into smaller PRs

## Questions?

Open a [GitHub Discussion](https://github.com/synapseos/synapseos/discussions) if you have questions about contributing.
