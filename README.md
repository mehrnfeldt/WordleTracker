# Wordle Leaderboard

A Flask web app that parses Wordle messages from a group chat, stores results in SQLite, and displays a leaderboard.

## Run with Docker

```bash
docker-compose up --build
```

Open http://localhost:5000.

## Install on your phone

After the app is hosted at a public HTTPS URL, open it on your phone:

- iPhone Safari: tap Share, then Add to Home Screen.
- Android Chrome: open the browser menu, then Install app or Add to Home screen.

The app includes a web-app manifest, icon, and service worker so it can launch from your home screen like a lightweight app.

## Deploy on Render

1. Push this project to a GitHub repository.
2. In Render, choose New, then Blueprint.
3. Connect the GitHub repository.
4. Render will read `render.yaml` and build the Dockerfile.
5. Open the deployed app URL.

The app automatically creates Megan, Ben, Syd, and Cathy when the database is empty, so Render Shell is not required.

Render will give you an HTTPS URL ending in `onrender.com`. Open that URL on your phone and use Add to Home Screen.

Note: Render's free web service does not support persistent disks. The included `render.yaml` uses free hosting, so SQLite data can be lost when the service is redeployed or restarted. For persistent hosted data, use a paid Render service with a disk, or switch the app to a hosted database such as PostgreSQL.

## Reset players and clear results

```bash
docker-compose run --rm web python seed.py
```

This creates Megan, Ben, Syd, and Cathy, and clears all Wordle results so the leaderboard can populate from pasted imports only.

## Import copied chat results

Open http://localhost:5000/import and paste chat text containing Wordle results.

Supported paste formats include:

```text
Megan: Wordle 1466 3/6
Ben: Wordle 1466 2/6
```

or:

```text
Megan
Wordle 1466 3/6

Ben
Wordle 1466 2/6
```

Sender names or phone numbers must match existing players.

## Connect Text Messages

Use an SMS provider such as Twilio to forward inbound texts to:

```text
POST https://your-public-app-url.com/webhooks/twilio/sms
```

For local testing, expose the app with a tunnel such as ngrok:

```bash
ngrok http 5000
```

Then configure the Twilio phone number's incoming message webhook to:

```text
https://your-ngrok-domain.ngrok-free.app/webhooks/twilio/sms
```

Twilio will send form fields named `From` and `Body`. The app matches `From` to a player's `phone_number`, parses `Body`, stores the result, and replies with a short SMS confirmation.

Important: a normal personal iMessage or carrier group chat cannot usually be read directly by a web app. The reliable setup is to have players text a shared SMS number, or use a provider/automation that can forward messages to this webhook.

## API

### Submit a result

```bash
curl -X POST http://localhost:5000/api/results \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+15550000001","message":"Wordle 1466 3/6"}'
```

The phone number must already belong to a player. Seed data creates:

- Megan: `+15550000001`
- Ben: `+15550000002`
- Syd: `+15550000003`
- Cathy: `+15550000004`

### Leaderboard

```bash
curl http://localhost:5000/api/leaderboard
```

Rows include total points, average guess count, daily wins, and current streak.

## Local development

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
python seed.py
python run.py
```

Run tests:

```bash
pytest
```

## Scoring

| Result | Points |
| ------ | ------ |
| 1/6 | 10 |
| 2/6 | 8 |
| 3/6 | 6 |
| 4/6 | 4 |
| 5/6 | 2 |
| 6/6 | 1 |
| X/6 | 0 |
