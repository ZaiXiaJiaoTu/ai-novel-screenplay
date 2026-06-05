from datetime import datetime
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.chapter import Chapter
from app.models.chapter_summary import ChapterSummary
from app.models.generation_task import GenerationArtifact, GenerationTask
from app.models.script_project import ScriptProject
from app.models.script_segment import ScriptSegment
from app.models.story_profile import StoryProfile
from app.models.user import User
from app.utils.chapter_parser import count_words

DEMO_USERNAME = "demo_author"
DEMO_BOOK_TITLE = "夜雨旧楼"

DEMO_CHAPTERS = [
    {
        "title": "第一章 旧楼来信",
        "content": (
            "林川在雨夜回到青禾旧楼。门缝里夹着一封没有署名的信，"
            "信纸上只有一句话：十年前失踪的房间，今晚会重新开门。"
            "他以为这是恶作剧，却在楼梯间听见了妹妹林夏的录音。"
        ),
    },
    {
        "title": "第二章 消失的房间",
        "content": (
            "林川按信上的地址来到五楼尽头，却发现走廊比记忆中多出一扇铁门。"
            "门后的房间保持着十年前的样子，墙上贴满他父亲当年调查旧楼火灾的照片。"
            "照片背面写着同一个名字：周砚。"
        ),
    },
    {
        "title": "第三章 雨声里的证词",
        "content": (
            "周砚承认自己曾参与封存旧楼档案，但否认与林夏失踪有关。"
            "就在两人争执时，整栋楼突然断电，广播里响起林夏的声音。"
            "她说真正的线索不在房间里，而在每个幸存者选择遗忘的那场雨里。"
        ),
    },
]

DEMO_SUMMARIES = [
    {
        "summary": "林川收到神秘来信，回到青禾旧楼，并听见失踪妹妹的录音。",
        "characters": ["林川", "林夏"],
        "key_events": ["神秘信件出现", "旧楼录音触发主线"],
        "locations": ["青禾旧楼"],
        "clues": ["无署名信件", "林夏录音"],
        "emotion_changes": ["怀疑", "震惊"],
    },
    {
        "summary": "林川发现不存在于记忆中的房间，并找到父亲调查旧楼火灾的照片。",
        "characters": ["林川", "周砚"],
        "key_events": ["隐藏房间出现", "周砚名字浮出水面"],
        "locations": ["五楼尽头房间"],
        "clues": ["旧楼火灾照片", "周砚姓名"],
        "emotion_changes": ["不安", "追查"],
    },
    {
        "summary": "周砚否认与失踪案有关，林夏的广播留言把真相指向十年前雨夜。",
        "characters": ["林川", "周砚", "林夏"],
        "key_events": ["周砚现身", "广播留言揭示新方向"],
        "locations": ["青禾旧楼"],
        "clues": ["封存档案", "雨夜证词"],
        "emotion_changes": ["对峙", "急迫"],
    },
]

DEMO_STORY_PROFILE = {
    "title": DEMO_BOOK_TITLE,
    "genre": "悬疑短篇",
    "overview": "一名青年收到失踪妹妹的线索，回到旧楼追查十年前被封存的火灾与失踪案。",
    "world_setting": "现代城市旧楼，雨夜、封存档案和幸存者证词交织出悬疑氛围。",
    "main_conflict": "林川必须在幸存者的沉默和妹妹留下的线索之间找出真相。",
    "characters": [
        {"name": "林川", "role": "主角", "goal": "找出妹妹林夏失踪真相"},
        {"name": "林夏", "role": "关键失踪者", "goal": "通过录音引导哥哥追查旧案"},
        {"name": "周砚", "role": "知情人", "goal": "隐藏自己参与封存档案的过去"},
    ],
    "relationships": [
        {"from": "林川", "to": "林夏", "relation": "兄妹"},
        {"from": "林川", "to": "周砚", "relation": "追问者与知情人"},
    ],
    "key_events": ["收到神秘来信", "发现消失房间", "广播揭示雨夜证词"],
    "chapter_outlines": [
        {"chapter_index": index + 1, "title": chapter["title"], "summary": summary["summary"]}
        for index, (chapter, summary) in enumerate(zip(DEMO_CHAPTERS, DEMO_SUMMARIES, strict=True))
    ],
    "clues": ["无署名信件", "林夏录音", "旧楼火灾照片", "封存档案"],
    "tone": "雨夜悬疑",
    "locked_settings": [{"name": "林夏失踪时间", "value": "十年前雨夜"}],
}


def build_demo_script_payload(book_id: int) -> dict[str, Any]:
    return {
        "script": {
            "metadata": {
                "title": "夜雨旧楼 - 第一集",
                "segment_title": "第一集：旧楼来信",
                "script_type": "short_drama",
                "style": "雨夜悬疑",
                "compression_level": "medium",
                "target_duration": 5,
                "source_book_id": str(book_id),
            },
            "scenes": [
                {
                    "scene_id": "S1",
                    "scene_title": "雨夜回楼",
                    "source_chapters": [1],
                    "location": "青禾旧楼门口",
                    "time": "夜",
                    "characters": ["林川"],
                    "scene_goal": "建立悬疑开端并引出神秘信件。",
                    "conflict": "林川不愿面对旧楼记忆，却被信件逼回现场。",
                    "action": ["林川撑伞停在旧楼前", "门缝中的信被雨水打湿"],
                    "dialogue": [{"speaker": "林川", "line": "谁会在这个时候寄这种信？"}],
                    "transition": "林川推门进入旧楼。",
                },
                {
                    "scene_id": "S2",
                    "scene_title": "消失房间",
                    "source_chapters": [2],
                    "location": "五楼尽头",
                    "time": "夜",
                    "characters": ["林川"],
                    "scene_goal": "揭示不存在于记忆中的房间和父亲调查线索。",
                    "conflict": "房间证据证明旧案并未结束。",
                    "action": ["铁门缓慢打开", "照片墙露出周砚的名字"],
                    "dialogue": [{"speaker": "林川", "line": "爸当年到底查到了什么？"}],
                    "transition": "楼道广播突然响起。",
                },
                {
                    "scene_id": "S3",
                    "scene_title": "广播里的妹妹",
                    "source_chapters": [3],
                    "location": "旧楼走廊",
                    "time": "夜",
                    "characters": ["林川", "林夏"],
                    "scene_goal": "用林夏录音推动主角继续追查雨夜真相。",
                    "conflict": "林夏的声音证明她可能早已预见危险。",
                    "action": ["整栋楼断电", "广播中传出林夏的声音"],
                    "dialogue": [{"speaker": "林夏", "line": "哥，别相信他们说的火灾结论。"}],
                    "transition": "林川冲向档案室。",
                },
            ],
        }
    }


def build_demo_plain_text(script_payload: dict[str, Any]) -> str:
    metadata = script_payload["script"]["metadata"]
    scenes = script_payload["script"]["scenes"]
    lines = [metadata["segment_title"]]
    for scene in scenes:
        lines.append(f"{scene['scene_id']}. {scene['scene_title']}")
        for dialogue in scene["dialogue"]:
            lines.append(f"{dialogue['speaker']}：{dialogue['line']}")
    return "\n".join(lines)


def build_demo_seed_preview(book_id: int = 1) -> dict[str, Any]:
    script_payload = build_demo_script_payload(book_id)
    return {
        "book_title": DEMO_BOOK_TITLE,
        "chapter_count": len(DEMO_CHAPTERS),
        "summary_count": len(DEMO_SUMMARIES),
        "script_scene_count": len(script_payload["script"]["scenes"]),
        "script_yaml": yaml.safe_dump(script_payload, allow_unicode=True, sort_keys=False),
    }


def seed_demo_data(db: Session) -> dict[str, Any]:
    existing_book = db.scalar(
        select(Book).where(Book.title == DEMO_BOOK_TITLE, Book.is_deleted.is_(False))
    )
    if existing_book is not None:
        return {"created": False, "book_id": existing_book.id, "book_title": existing_book.title}

    user = db.scalar(select(User).where(User.username == DEMO_USERNAME, User.is_deleted.is_(False)))
    if user is None:
        user = User(username=DEMO_USERNAME, nickname="演示作者")
        db.add(user)
        db.flush()

    book = Book(
        user_id=user.id,
        title=DEMO_BOOK_TITLE,
        original_filename="demo_novel.txt",
        source_type="demo_seed",
        novel_type="short",
        word_count=sum(count_words(chapter["content"]) for chapter in DEMO_CHAPTERS),
        chapter_count=len(DEMO_CHAPTERS),
        preprocess_status="completed",
        story_profile_status="confirmed",
    )
    db.add(book)
    db.flush()

    chapters: list[Chapter] = []
    for index, chapter_payload in enumerate(DEMO_CHAPTERS, start=1):
        chapter = Chapter(
            book_id=book.id,
            chapter_index=index,
            title=chapter_payload["title"],
            content=chapter_payload["content"],
            word_count=count_words(chapter_payload["content"]),
        )
        db.add(chapter)
        chapters.append(chapter)
    db.flush()

    for chapter, summary_payload in zip(chapters, DEMO_SUMMARIES, strict=True):
        db.add(ChapterSummary(book_id=book.id, chapter_id=chapter.id, **summary_payload))

    db.add(StoryProfile(book_id=book.id, confirmed=True, version=1, **DEMO_STORY_PROFILE))

    project = ScriptProject(
        user_id=user.id,
        book_id=book.id,
        project_name="夜雨旧楼 - 演示短剧",
        script_type="short_drama",
        default_style="雨夜悬疑",
        default_compression_level="medium",
        default_target_duration=5,
        status="ongoing",
    )
    db.add(project)
    db.flush()

    task = GenerationTask(
        user_id=user.id,
        book_id=book.id,
        script_project_id=project.id,
        task_type="script_generation",
        status="completed",
        current_step="completed",
        adapt_scope={"type": "chapter_range", "start_chapter": 1, "end_chapter": 3},
        generation_config={
            "script_type": "short_drama",
            "style": "雨夜悬疑",
            "compression_level": "medium",
            "target_duration": 5,
        },
        finished_at=datetime.utcnow(),
    )
    db.add(task)
    db.flush()

    script_payload = build_demo_script_payload(book.id)
    script_yaml = yaml.safe_dump(script_payload, allow_unicode=True, sort_keys=False)
    plain_text = build_demo_plain_text(script_payload)
    db.add(
        ScriptSegment(
            project_id=project.id,
            book_id=book.id,
            segment_name="第一集：旧楼来信",
            adapt_scope=task.adapt_scope,
            style_source="inherit_project",
            style="雨夜悬疑",
            compression_level="medium",
            target_duration=5,
            actual_word_count=count_words(plain_text),
            scene_count=len(script_payload["script"]["scenes"]),
            yaml_content=script_yaml,
            plain_text_content=plain_text,
            status="completed",
        )
    )
    db.add(
        GenerationArtifact(
            task_id=task.id,
            artifact_type="script_yaml",
            content=script_payload,
            version=1,
            editable=True,
        )
    )

    db.commit()
    return {"created": True, "book_id": book.id, "book_title": book.title, "project_id": project.id}
