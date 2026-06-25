from __future__ import annotations

from pathlib import Path

from flask import Flask

from .config import Config
from .defaults import DEFAULT_PLAYERS
from .extensions import db
from .models import Player
from .routes import api_bp, dashboard_bp, webhooks_bp


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(api_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(dashboard_bp)

    with app.app_context():
        db.create_all()
        _create_default_players()

    return app


def _create_default_players() -> None:
    if Player.query.count() > 0:
        return

    for name, phone_number in DEFAULT_PLAYERS:
        db.session.add(Player(name=name, phone_number=phone_number))
    db.session.commit()
