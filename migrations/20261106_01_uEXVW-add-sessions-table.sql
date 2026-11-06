-- add sessions table
-- depends: 20261105_01_lxl33-fix-user-table-email-column-validation

CREATE TABLE IF NOT EXISTS sessions (
    token_hash  BYTEA PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    create_ts   TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_ts  TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions (user_id);