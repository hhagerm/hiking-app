-- add user table
-- depends: 20261102_01_YPgFU-ele-to-numeric

CREATE TABLE IF NOT EXISTS users (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username      TEXT NOT NULL,
    email         TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    create_ts     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT username_length CHECK (length(username) BETWEEN 3 AND 32),
    CONSTRAINT email_length    CHECK (length(email) <= 254),
    CONSTRAINT email_format    CHECK (email LIKE '%_@_._%')
);

CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_idx    ON users (lower(email));
CREATE UNIQUE INDEX IF NOT EXISTS users_username_lower_idx ON users (lower(username));