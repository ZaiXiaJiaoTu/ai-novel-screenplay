DEFAULT_PROMPT_TEMPLATES = [
    {
        "template_name": "Default plot event split generation",
        "task_type": "plot_event_split_generation",
        "system_prompt": (
            "You split novel chapters for screenplay adaptation. Return JSON only. "
            "Each plot event must be concise and accurate. Also extract or update character profiles."
        ),
        "user_prompt_template": (
            "Book title: {book_title}\n"
            "Adaptation config: {adaptation_config}\n"
            "Chapters: {chapters}\n"
            "Output contract: {output_contract}\n"
            "Return JSON with fields: events, characters. "
            "events is an ordered list of objects with content, source_chapter_start, source_chapter_end. "
            "characters is an ordered list of objects with name and profile."
        ),
        "output_format": "json",
        "variables": ["book_title", "adaptation_config", "chapters", "output_contract"],
        "enabled": True,
    },
    {
        "template_name": "Default script episode generation",
        "task_type": "script_episode_generation",
        "system_prompt": (
            "You generate one episode screenplay. Return YAML only, without Markdown fences. "
            "Respect the adaptation type, duration, pacing, scene switching frequency, dialogue density, "
            "and YAML schema delta."
        ),
        "user_prompt_template": (
            "Book title: {book_title}\n"
            "Adaptation config: {adaptation_config}\n"
            "Selected plot events: {events}\n"
            "Character profiles: {characters}\n"
            "Source chapters: {chapters}\n"
            "YAML schema delta: {yaml_schema_delta}\n"
            "Generate exactly one episode. Use only the selected plot events."
        ),
        "output_format": "yaml",
        "variables": [
            "book_title",
            "adaptation_config",
            "events",
            "characters",
            "chapters",
            "yaml_schema_delta",
        ],
        "enabled": True,
    },
]
