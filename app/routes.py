from __future__ import annotations

from html import escape

from flask import Blueprint, Response, current_app, jsonify, redirect, render_template, request, send_from_directory, url_for
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Player, WordleResult
from .services.importer import extract_import_candidates
from .services.leaderboard import build_leaderboard
from .services.wordle import WordleParseError, parse_wordle_message


api_bp = Blueprint("api", __name__, url_prefix="/api")
dashboard_bp = Blueprint("dashboard", __name__)
webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")


@api_bp.post("/results")
def create_result():
    payload = request.get_json(silent=True) or {}
    phone_number = payload.get("phone_number")
    message = payload.get("message")

    if not phone_number or not message:
        return jsonify({"error": "phone_number and message are required"}), 400

    result_payload, status_code = _store_wordle_result(phone_number, message)
    return jsonify(result_payload), status_code


@webhooks_bp.post("/twilio/sms")
def twilio_sms_webhook():
    phone_number = request.form.get("From")
    message = request.form.get("Body")

    if not phone_number or not message:
        return _twiml("Missing sender or message body."), 400

    payload, status_code = _store_wordle_result(phone_number, message)
    if status_code == 201:
        return _twiml(
            f"Saved {payload['player']}'s Wordle {payload['wordle_number']} "
            f"{payload['raw_score']} for {payload['points']} points."
        ), 201

    return _twiml(payload["error"]), status_code


def _store_wordle_result(phone_number: str, message: str) -> tuple[dict, int]:
    player = Player.query.filter_by(phone_number=phone_number).one_or_none()
    if player is None:
        return {"error": "No player found for phone number"}, 404

    try:
        parsed = parse_wordle_message(message)
    except WordleParseError as exc:
        return {"error": str(exc)}, 400

    result = WordleResult(
        player_id=player.id,
        wordle_number=parsed.wordle_number,
        raw_score=parsed.raw_score,
        guesses=parsed.guesses,
        points=parsed.points,
    )
    db.session.add(result)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "Duplicate submission for this player and Wordle number"}, 409

    return {
        "id": result.id,
        "player": player.name,
        "wordle_number": result.wordle_number,
        "raw_score": result.raw_score,
        "guesses": result.guesses,
        "points": result.points,
        "submitted_at": result.submitted_at.isoformat(),
    }, 201


def _twiml(message: str) -> Response:
    escaped_message = escape(message)
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>{escaped_message}</Message>
</Response>"""
    return Response(body, mimetype="application/xml")


@api_bp.get("/leaderboard")
def leaderboard_api():
    rows = build_leaderboard(Player.query.order_by(Player.name).all())
    return jsonify([row.as_dict() for row in rows])


@dashboard_bp.get("/")
def dashboard():
    players = Player.query.order_by(Player.name).all()
    rows = build_leaderboard(players)
    results = WordleResult.query.all()
    latest_wordle = max((result.wordle_number for result in results), default=None)
    return render_template(
        "dashboard.html",
        rows=rows,
        total_players=len(players),
        total_results=len(results),
        latest_wordle=latest_wordle,
        leader=rows[0] if rows and results else None,
        history_cleared=request.args.get("cleared") == "1",
    )


@dashboard_bp.post("/clear-history")
def clear_history():
    WordleResult.query.delete()
    db.session.commit()
    return redirect(url_for("dashboard.dashboard", cleared="1"))


@dashboard_bp.get("/service-worker.js")
def service_worker():
    response = send_from_directory(current_app.static_folder, "service-worker.js")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


@dashboard_bp.route("/import", methods=["GET", "POST"])
def import_results():
    players = Player.query.order_by(Player.name).all()
    import_summary = None
    paste_text = ""

    if request.method == "POST":
        paste_text = request.form.get("paste_text", "")
        import_summary = []
        for candidate in extract_import_candidates(paste_text, players):
            if candidate.player is None:
                import_summary.append(
                    {
                        "status": "Skipped",
                        "message": candidate.message,
                        "detail": f"Line {candidate.line_number}: could not match sender '{candidate.sender or 'unknown'}' to a player.",
                    }
                )
                continue

            payload, status_code = _store_wordle_result(candidate.player.phone_number, candidate.message)
            import_summary.append(
                {
                    "status": "Saved" if status_code == 201 else "Skipped",
                    "message": candidate.message,
                    "detail": (
                        f"{payload['player']} earned {payload['points']} points."
                        if status_code == 201
                        else f"{candidate.player.name}: {payload['error']}"
                    ),
                }
            )

    return render_template(
        "import.html",
        players=players,
        import_summary=import_summary,
        paste_text=paste_text,
    )
