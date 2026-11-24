CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    telegram_update_id INTEGER NOT NULL UNIQUE,
    source_json TEXT NOT NULL,
    document_json TEXT,
    status TEXT NOT NULL,
    estimated_length_mm REAL,
    error TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE INDEX jobs_status_created_at ON jobs (status, created_at, id);
