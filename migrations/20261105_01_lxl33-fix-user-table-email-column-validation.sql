-- fix user table email column validation
-- depends: 20261103_01_RlLMK-add-user-table

ALTER TABLE users DROP CONSTRAINT email_format;
ALTER TABLE users ADD CONSTRAINT email_format CHECK (email LIKE '%_@_%._%');