DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'admin') THEN

      CREATE USER admin WITH PASSWORD 'admin';
   END IF;
END
$do$;

ALTER USER admin WITH SUPERUSER;

DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_database
      WHERE  datname = 'previanza') THEN

      CREATE DATABASE previanza;
   END IF;
END
$do$;

GRANT ALL PRIVILEGES ON DATABASE previanza TO admin;