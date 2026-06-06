BEGIN;

DROP TABLE IF EXISTS chapter_summaries CASCADE;
DROP TABLE IF EXISTS story_profiles CASCADE;
ALTER TABLE books DROP COLUMN IF EXISTS story_profile_status;

UPDATE llm_call_logs
SET prompt_template_id = NULL
WHERE prompt_template_id IN (
    SELECT id
    FROM prompt_templates
    WHERE task_type IN ('story_profile_generation', 'chapter_summary_generation')
);

DELETE FROM prompt_template_versions
WHERE template_id IN (
    SELECT id
    FROM prompt_templates
    WHERE task_type IN ('story_profile_generation', 'chapter_summary_generation')
);

DELETE FROM prompt_templates
WHERE task_type IN ('story_profile_generation', 'chapter_summary_generation');

COMMIT;
