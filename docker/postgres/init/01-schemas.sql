-- Better Auth migrations run before the backend has necessarily created this schema.
CREATE SCHEMA IF NOT EXISTS auth;
