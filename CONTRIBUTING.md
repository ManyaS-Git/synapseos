# Contributing to SynapseOS

> **This is a private, confidential project.** External contributions are not accepted.

## Internal Development

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.12+
- Git

### Setup

```bash
git clone https://github.com/ManyaS-Git/synapseos.git
cd synapseos
cp .env.example .env
docker compose up -d
```

### Branch Strategy

```
main          ← Production-ready code
  └── develop ← Integration branch
       ├── feature/xxx  ← New features
       ├── fix/xxx      ← Bug fixes
       └── refactor/xxx ← Code refactoring
```

### Commit Style

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

| Type | Description |
|------|------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `refactor` | Code refactoring |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |

### Code Review

All changes require review before merging to `main`.
