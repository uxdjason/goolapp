CREATE TABLE IF NOT EXISTS festivals (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  region      TEXT NOT NULL,
  city        TEXT NOT NULL,
  venue       TEXT NOT NULL,
  start_date  TEXT NOT NULL,
  end_date    TEXT NOT NULL,
  tags        TEXT
);
CREATE INDEX IF NOT EXISTS idx_region     ON festivals(region);
CREATE INDEX IF NOT EXISTS idx_start_date ON festivals(start_date);
CREATE INDEX IF NOT EXISTS idx_end_date   ON festivals(end_date);
