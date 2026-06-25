from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Player, WordleResult


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


def test_create_result_and_reject_duplicate():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.session.add(Player(name="Ada Lovelace", phone_number="+15551234567"))
        db.session.commit()

    response = client.post(
        "/api/results",
        json={"phone_number": "+15551234567", "message": "Wordle 1466 3/6"},
    )
    assert response.status_code == 201
    assert response.get_json()["points"] == 6

    duplicate = client.post(
        "/api/results",
        json={"phone_number": "+15551234567", "message": "Wordle 1466 3/6"},
    )
    assert duplicate.status_code == 409


def test_leaderboard_endpoint_returns_ranked_rows():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.session.add_all(
            [
                Player(name="Ada Lovelace", phone_number="+15551234567"),
                Player(name="Grace Hopper", phone_number="+15557654321"),
            ]
        )
        db.session.commit()

    client.post("/api/results", json={"phone_number": "+15551234567", "message": "Wordle 1466 3/6"})
    client.post("/api/results", json={"phone_number": "+15557654321", "message": "Wordle 1466 1/6"})

    response = client.get("/api/leaderboard")

    assert response.status_code == 200
    rows = response.get_json()
    assert rows[0]["player"] == "Grace Hopper"
    assert rows[0]["total_points"] == 10


def test_twilio_sms_webhook_stores_result():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.session.add(Player(name="Ada Lovelace", phone_number="+15551234567"))
        db.session.commit()

    response = client.post(
        "/webhooks/twilio/sms",
        data={"From": "+15551234567", "Body": "Wordle 1466 3/6"},
    )

    assert response.status_code == 201
    assert response.mimetype == "application/xml"
    assert b"Saved Ada Lovelace" in response.data

    leaderboard = client.get("/api/leaderboard").get_json()
    assert leaderboard[0]["total_points"] == 6


def test_import_page_stores_pasted_results():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.session.add_all(
            [
                Player(name="Ada Lovelace", phone_number="+15551234567"),
                Player(name="Grace Hopper", phone_number="+15557654321"),
            ]
        )
        db.session.commit()

    response = client.post(
        "/import",
        data={
            "paste_text": "Ada Lovelace: Wordle 1466 3/6\nGrace Hopper\nWordle 1466 2/6",
        },
    )

    assert response.status_code == 200
    assert b"Saved" in response.data

    leaderboard = client.get("/api/leaderboard").get_json()
    assert leaderboard[0]["player"] == "Grace Hopper"
    assert leaderboard[0]["total_points"] == 8


def test_clear_history_removes_results_but_keeps_players():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        db.session.add(Player(name="Ada Lovelace", phone_number="+15551234567"))
        db.session.commit()

    client.post("/api/results", json={"phone_number": "+15551234567", "message": "Wordle 1466 3/6"})

    response = client.post("/clear-history", follow_redirects=True)

    assert response.status_code == 200
    assert b"History cleared" in response.data
    with app.app_context():
        assert Player.query.count() == 5
        assert WordleResult.query.count() == 0


def test_web_app_manifest_and_service_worker_are_available():
    app = create_app(TestConfig)
    client = app.test_client()

    manifest = client.get("/static/manifest.webmanifest")
    service_worker = client.get("/service-worker.js")

    assert manifest.status_code == 200
    assert manifest.content_type.startswith("application/manifest+json") or manifest.content_type.startswith("application/octet-stream")
    assert service_worker.status_code == 200
    assert service_worker.headers["Service-Worker-Allowed"] == "/"


def test_default_players_are_created_on_startup():
    app = create_app(TestConfig)

    with app.app_context():
        assert [player.name for player in Player.query.order_by(Player.name).all()] == [
            "Ben",
            "Cathy",
            "Megan",
            "Syd",
        ]
