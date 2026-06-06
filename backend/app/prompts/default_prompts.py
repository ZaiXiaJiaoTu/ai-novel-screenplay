DEFAULT_PROMPT_TEMPLATES = [
    {
        "template_name": "Default plot event split generation",
        "task_type": "plot_event_split_generation",
        "system_prompt": (
            "你是中文小说改编剧本的剧情整理助手。必须只依据用户提供的小说章节内容输出，"
            "禁止引入原文没有出现的人物、地点、世界观、作品设定或外部 IP。"
            "只返回合法 JSON，不要返回 Markdown 代码块或解释文字。"
        ),
        "user_prompt_template": (
            "小说名称：{book_title}\n"
            "改编参数：{adaptation_config}\n"
            "已有结构化人物事实：{existing_characters}\n"
            "本批章节：{chapters}\n"
            "输出契约：{output_contract}\n\n"
            "任务：\n"
            "1. 将本批章节拆成若干剧情事件，剧情事件必须简洁、准确，使用中文。\n"
            "2. 识别每个剧情事件涉及的人物，并对照已有结构化人物事实。\n"
            "3. characters 只输出本批章节带来的新增事实或状态变化，禁止输出完整人物介绍，禁止重复已有事实。\n"
            "4. 不得写哈利波特、霍格沃茨、魔法学院等原文未出现的设定；也不得改写成其他作品。\n\n"
            "返回 JSON 字段：\n"
            "- events：按剧情顺序排列的数组，每项包含 content、source_chapter_start、source_chapter_end。\n"
            "- characters：数组，每项包含 name、facts；facts 每项包含 fact_type、content。"
        ),
        "output_format": "json",
        "variables": [
            "book_title",
            "adaptation_config",
            "existing_characters",
            "chapters",
            "output_contract",
        ],
        "enabled": True,
    },
    {
        "template_name": "Default script episode generation",
        "task_type": "script_episode_generation",
        "system_prompt": (
            "你是中文剧本改编编剧。必须只依据用户提供的剧情事件、人物档案和原文章节生成一集剧本，"
            "禁止引入原文没有出现的人物、地点、世界观、作品设定或外部 IP。"
            "只返回合法 YAML，不要返回 Markdown 代码块或解释文字。"
        ),
        "user_prompt_template": (
            "小说名称：{book_title}\n"
            "改编参数：{adaptation_config}\n"
            "本集使用的剧情事件：{events}\n"
            "人物档案：{characters}\n"
            "对应原文章节：{chapters}\n"
            "YAML Schema 差分：{yaml_schema_delta}\n\n"
            "要求：\n"
            "1. 生成且只生成一集剧本，必须使用中文。\n"
            "2. 只能使用本集剧情事件、人物档案和对应原文章节中的信息。\n"
            "3. 不得写哈利波特、霍格沃茨、魔法学院等原文未出现的设定；也不得改写成其他作品。\n"
            "4. metadata 中必须包含 source_book_title，值必须等于小说名称。\n"
            "5. scenes 中每个场景包含 scene_id、scene_title、source_events、location、time、characters、action、dialogue、transition。\n"
            "6. dialogue 数组每项包含 speaker、line。\n"
            "7. 按改编类型、单集时长、剧情节奏、场景切换频率、对话密度控制输出。"
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
