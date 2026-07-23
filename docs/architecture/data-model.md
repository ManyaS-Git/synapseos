# Identity Data Model

## Entity-Relationship Diagram

```mermaid
erDiagram
    USERS {
        uuid id PK
        varchar email UK
        varchar username UK
        varchar full_name
        text avatar_url
        varchar password_hash
        boolean email_verified
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
        timestamptz last_login
    }

    WORKSPACES {
        uuid id PK
        uuid owner_id FK
        varchar name
        varchar slug UK
        text description
        timestamptz created_at
        timestamptz updated_at
    }

    WORKSPACE_MEMBERS {
        uuid workspace_id FK
        uuid user_id FK
        enum role
        timestamptz created_at
    }

    PROJECTS {
        uuid id PK
        uuid workspace_id FK
        varchar name
        text description
        varchar icon
        varchar color
        boolean archived
        timestamptz created_at
        timestamptz updated_at
    }

    USERS ||--o{ WORKSPACES : "owns"
    USERS ||--o{ WORKSPACE_MEMBERS : "belongs to"
    WORKSPACES ||--o{ WORKSPACE_MEMBERS : "has members"
    WORKSPACES ||--o{ PROJECTS : "contains"
```

## Relationships

| Relationship | Type | Description |
|-------------|------|-------------|
| User → Workspace | One-to-Many | A user owns multiple workspaces |
| User → WorkspaceMember | One-to-Many | A user can belong to multiple workspaces |
| Workspace → WorkspaceMember | One-to-Many | A workspace has multiple members |
| Workspace → Project | One-to-Many | A workspace contains multiple projects |

## Ownership Hierarchy

```
User (owner)
  └── Workspace
        ├── WorkspaceMember (owner, admin, member)
        └── Project
              └── [Future: Memory, Agent, Connector]
```

## Roles

| Role | Permissions |
|------|------------|
| `owner` | Full control. Can delete workspace, manage all members |
| `admin` | Can update workspace, manage members |
| `member` | Can view and create projects |

## Indexes

| Table | Index | Type |
|-------|-------|------|
| users | email | Unique |
| users | username | Unique |
| workspaces | slug | Unique |
| workspaces | owner_id | Foreign key |
| workspace_members | (workspace_id, user_id) | Composite primary key |
| projects | workspace_id | Foreign key |
