"""
AXIOM WhatsApp Webhook Server
Runs 24/7 on Railway. Receives WhatsApp messages and replies instantly using Claude.
"""

import os
import json
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

IGNORED_MESSAGES = {
    "join driver-ever", "join", "stop", "start", "yes", "no",
    "help", "unstop", "cancel", "unsubscribe", "subscribe"
}

STATE_FILE = "axiom_state.json"


def load_mission() -> dict:
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            return state.get("current_mission") or {}
    except Exception:
        return {}


def answer_question(question: str) -> str:
    try:
        import anthropic
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
Answer helpfully and concisely under 400 characters. Be direct and practical."""

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=system,
            messages=[{"role": "user", "content": question}]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"⚠️ Error: {str(e)[:100]}"


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    try:
        incoming = request.form.get("Body", "").strip()
        print(f"📩 Received: {incoming}")

        # Build TwiML response manually (avoids twilio import issues)
        if not incoming or incoming.lower() in IGNORED_MESSAGES or len(incoming) < 8:
            print(f"   ⏭️ Skipped: '{incoming}'")
            return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200, {'Content-Type': 'text/xml'}

        answer = answer_question(incoming)
        reply = f"🧠 AXIOM:\n{answer}"
        print(f"   ✅ Replying: {reply[:80]}...")

        # Return TwiML response
        twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{reply}</Message></Response>'
        return twiml, 200, {'Content-Type': 'text/xml'}

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200, {'Content-Type': 'text/xml'}


@app.route("/health", methods=["GET"])
def health():
    mission = load_mission()
    return {"status": "running", "mission": mission.get("mission_title", "none")}


@app.route("/update_state", methods=["POST"])
def update_state():
    secret = request.headers.get("X-AXIOM-SECRET", "")
    expected = os.getenv("AXIOM_WEBHOOK_SECRET", "")
    if expected and secret != expected:
        return {"error": "Unauthorized"}, 401
    try:
        state = request.json or {}
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        print(f"✅ State updated")
        return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/", methods=["GET"])
def index():
    return {"status": "AXIOM webhook server running 🧠"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 AXIOM starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
