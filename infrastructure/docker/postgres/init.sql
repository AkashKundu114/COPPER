-- C.O.P.P.E.R. PostgreSQL Database Initialization Script
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable pgvector if extension is available
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS "vector";
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pgvector extension not found, vector operations will fallback to ChromaDB';
END
$$;

-- Create default schema search path
SET search_path TO public;
