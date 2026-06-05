# 剧本 YAML Schema

首期剧本 YAML 至少包含 `metadata`、`adapt_scope`、`generation_config`、`characters` 和 `scenes`。

```yaml
script:
  metadata:
    script_id: "script_001"
    project_id: "project_001"
    segment_id: "segment_001"
    source_book_id: "book_001"
    title: "长夜来信短剧版"
    segment_title: "第1章至第3章：旧信出现"
    script_type: "短剧剧本"
    style: "校园悬疑"
    compression_level: "high"
    target_duration: 5
    duration_unit: "minute"
  adapt_scope:
    type: "chapter_range"
    start_chapter: 1
    end_chapter: 3
    description: "改编第1章至第3章"
  generation_config:
    scene_density: "low"
    dialogue_ratio: "medium"
    narration_ratio: "low"
    keep_main_plot: true
    allow_remove_side_plots: true
    allow_merge_minor_characters: true
  characters:
    - name: "林川"
      role: "男主角"
      description: "敏感、冷静、执着。"
  scenes:
    - scene_id: 1
      scene_title: "旧信出现"
      source_chapters:
        - 1
      location: "教室"
      time: "傍晚"
      characters:
        - "林川"
      scene_goal: "用旧信引出主线悬念"
      conflict: "林川想忽略旧信，但信中的内容指向过去"
      action:
        - "教室里只剩下林川一个人。"
      dialogue:
        - speaker: "林川"
          line: "这是谁放的？"
          emotion: "疑惑"
      transition: "画面切至旧教学楼外。"
```

不同剧本类型可扩展 `short_drama`、`film`、`audio`、`stage` 和 `shots` 字段。
