BEGIN;

ALTER TABLE script_projects ADD COLUMN IF NOT EXISTS pacing VARCHAR(50) DEFAULT 'medium' NOT NULL;
ALTER TABLE script_projects ADD COLUMN IF NOT EXISTS scene_frequency VARCHAR(50) DEFAULT 'medium' NOT NULL;
ALTER TABLE script_projects ADD COLUMN IF NOT EXISTS dialogue_density VARCHAR(50) DEFAULT 'medium' NOT NULL;
ALTER TABLE script_projects ADD COLUMN IF NOT EXISTS events_per_episode INTEGER DEFAULT 10 NOT NULL;
ALTER TABLE script_projects ADD COLUMN IF NOT EXISTS yaml_schema_delta JSONB;
ALTER TABLE script_projects ADD COLUMN IF NOT EXISTS split_status VARCHAR(50) DEFAULT 'idle' NOT NULL;
ALTER TABLE script_projects ADD COLUMN IF NOT EXISTS split_stop_requested BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE script_projects ADD COLUMN IF NOT EXISTS generation_status VARCHAR(50) DEFAULT 'idle' NOT NULL;
ALTER TABLE script_projects ADD COLUMN IF NOT EXISTS generation_stop_requested BOOLEAN DEFAULT FALSE NOT NULL;

CREATE TABLE IF NOT EXISTS script_event_batches (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES script_projects(id),
    book_id BIGINT NOT NULL REFERENCES books(id),
    batch_index INTEGER NOT NULL,
    chapter_start_index INTEGER NOT NULL,
    chapter_end_index INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'completed' NOT NULL,
    raw_response JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS script_plot_events (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES script_projects(id),
    batch_id BIGINT NOT NULL REFERENCES script_event_batches(id),
    event_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    source_chapter_start INTEGER NOT NULL,
    source_chapter_end INTEGER NOT NULL,
    locked BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE IF NOT EXISTS script_character_profiles (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES script_projects(id),
    name VARCHAR(255) NOT NULL,
    profile TEXT DEFAULT '' NOT NULL,
    metadata_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE IF NOT EXISTS script_character_facts (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES script_projects(id),
    character_id BIGINT NOT NULL REFERENCES script_character_profiles(id),
    batch_id BIGINT REFERENCES script_event_batches(id),
    fact_type VARCHAR(100) DEFAULT '设定' NOT NULL,
    content TEXT NOT NULL,
    normalized_content VARCHAR(500) NOT NULL,
    status VARCHAR(50) DEFAULT 'active' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE IF NOT EXISTS script_episodes (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES script_projects(id),
    episode_index INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    event_ids JSONB DEFAULT '[]'::jsonb NOT NULL,
    yaml_content TEXT,
    plain_text_content TEXT,
    status VARCHAR(50) DEFAULT 'draft' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_script_event_batches_project_id ON script_event_batches(project_id);
CREATE INDEX IF NOT EXISTS idx_script_plot_events_project_id ON script_plot_events(project_id);
CREATE INDEX IF NOT EXISTS idx_script_characters_project_id ON script_character_profiles(project_id);
CREATE INDEX IF NOT EXISTS idx_script_character_facts_character_id ON script_character_facts(character_id);
CREATE INDEX IF NOT EXISTS idx_script_episodes_project_id ON script_episodes(project_id);

COMMIT;
