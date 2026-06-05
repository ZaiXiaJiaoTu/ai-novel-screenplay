from app import models  # noqa: F401
from app.core.database import Base, SessionLocal, engine
from app.services.demo_seed_service import seed_demo_data


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        result = seed_demo_data(db)
    if result["created"]:
        print(f"Demo data created: book #{result['book_id']} - {result['book_title']}")
    else:
        print(f"Demo data already exists: book #{result['book_id']} - {result['book_title']}")


if __name__ == "__main__":
    main()
