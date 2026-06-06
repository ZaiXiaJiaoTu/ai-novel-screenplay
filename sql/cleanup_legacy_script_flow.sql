BEGIN;

ALTER TABLE llm_call_logs DROP COLUMN IF EXISTS task_id;
ALTER TABLE export_records DROP COLUMN IF EXISTS segment_id;

DELETE FROM llm_call_logs
WHERE task_type IN (
    'style_strategy_generation',
    'scene_plan_generation',
    'script_yaml_generation',
    'yaml_repair'
)
   OR prompt_template_id IN (
        SELECT id
        FROM prompt_templates
        WHERE task_type IN (
            'style_strategy_generation',
            'scene_plan_generation',
            'script_yaml_generation',
            'yaml_repair'
        )
   );

DELETE FROM prompt_template_versions
WHERE template_id IN (
    SELECT id
    FROM prompt_templates
    WHERE task_type IN (
        'style_strategy_generation',
        'scene_plan_generation',
        'script_yaml_generation',
        'yaml_repair'
    )
);

DELETE FROM prompt_templates
WHERE task_type IN (
    'style_strategy_generation',
    'scene_plan_generation',
    'script_yaml_generation',
    'yaml_repair'
);

UPDATE llm_configs
SET task_scope = NULL
WHERE task_scope ?| array[
    'style_strategy_generation',
    'scene_plan_generation',
    'script_yaml_generation',
    'yaml_repair'
];

DELETE FROM export_records
WHERE project_id IS NOT NULL
   OR export_type IN ('segment', 'project');

DELETE FROM script_episodes;
DELETE FROM script_character_profiles;
DELETE FROM script_plot_events;
DELETE FROM script_event_batches;
DELETE FROM script_projects;

DROP TABLE IF EXISTS generation_artifacts CASCADE;
DROP TABLE IF EXISTS generation_tasks CASCADE;
DROP TABLE IF EXISTS script_segments CASCADE;

COMMIT;
