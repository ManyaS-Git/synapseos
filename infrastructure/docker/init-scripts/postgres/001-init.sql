-- SynapseOS Database Initialization
-- This script runs on first PostgreSQL container start.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- TODO: Create initial tables via Alembic migrations
-- This file is for extensions and initial setup only.
