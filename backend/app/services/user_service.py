from sqlalchemy.orm import Session

from app.models.fleet import Fleet
from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def get_or_create_user(
        self,
        *,
        firebase_uid: str,
        email: str,
        name: str | None = None,
    ) -> User:
        existing_user = self.user_repository.get_by_firebase_uid(
            firebase_uid
        )

        if existing_user:
            return existing_user

        existing_user = self.user_repository.get_by_email(email)

        if existing_user:
            existing_user.firebase_uid = firebase_uid
            if name and not existing_user.name:
                existing_user.name = name
            self.db.commit()
            self.db.refresh(existing_user)
            return existing_user

        fleet = Fleet(
            name=f"{email.split('@')[0]} Fleet",
        )

        self.db.add(fleet)
        self.db.flush()

        user = self.user_repository.create_user(
            firebase_uid=firebase_uid,
            email=email,
            name=name,
            fleet_id=fleet.id,
            role="admin",
        )

        self.db.commit()
        self.db.refresh(user)

        return user
