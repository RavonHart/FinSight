-- FinSight Database Initialization Script
-- Ensures pgvector and uuid extensions are active

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create application role for non-superuser RLS enforcement
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'finsight_app') THEN
    CREATE ROLE finsight_app WITH LOGIN PASSWORD 'finsight_secret';
  END IF;
  GRANT ALL PRIVILEGES ON SCHEMA public TO finsight_app;
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO finsight_app;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO finsight_app;
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO finsight_app;
  RAISE NOTICE 'FinSight PostgreSQL extensions and roles initialized successfully.';
END $$;
