BEGIN;

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

CREATE INDEX IF NOT EXISTS idx_script_character_facts_project_id ON script_character_facts(project_id);
CREATE INDEX IF NOT EXISTS idx_script_character_facts_character_id ON script_character_facts(character_id);

COMMIT;
