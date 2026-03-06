"""
AXIOM WhatsApp Webhook Server
Runs 24/7 on Railway (free tier).
Receives incoming WhatsApp messages from Twilio instantly
and replies using Claude with context of the current mission.
"""

import os
import json
import anthropic
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Twilio system messages to ignore
IGNORED_MESSAGES = {
    "join driver-ever", "join", "stop", "start", "yes", "no",
    "help", "unstop", "cancel", "unsubscribe", "subscribe"
}

STATE_FILE = "axiom_state.json"


def load_mission() -> dict:
    """Load current mission from state file."""
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            return state.get("current_mission") or {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def answer_question(question: str) -> str:
    """Use Claude to answer a mission-related question instantly."""
    mission = load_mission()
    mission_title = mission.get("mission_title", "your coding mission")
    tech_stack = ", ".join(mission.get("tech_stack", []))
    mission_desc = mission.get("mission_description", "")
    steps = mission.get("starter_steps", [])
    username = os.getenv("GITHUB_USERNAME", "developer")

    system = f"""You are AXIOM, an AI coding mentor for @{username}.

Current mission: {mission_title}
Description: {mission_desc}
Tech stack: {tech_stack}
Steps: {', '.join(steps) if steps else 'Not set yet'}

Answer the user's question helpfully and concisely.
Keep replies under 400 characters so they fit in WhatsApp.
Be practical — give very short code snippets only when truly needed (1-2 lines max).
Be direct and encouraging. No fluff."""

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=system,
            messages=[{"role": "user", "content": question}]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"⚠️ Couldn't answer right now: {str(e)[:80]}"


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Twilio calls this endpoint every time you send a WhatsApp message."""
    incoming = request.form.get("Body", "").strip()
    sender = request.form.get("From", "")

    print(f"📩 Received from {sender}: {incoming}")

    # Use TwiML response — Twilio handles sending this back automatically
    twiml = MessagingResponse()

    # Ignore system/sandbox messages
    if not incoming or incoming.lower() in IGNORED_MESSAGES or len(incoming) < 8:
        print(f"   ⏭️ Skipped system message: '{incoming}'")
        return str(twiml)  # Empty response = no reply sent

    # Answer the question
    print(f"   🤔 Answering: {incoming[:60]}...")
    answer = answer_question(incoming)
    reply = f"🧠 *AXIOM:*\n{answer}"

    print(f"   ✅ Reply: {reply[:80]}...")
    twiml.message(reply)
    return str(twiml)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint so Railway knows the server is alive."""
    mission = load_mission()
    return {
        "status": "running",
        "current_mission": mission.get("mission_title", "None assigned yet")
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 AXIOM Webhook Server starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)


# In-memory mission state (updated by pipeline each morning)
_current_state = {}

@app.route("/update_state", methods=["POST"])
def update_state():
    """Called by the GitHub Actions pipeline each morning to sync mission state."""
    secret = request.headers.get("X-AXIOM-SECRET", "")
    expected = os.getenv("AXIOM_WEBHOOK_SECRET", "")
    if expected and secret != expected:
        return {"error": "Unauthorized"}, 401

    global _current_state
    _current_state = request.json or {}

    # Also write to disk so it survives Railway restarts
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(_current_state, f, indent=2)
        print(f"✅ State updated: {_current_state.get('current_mission', {}).get('mission_title', 'unknown')}")
    except Exception as e:
        print(f"⚠️ Could not write state: {e}")

    return {"status": "ok"}
