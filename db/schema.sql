-- Database schema for RoboticImaging pipeline
-- SQLite 3+

CREATE TABLE IF NOT EXISTS sites (
    site_id TEXT PRIMARY KEY,
    name TEXT,
    location TEXT,
    metadata TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spots (
    spot_id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    image_count INTEGER DEFAULT 0,
    metadata TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (site_id) REFERENCES sites(site_id)
);

CREATE INDEX IF NOT EXISTS idx_spots_site_id ON spots(site_id);

CREATE TABLE IF NOT EXISTS equipment (
    equipment_id TEXT PRIMARY KEY,
    spot_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    equipment_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    location TEXT,
    metadata TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    FOREIGN KEY (site_id) REFERENCES sites(site_id)
);

CREATE INDEX IF NOT EXISTS idx_equipment_spot_id ON equipment(spot_id);
CREATE INDEX IF NOT EXISTS idx_equipment_site_id ON equipment(site_id);
CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment(equipment_type);

CREATE TABLE IF NOT EXISTS question_answers (
    qa_id TEXT PRIMARY KEY,
    spot_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    confidence REAL,
    metadata TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    FOREIGN KEY (site_id) REFERENCES sites(site_id)
);

CREATE INDEX IF NOT EXISTS idx_qa_spot_id ON question_answers(spot_id);
CREATE INDEX IF NOT EXISTS idx_qa_site_id ON question_answers(site_id);

-- Summary/aggregation table for quick queries
CREATE TABLE IF NOT EXISTS spot_summaries (
    spot_id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    equipment_count INTEGER DEFAULT 0,
    qa_count INTEGER DEFAULT 0,
    processing_status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (spot_id) REFERENCES spots(spot_id),
    FOREIGN KEY (site_id) REFERENCES sites(site_id)
);

CREATE INDEX IF NOT EXISTS idx_spot_summaries_site_id ON spot_summaries(site_id);
CREATE INDEX IF NOT EXISTS idx_spot_summaries_status ON spot_summaries(processing_status);
