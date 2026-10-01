-- Referenzschema. Die echte DB wird durch SQLAlchemy Base.metadata.create_all() erzeugt.
CREATE TABLE dim_region (
    region_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rki_region_id INTEGER NOT NULL UNIQUE,
    region_name VARCHAR(80) NOT NULL UNIQUE,
    is_national BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL
);

CREATE TABLE dim_age_group (
    age_group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    age_group_code VARCHAR(16) NOT NULL UNIQUE,
    display_name VARCHAR(80) NOT NULL,
    sort_order INTEGER NOT NULL
);

CREATE TABLE etl_run (
    etl_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at DATETIME NOT NULL,
    finished_at DATETIME,
    status VARCHAR(30) NOT NULL,
    source_type VARCHAR(30) NOT NULL,
    source_url TEXT,
    source_hash VARCHAR(64),
    rows_downloaded INTEGER NOT NULL DEFAULT 0,
    rows_valid INTEGER NOT NULL DEFAULT 0,
    rows_rejected INTEGER NOT NULL DEFAULT 0,
    rows_inserted INTEGER NOT NULL DEFAULT 0,
    rows_updated INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE TABLE fact_are_incidence (
    incidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id INTEGER NOT NULL REFERENCES dim_region(region_id),
    age_group_id INTEGER NOT NULL REFERENCES dim_age_group(age_group_id),
    season VARCHAR(16) NOT NULL,
    calendar_week VARCHAR(8) NOT NULL,
    incidence_value FLOAT,
    source_hash VARCHAR(64),
    imported_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    imported_by_run_id INTEGER REFERENCES etl_run(etl_run_id),
    CONSTRAINT uq_are_region_age_week UNIQUE(region_id, age_group_id, calendar_week)
);
