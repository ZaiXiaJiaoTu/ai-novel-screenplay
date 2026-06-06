from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.chapter import Chapter
from app.models.script_adaptation import (
    ScriptCharacterProfile,
    ScriptEpisode,
    ScriptEventBatch,
    ScriptPlotEvent,
)
from app.models.script_project import ScriptProject
from app.models.user import User
from app.services.script_adaptation_service import get_yaml_schema_delta
from app.utils.chapter_parser import count_words

DEMO_USERNAME = "demo_author"
DEMO_BOOK_TITLE = "Night Rain Old Building"

DEMO_CHAPTERS = [
    {
        "title": "Chapter 1 The Letter",
        "content": (
            "Lin Chuan returns to the old building on a rainy night. "
            "An unsigned letter waits under the door and points him to a room "
            "that disappeared ten years ago."
        ),
    },
    {
        "title": "Chapter 2 The Hidden Room",
        "content": (
            "The room at the end of the fifth floor still looks untouched. "
            "Photos on the wall reveal that his father investigated the old fire."
        ),
    },
    {
        "title": "Chapter 3 The Broadcast",
        "content": (
            "A witness denies knowing the truth. When the power fails, "
            "Lin Xia's recorded voice points everyone back to the night of the rain."
        ),
    },
]


def build_demo_script_payload(book_id: int) -> dict[str, Any]:
    return {
        "script": {
            "metadata": {
                "title": f"{DEMO_BOOK_TITLE} - Episode 1",
                "episode_index": 1,
                "script_type": "short_drama",
                "target_duration": 5,
                "source_book_id": str(book_id),
            },
            "scenes": [
                {
                    "scene_id": "S1",
                    "scene_title": "Rainy Return",
                    "source_events": [1],
                    "location": "Old building entrance",
                    "time": "Night",
                    "characters": ["Lin Chuan"],
                    "action": ["Rain hits the stairs", "Lin Chuan opens the letter"],
                    "dialogue": [
                        {"speaker": "Lin Chuan", "line": "Who sent this to me now?"}
                    ],
                    "transition": "He pushes open the old door.",
                },
                {
                    "scene_id": "S2",
                    "scene_title": "The Broadcast",
                    "source_events": [2, 3],
                    "location": "Corridor",
                    "time": "Night",
                    "characters": ["Lin Chuan", "Lin Xia"],
                    "action": ["The lights go out", "A familiar voice plays"],
                    "dialogue": [
                        {"speaker": "Lin Xia", "line": "Do not believe their report."}
                    ],
                    "transition": "Lin Chuan runs toward the archive room.",
                },
            ],
        }
    }


def build_demo_plain_text(script_payload: dict[str, Any]) -> str:
    metadata = script_payload["script"]["metadata"]
    scenes = script_payload["script"]["scenes"]
    lines = [metadata["title"]]
    for scene in scenes:
        lines.append(f"{scene['scene_id']}. {scene['scene_title']}")
        for dialogue in scene["dialogue"]:
            lines.append(f"{dialogue['speaker']}: {dialogue['line']}")
    return "\n".join(lines)


def build_demo_seed_preview(book_id: int = 1) -> dict[str, Any]:
    script_payload = build_demo_script_payload(book_id)
    return {
        "book_title": DEMO_BOOK_TITLE,
        "chapter_count": len(DEMO_CHAPTERS),
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
        user = User(username=DEMO_USERNAME, nickname="Demo Author")
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
    )
    db.add(book)
    db.flush()

    for index, chapter_payload in enumerate(DEMO_CHAPTERS, start=1):
        db.add(
            Chapter(
                book_id=book.id,
                chapter_index=index,
                title=chapter_payload["title"],
                content=chapter_payload["content"],
                word_count=count_words(chapter_payload["content"]),
            )
        )
    db.flush()

    project = ScriptProject(
        user_id=user.id,
        book_id=book.id,
        project_name=f"{DEMO_BOOK_TITLE} - Demo Adaptation",
        script_type="short_drama",
        default_style="short_drama",
        default_compression_level="medium",
        default_target_duration=5,
        pacing="medium",
        scene_frequency="high",
        dialogue_density="medium",
        events_per_episode=3,
        yaml_schema_delta=get_yaml_schema_delta("short_drama"),
        status="ongoing",
    )
    db.add(project)
    db.flush()

    batch = ScriptEventBatch(
        project_id=project.id,
        book_id=book.id,
        batch_index=1,
        chapter_start_index=1,
        chapter_end_index=3,
    )
    db.add(batch)
    db.flush()
    for index, chapter in enumerate(DEMO_CHAPTERS, start=1):
        db.add(
            ScriptPlotEvent(
                project_id=project.id,
                batch_id=batch.id,
                event_index=index,
                content=chapter["content"],
                source_chapter_start=index,
                source_chapter_end=index,
                locked=True,
            )
        )

    db.add(
        ScriptCharacterProfile(
            project_id=project.id,
            name="Lin Chuan",
            profile="A young man pulled back into a sealed old case.",
        )
    )
    script_payload = build_demo_script_payload(book.id)
    script_yaml = yaml.safe_dump(script_payload, allow_unicode=True, sort_keys=False)
    plain_text = build_demo_plain_text(script_payload)
    db.add(
        ScriptEpisode(
            project_id=project.id,
            episode_index=1,
            title="Episode 1",
            event_ids=[1, 2, 3],
            yaml_content=script_yaml,
            plain_text_content=plain_text,
            status="completed",
        )
    )

    db.commit()
    return {"created": True, "book_id": book.id, "book_title": book.title, "project_id": project.id}
