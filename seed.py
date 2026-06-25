from __future__ import annotations

from app import create_app
from app.extensions import db
from app.models import Player


PLAYERS = [
    ("Megan", "+15550000001"),
    ("Ben", "+15550000002"),
    ("Syd", "+15550000003"),
    ("Cathy", "+15550000004"),
]

def seed() -> None:
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        for name, phone_number in PLAYERS:
            player = Player(name=name, phone_number=phone_number)
            db.session.add(player)

        db.session.commit()


if __name__ == "__main__":
    seed()
    print("Players loaded. Leaderboard results cleared.")
