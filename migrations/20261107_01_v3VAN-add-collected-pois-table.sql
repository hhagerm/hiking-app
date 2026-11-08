-- add collected_pois table
-- depends: 20261106_01_uEXVW-add-sessions-table

CREATE TABLE IF NOT EXISTS collected_pois (
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    osm_type   CHAR(1) NOT NULL,
    osm_id     BIGINT  NOT NULL,
    collect_ts TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (user_id, osm_type, osm_id),
    FOREIGN KEY (osm_type, osm_id) REFERENCES pois (osm_type, osm_id) ON DELETE CASCADE
);