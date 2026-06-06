CREATE DATABASE ai_novel_screenplay;

\connect ai_novel_screenplay

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    nickname VARCHAR(100),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE IF NOT EXISTS books (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    source_type VARCHAR(50) NOT NULL,
    novel_type VARCHAR(50),
    word_count INTEGER DEFAULT 0 NOT NULL,
    chapter_count INTEGER DEFAULT 0 NOT NULL,
    preprocess_status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE IF NOT EXISTS chapters (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT NOT NULL REFERENCES books(id),
    chapter_index INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE IF NOT EXISTS script_projects (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    book_id BIGINT NOT NULL REFERENCES books(id),
    project_name VARCHAR(255) NOT NULL,
    script_type VARCHAR(100),
    default_style VARCHAR(100),
    default_compression_level VARCHAR(50),
    default_target_duration INTEGER,
    status VARCHAR(50) DEFAULT 'ongoing' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE IF NOT EXISTS generation_tasks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    book_id BIGINT NOT NULL REFERENCES books(id),
    script_project_id BIGINT REFERENCES script_projects(id),
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    current_step VARCHAR(100),
    adapt_scope JSONB,
    generation_config JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    finished_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generation_artifacts (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL REFERENCES generation_tasks(id),
    artifact_type VARCHAR(100) NOT NULL,
    content JSONB,
    version INTEGER DEFAULT 1 NOT NULL,
    editable BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS script_segments (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES script_projects(id),
    book_id BIGINT NOT NULL REFERENCES books(id),
    segment_name VARCHAR(255) NOT NULL,
    adapt_scope JSONB,
    style_source VARCHAR(50) DEFAULT 'inherit_project' NOT NULL,
    style VARCHAR(100),
    compression_level VARCHAR(50),
    target_duration INTEGER,
    actual_word_count INTEGER DEFAULT 0 NOT NULL,
    scene_count INTEGER DEFAULT 0 NOT NULL,
    yaml_content TEXT,
    plain_text_content TEXT,
    status VARCHAR(50) DEFAULT 'draft' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_configs (
    id BIGSERIAL PRIMARY KEY,
    provider VARCHAR(100) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_key_masked VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    temperature NUMERIC(4, 2),
    top_p NUMERIC(4, 2),
    max_tokens INTEGER,
    timeout_seconds INTEGER DEFAULT 60 NOT NULL,
    retry_count INTEGER DEFAULT 2 NOT NULL,
    task_scope JSONB,
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE IF NOT EXISTS prompt_templates (
    id BIGSERIAL PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    output_format VARCHAR(50) NOT NULL,
    variables JSONB,
    version INTEGER DEFAULT 1 NOT NULL,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE IF NOT EXISTS prompt_template_versions (
    id BIGSERIAL PRIMARY KEY,
    template_id BIGINT NOT NULL REFERENCES prompt_templates(id),
    version INTEGER NOT NULL,
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    output_format VARCHAR(50) NOT NULL,
    variables JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_call_logs (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT REFERENCES generation_tasks(id),
    llm_config_id BIGINT REFERENCES llm_configs(id),
    prompt_template_id BIGINT REFERENCES prompt_templates(id),
    task_type VARCHAR(100) NOT NULL,
    request_summary TEXT,
    response_summary TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS export_records (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    project_id BIGINT NOT NULL REFERENCES script_projects(id),
    segment_id BIGINT REFERENCES script_segments(id),
    export_type VARCHAR(50) NOT NULL,
    file_format VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_books_user_id ON books(user_id);
CREATE INDEX IF NOT EXISTS idx_books_novel_type ON books(novel_type);
CREATE INDEX IF NOT EXISTS idx_chapters_book_id ON chapters(book_id);
CREATE INDEX IF NOT EXISTS idx_chapters_book_index ON chapters(book_id, chapter_index);
CREATE INDEX IF NOT EXISTS idx_generation_tasks_user_id ON generation_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_generation_tasks_book_id ON generation_tasks(book_id);
CREATE INDEX IF NOT EXISTS idx_script_projects_user_id ON script_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_script_projects_book_id ON script_projects(book_id);
CREATE INDEX IF NOT EXISTS idx_script_segments_project_id ON script_segments(project_id);
CREATE INDEX IF NOT EXISTS idx_llm_call_logs_task_id ON llm_call_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_task_type ON prompt_templates(task_type);
