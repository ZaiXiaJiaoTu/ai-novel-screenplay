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
            "已有结构化人物特征：{existing_characters}\n"
            "本批章节：{chapters}\n"
            "输出契约：{output_contract}\n\n"
            "任务：\n"
            "1. 将本批章节拆成若干剧情事件，剧情事件必须简洁、准确，使用中文。\n"
            "2. 识别每个剧情事件涉及的人物，并对照已有结构化人物特征。\n"
            "3. characters 只输出本批章节带来的关键特征、能力变化、人物性格或关系变化，禁止输出完整人物介绍，禁止重复已有特征。\n"
            "4. 不得写哈利波特、霍格沃茨、魔法学院等原文未出现的设定；也不得改写成其他作品。\n\n"
            "返回 JSON 字段：\n"
            "- events：按剧情顺序排列的数组，每项包含 content、source_chapter_start、source_chapter_end。\n"
            "- characters：数组，每项包含 name、traits；traits 每项包含 trait_type、content。"
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
            "本集集数：{episode_number}\n"
            "本集使用的剧情事件：{events}\n"
            "人物档案：{characters}\n"
            "对应原文章节：{chapters}\n"
            "YAML Schema 差分：{yaml_schema_delta}\n\n"
            "要求：\n"
            "1. 生成且只生成一集剧本，必须使用中文。\n"
            "2. 只能使用本集剧情事件、人物档案和对应原文章节中的信息。\n"
            "3. 不得写哈利波特、霍格沃茨、魔法学院等原文未出现的设定；也不得改写成其他作品。\n"
            "4. metadata 必须固定包含且只按以下含义填写：format、title、episode_number、source_book_title、adaptation_type、episode_duration、pacing、scene_frequency、dialogue_density。\n"
            "5. episode_number 必须等于“本集集数”，source_book_title 必须等于小说名称，其他参数必须来自改编参数。\n"
            "6. title 是本集中文标题，只写剧情主题，例如“启程·诺丁城”或“废武魂与先天满魂力”；不要包含小说名、剧名、“第几集”、Episode 等集数前缀。\n"
            "7. scenes 中每个场景包含 scene_id、scene_title、source_events、location、time、characters、action、dialogue、transition。\n"
            "8. source_events 必须填写剧情事件拆分模块中的全剧本事件序号 event_index，不要按本集重新从 1 编号。\n"
            "9. dialogue 数组每项包含 speaker、line。\n"
            "10. 按改编类型、单集时长、剧情节奏、场景切换频率、对话密度控制输出。"
        ),
        "output_format": "yaml",
        "variables": [
            "book_title",
            "adaptation_config",
            "episode_number",
            "events",
            "characters",
            "chapters",
            "yaml_schema_delta",
        ],
        "enabled": True,
    },
    {
        "template_name": "Default character profile consolidation",
        "task_type": "character_profile_consolidation",
        "system_prompt": (
            "你是中文剧本人物小传编辑。只根据输入的人物拆分输出进行整合，"
            "不要引入原文没有的信息。只返回合法 JSON，不要返回 Markdown。"
        ),
        "user_prompt_template": (
            "小说名称：{book_title}\n"
            "人物拆分输出：{characters}\n\n"
            "任务：\n"
            "将每个人物的碎片化特征整合为简洁人物档案，只保留关键特征、性格、能力、关系和当前状态。\n"
            "删除重复表达和语义相同内容，不要写成长篇百科。\n\n"
            "返回 JSON：\n"
            "{\n"
            "  \"characters\": [\n"
            "    {\"name\": \"人物名\", \"profile\": \"整合后人物档案\"}\n"
            "  ]\n"
            "}"
        ),
        "output_format": "json",
        "variables": ["book_title", "characters"],
        "enabled": True,
    },
]
