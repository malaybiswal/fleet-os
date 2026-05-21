from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_firebase_uid(self, firebase_uid: str) -> User | None:
        return (
            self.db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )

    def create_user(
        self,
        *,
        firebase_uid: str,
        email: str,
        name: str | None,
        fleet_id: int,
        role: str = "admin",
    ) -> User:
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            name=name,
            fleet_id=fleet_id,
            role=role,
        )
        self.db.add(user)
        self.db.flush()
        return user