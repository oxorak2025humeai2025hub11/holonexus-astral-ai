# Holonexus Astral AI — starter server

This is a small hosted backend for the Astral AI panel in the Holonexus HTML page.
It keeps the AI provider key on the server and returns JSON in the format the page expects:
`{"reply":"..."}`.

## Before you deploy

- You need an OpenAI API key and API billing enabled. ChatGPT subscriptions and API billing are separate.
- Never put the OpenAI key in the Holonexus HTML, browser settings, GitHub, or a public message.
- The starter has an origin allowlist and per-IP request limits. CORS is not authentication; these are basic abuse controls, not a guarantee against all misuse. Watch API usage and set provider-side usage limits.
- The `memory://` rate limiter resets on restart and is not shared across multiple instances. For a larger deployment, use a persistent Redis-compatible rate-limit store.
- Render free web services can sleep when idle, so the first request after inactivity may take longer.

## Deploy on Render using GitHub

1. Create a new **private** GitHub repository, for example `holonexus-astral-ai`.
2. Upload `app.py`, `requirements.txt`, and `render.yaml` from this folder to the repository root.
3. In Render, choose **New → Blueprint** and connect that repository, or choose **New → Web Service** and connect it.
4. If deploying as a Web Service manually, use:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
5. In the Render service's **Environment** settings, set `OPENAI_API_KEY` to your secret key. Do not add the key to GitHub or the HTML.
6. Set `ALLOWED_ORIGINS` to the exact origin of the Holonexus page, with no path. The default is `https://spidyradioon.is-great.net`. If you also use another hostname, add it comma-separated.
7. Deploy and wait for the service to report Live.

## Test the deployment

Open this URL in a browser, replacing the example with your actual Render hostname:

`https://YOUR-SERVICE.onrender.com/health`

It should return a small JSON object like `{"ok":true,"service":"astral-ai"}`.

The chat endpoint is:

`https://YOUR-SERVICE.onrender.com/api/astral-chat`

In Holonexus, open **ASTRAL AI → Connection & Voice Settings** and enter that complete URL. Save it, then send a short test message. The backend only allows requests from the configured site origin.

## If it fails

- `Origin not allowed`: update `ALLOWED_ORIGINS` to exactly match the website origin (scheme + hostname only), then redeploy.
- `AI service is not configured yet`: add `OPENAI_API_KEY` in Render's Environment settings.
- `The AI service could not complete that request`: inspect Render logs, confirm API billing/model access, and check your provider usage limits.
- Slow first reply: the Render free service may have been asleep. Try again after it wakes.
- Do not expose secrets when sharing logs or screenshots.

## Important scope

This server handles text conversations only. The Holonexus browser's existing Test Voice feature can speak text with browser speech. This does not yet connect XTTS/RVC, persistent chat memory, account login, or real-time audio streaming.
