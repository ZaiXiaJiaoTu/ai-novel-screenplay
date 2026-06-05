DEFAULT_PROMPT_TEMPLATES = [
    {
        "template_name": "默认故事设定档案生成模板",
        "task_type": "story_profile_generation",
        "system_prompt": (
            "你是小说改编策划助手。你必须只输出 JSON，不要输出 Markdown 代码块或额外解释。"
        ),
        "user_prompt_template": (
            "请根据以下小说信息生成故事设定档案 JSON。\n"
            "作品标题：{{book_title}}\n"
            "小说篇幅类型：{{novel_type}}\n"
            "章节内容：{{chapters}}\n\n"
            "JSON 字段必须包含：title、genre、overview、world_setting、main_conflict、"
            "characters、relationships、key_events、chapter_outlines、clues、tone、locked_settings。\n"
            "characters、relationships、key_events、chapter_outlines、clues、locked_settings 必须是数组。"
        ),
        "output_format": "json",
        "variables": ["book_title", "novel_type", "chapters"],
        "enabled": True,
    },
    {
        "template_name": "默认风格策略生成模板",
        "task_type": "style_strategy_generation",
        "system_prompt": "你是专业剧本改编策划，擅长把小说改编为结构清晰、风格统一的剧本。",
        "user_prompt_template": (
            "请根据以下信息生成剧本改编风格策略，输出简洁中文说明。\n"
            "作品标题：{{book_title}}\n"
            "改编范围：{{adapt_scope}}\n"
            "生成配置：{{generation_config}}\n"
            "章节内容：{{chapters}}\n"
            "请包含叙事风格、节奏、对白风格、视觉/听觉重点和改编注意事项。"
        ),
        "output_format": "text",
        "variables": ["book_title", "adapt_scope", "generation_config", "chapters"],
        "enabled": True,
    },
    {
        "template_name": "默认场景规划生成模板",
        "task_type": "scene_plan_generation",
        "system_prompt": "你是专业剧本统筹，擅长将小说章节拆解为可拍摄、可表演的场景。",
        "user_prompt_template": (
            "请根据以下信息规划剧本场景，输出中文结构化说明。\n"
            "作品标题：{{book_title}}\n"
            "改编范围：{{adapt_scope}}\n"
            "生成配置：{{generation_config}}\n"
            "风格策略：{{style_strategy}}\n"
            "章节内容：{{chapters}}\n"
            "请列出每个场景的标题、地点、时间、出场人物、目标、冲突和转场。"
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
        "template_name": "默认剧本 YAML 生成模板",
        "task_type": "script_yaml_generation",
        "system_prompt": (
            "你是专业剧本创作助手。你必须只输出 YAML，不要输出 Markdown 代码块或额外解释。"
        ),
        "user_prompt_template": (
            "请生成符合以下结构的剧本 YAML。\n"
            "作品标题：{{book_title}}\n"
            "改编范围：{{adapt_scope}}\n"
            "生成配置：{{generation_config}}\n"
            "风格策略：{{style_strategy}}\n"
            "场景规划：{{scene_plan}}\n"
            "章节内容：{{chapters}}\n\n"
            "必须包含顶层字段 script，script 下包含 metadata、adapt_scope、generation_config、characters、scenes。\n"
            "scenes 中每个场景至少包含 scene_id、scene_title、source_chapters、location、time、characters、scene_goal、conflict、action、dialogue、transition。\n"
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
        "template_name": "默认 YAML 修复模板",
        "task_type": "yaml_repair",
        "system_prompt": "你是 YAML 格式修复助手。你必须只输出修复后的 YAML。",
        "user_prompt_template": (
            "以下 YAML 解析失败，请在不改变业务含义的前提下修复格式并只输出 YAML。\n"
            "错误信息：{{error_message}}\n"
            "原始内容：{{raw_yaml}}\n"
        ),
        "output_format": "yaml",
        "variables": ["error_message", "raw_yaml"],
        "enabled": True,
    },
]
