from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.base import Base
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.db.session import engine

def init_db(db: Session) -> None:
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create admin user if not exists
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        admin = User(
            email="admin@example.com",
            name="Admin",
            hashed_password=get_password_hash("admin123"),
            is_superuser=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    # Create test user if not exists
    test_user = db.query(User).filter(User.email == "test@example.com").first()
    if not test_user:
        test_user = User(
            email="test@example.com",
            name="Test User",
            hashed_password=get_password_hash("test123"),
            is_superuser=False
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user) 