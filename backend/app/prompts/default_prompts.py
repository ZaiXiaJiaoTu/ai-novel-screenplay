DEFAULT_PROMPT_TEMPLATES = [
    {
        "template_name": "Default style strategy generation",
        "task_type": "style_strategy_generation",
        "system_prompt": (
            "You are a professional screenplay adaptation planner. "
            "Return concise Chinese guidance only."
        ),
        "user_prompt_template": (
            "Generate an adaptation style strategy.\n"
            "Book title: {book_title}\n"
            "Adapt scope: {adapt_scope}\n"
            "Generation config: {generation_config}\n"
            "Chapters: {chapters}\n"
            "Include narrative style, pacing, dialogue tone, visual focus, and adaptation notes."
        ),
        "output_format": "text",
        "variables": ["book_title", "adapt_scope", "generation_config", "chapters"],
        "enabled": True,
    },
    {
        "template_name": "Default scene plan generation",
        "task_type": "scene_plan_generation",
        "system_prompt": (
            "You are a professional screenplay planner. "
            "Break novel chapters into filmable scenes."
        ),
        "user_prompt_template": (
            "Create a scene plan.\n"
            "Book title: {book_title}\n"
            "Adapt scope: {adapt_scope}\n"
            "Generation config: {generation_config}\n"
            "Style strategy: {style_strategy}\n"
            "Chapters: {chapters}\n"
            "For each scene include title, location, time, characters, goal, conflict, and turn."
        ),
        "output_format": "text",
        "variables": [
            "book_title",
            "adapt_scope",
            "generation_config",
            "style_strategy",
            "chapters",
        ],
        "enabled": True,
    },
    {
        "template_name": "Default script YAML generation",
        "task_type": "script_yaml_generation",
        "system_prompt": (
            "You are a professional screenplay writer. "
            "Return YAML only, without Markdown fences or extra explanation."
        ),
        "user_prompt_template": (
            "Generate screenplay YAML.\n"
            "Book title: {book_title}\n"
            "Adapt scope: {adapt_scope}\n"
            "Generation config: {generation_config}\n"
            "Style strategy: {style_strategy}\n"
            "Scene plan: {scene_plan}\n"
            "Chapters: {chapters}\n"
            "The top-level field must be script. Include metadata, adapt_scope, "
            "generation_config, characters, and scenes."
        ),
        "output_format": "yaml",
        "variables": [
            "book_title",
            "adapt_scope",
            "generation_config",
            "style_strategy",
            "scene_plan",
            "chapters",
        ],
        "enabled": True,
    },
    {
        "template_name": "Default YAML repair",
        "task_type": "yaml_repair",
        "system_prompt": "You repair YAML. Return repaired YAML only.",
        "user_prompt_template": (
            "The following YAML failed to parse. Repair formatting without changing business meaning.\n"
            "Error: {error_message}\n"
            "Original YAML: {raw_yaml}\n"
        ),
        "output_format": "yaml",
        "variables": ["error_message", "raw_yaml"],
        "enabled": True,
    },
]
