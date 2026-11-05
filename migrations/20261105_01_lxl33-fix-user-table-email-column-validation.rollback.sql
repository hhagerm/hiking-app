
ALTER TABLE users DROP CONSTRAINT email_format;
ALTER TABLE users ADD CONSTRAINT email_format CHECK (email LIKE '%_@_._%');