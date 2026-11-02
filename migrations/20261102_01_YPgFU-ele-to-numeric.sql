-- ele to numeric
-- depends: 20261031_01_iJ9MC-initial-schema

ALTER TABLE pois
  ALTER COLUMN ele TYPE numeric(5,1) USING ele::numeric(5,1);