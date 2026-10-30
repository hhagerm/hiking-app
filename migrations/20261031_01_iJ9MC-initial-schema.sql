-- initial schema
-- depends: 

CREATE TABLE IF NOT EXISTS pois (
    osm_type CHAR(1) NOT NULL,
    osm_id   BIGINT  NOT NULL,
    kind     TEXT    NOT NULL,
    name     TEXT,
    ele      REAL,
    tags     JSONB   NOT NULL DEFAULT '{}',
    geom     GEOMETRY(Point, 4326) NOT NULL,
    PRIMARY KEY (osm_type, osm_id)
);
CREATE INDEX IF NOT EXISTS pois_geom_idx ON pois USING GIST (geom);
CREATE INDEX IF NOT EXISTS pois_kind_idx ON pois (kind);