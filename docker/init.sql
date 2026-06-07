-- NSE Scanner database initialization
-- Runs once when PostgreSQL container is first created

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'Asia/Kolkata';

-- Grants (postgres user already owns the db, this is a no-op but explicit)
GRANT ALL PRIVILEGES ON DATABASE nse_scanner TO nse;
