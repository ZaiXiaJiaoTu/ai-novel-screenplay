# 剧本 YAML 设计文档

## 1. 根结构

剧集 YAML 固定以 `script` 为根节点：

```yaml
script:
  metadata: {}
  scenes: []
```

后端会在生成和保存时规范化 `metadata`，确保关键字段稳定。模型可以输出额外场景字段，但前端中文表单主要维护下列标准字段。

## 2. metadata

`metadata` 固定包含以下字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| format | string | 剧集格式，按改编类型派生 |
| title | string | 本集标题，只写剧情主题，不带小说名和集数 |
| episode_number | integer | 系统剧集序号 |
| source_book_title | string | 来源小说名 |
| adaptation_type | string | tv/short_drama/animation/audio_drama |
| episode_duration | integer | 单集目标时长，单位分钟 |
| pacing | string | fast/medium/slow |
| scene_frequency | string | high/medium/low |
| dialogue_density | string | high/medium/low |

改编类型与 `format` 对应：

| adaptation_type | format |
| --- | --- |
| tv | episode |
| short_drama | short_drama_episode |
| animation | animation_episode |
| audio_drama | audio_drama_episode |

标题规则：

- 正确：`启程·诺丁城`
- 正确：`废武魂与先天满魂力`
- 错误：`斗罗大陆 第1集：废武魂与先天满魂力`
- 错误：`第1集 启程·诺丁城`

## 3. scenes

`scenes` 是场景数组。每个场景标准字段如下：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| scene_id | string/integer | 场景编号 |
| scene_title | string | 场景标题 |
| source_events | integer[] | 对应剧情事件的全剧本 event_index |
| location | string | 地点 |
| time | string | 时间 |
| characters | string[] | 出场人物 |
| action | string[] | 动作描写，每项一条 |
| dialogue | object[] | 对白 |
| transition | string | 转场 |

`source_events` 必须使用剧情事件拆分模块中的全局 `event_index`，不能按本集重新从 1 编号。

## 4. dialogue

```yaml
dialogue:
  - speaker: 唐三
    line: 我不会放弃。
```

字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| speaker | string | 说话人 |
| line | string | 台词 |

## 5. 完整示例

```yaml
script:
  metadata:
    format: animation_episode
    title: 启程·诺丁城
    episode_number: 6
    source_book_title: 斗罗大陆
    adaptation_type: animation
    episode_duration: 24
    pacing: medium
    scene_frequency: medium
    dialogue_density: medium
  scenes:
    - scene_id: 1
      scene_title: 武魂觉醒
      source_events:
        - 17
      location: 圣魂村武魂殿
      time: 白天
      characters:
        - 唐三
        - 素云涛
      action:
        - 唐三站在觉醒阵中央，蓝银草在掌心浮现。
        - 素云涛原本失望，却被水晶球爆发出的光芒震住。
      dialogue:
        - speaker: 素云涛
          line: 蓝银草，却是先天满魂力。
        - speaker: 唐三
          line: 这意味着我还有机会。
      transition: 镜头切向通往诺丁城的道路。
```

## 6. TXT 渲染规则

TXT 导出由后端从 YAML 渲染，主要规则：

- 首行使用 `metadata.title`。
- 展示来源小说、集数、目标时长。
- 每个场景渲染为“场景 X：标题”。
- 动作描写按“动作：”分行输出。
- 对白按“人物：台词”输出。
- 转场按“转场：内容”输出。
