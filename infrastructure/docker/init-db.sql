-- FinSight Database Initialization Script
-- Ensures pgvector and uuid extensions are active

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Verification
DO $$
BEGIN
  RAISE NOTICE 'FinSight PostgreSQL extensions initialized successfully.';
END $$;
