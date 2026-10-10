import os
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from openai import OpenAI

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # Reject oversized request bodies.

# Basic abuse controls. Memory storage is suitable for a starter deployment;
# use a shared Redis-compatible store for multi-instance production deployments.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)

def allowed_origins():
    raw = os.getenv(
        "ALLOWED_ORIGINS",
        "https://spidyradioon.is-great.net"
    )
    return {origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()}

@app.after_request
def cors_headers(response):
    origin = request.headers.get("Origin", "").rstrip("/")
    if origin and origin in allowed_origins():
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Max-Age"] = "600"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/health")
def health():
    # Do not reveal secret configuration or provider details here.
    return jsonify({"ok": True, "service": "astral-ai"}), 200

@app.route("/api/astral-chat", methods=["POST", "OPTIONS"])
@limiter.limit("10 per minute; 100 per day", methods=["POST"])
def astral_chat():
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "").rstrip("/")
        if not origin or origin not in allowed_origins():
            return jsonify({"error": "Origin not allowed"}), 403
        return ("", 204)

    origin = request.headers.get("Origin", "").rstrip("/")
    if not origin or origin not in allowed_origins():
        return jsonify({"error": "Origin not allowed"}), 403

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        app.logger.error("OPENAI_API_KEY is not configured.")
        return jsonify({"error": "AI service is not configured yet."}), 503

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON object containing a message."}), 400

    message = data.get("message", "")
    if not isinstance(message, str):
        return jsonify({"error": "Message must be text."}), 400

    message = message.strip()
    if not message:
        return jsonify({"error": "Please enter a message."}), 400
    if len(message) > 1500:
        return jsonify({"error": "Please keep messages to 1,500 characters or fewer."}), 413

    # Keep the character/persona instruction on the server, not in the public HTML.
    system_prompt = os.getenv(
        "ASTRAL_SYSTEM_PROMPT",
        "You are Astral, a warm, thoughtful sci-fi companion inside Holonexus. "
        "Speak clearly, kindly, and conversationally. Keep replies concise enough "
        "to be spoken aloud. Do not claim to control the user's device or access "
        "their camera unless a connected tool explicitly provides that ability."
    )

    try:
        client = OpenAI(api_key=api_key, timeout=30.0, max_retries=1)
        result = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            instructions=system_prompt,
            input=message,
            max_output_tokens=350,
        )
        reply = (result.output_text or "").strip()
        if not reply:
            reply = "I didn't receive a text answer that time. Please try again."
        return jsonify({"reply": reply}), 200
    except Exception:
        # Detailed errors belong in server logs; do not return secrets to the browser.
        app.logger.exception("Astral AI request failed.")
        return jsonify({"error": "The AI service could not complete that request. Please try again shortly."}), 502

if __name__ == "__main__":
    # Local testing only. Render uses the Gunicorn start command from the README.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")), debug=False)
