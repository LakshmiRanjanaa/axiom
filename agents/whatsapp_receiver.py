"""
AXIOM Agent 8 — WhatsApp Receiver
Polls Twilio for messages sent by the user since the last run.
If a question is found, Claude answers it in context of the current mission
and sends the reply back via WhatsApp.
"""

import os
import anthropic
from twilio.rest import Client
from datetime import datetime, timezone, timedelta


class WhatsAppReceiver:
    def __init__(self, anthropic_key: str):
        self.anthropic_key = anthropic_key
        self.client = anthropic.Anthropic(api_key=anthropic_key)
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        self.to_number = os.getenv("YOUR_WHATSAPP_NUMBER")

    def _get_incoming_messages(self) -> list:
        """Poll Twilio for messages received in the last 25 hours."""
        if not all([self.account_sid, self.auth_token]):
            return []

        try:
            twilio_client = Client(self.account_sid, self.auth_token)
            since = datetime.now(timezone.utc) - timedelta(hours=25)

            # Fetch messages sent TO our Twilio number (i.e. FROM the user)
            messages = twilio_client.messages.list(
                to=self.from_number,
                date_sent_after=since,
                limit=10
            )

            # Only return messages from the user's number
            user_messages = [
                m for m in messages
                if m.from_ == self.to_number and m.direction == "inbound"
            ]

            return user_messages
        except Exception as e:
            print(f"   ⚠️ Could not poll messages: {e}")
            return []

    def _answer_question(self, question: str, mission_data: dict, github_data: dict) -> str:
        """Use Claude to answer a mission-related question."""
        mission_title = mission_data.get("mission_title", "your mission")
        tech_stack = ", ".join(mission_data.get("tech_stack", []))
        mission_desc = mission_data.get("mission_description", "")
        steps = mission_data.get("starter_steps", [])
        username = github_data.get("username", "")
        languages = ", ".join(github_data.get("languages", []))

        system = f"""You are AXIOM, an AI mentor helping a developer named @{username} build their coding mission.

Current mission: {mission_title}
Description: {mission_desc}
Tech stack: {tech_stack}
Their current skills: {languages}
Steps: {', '.join(steps)}

Answer their question helpfully and concisely. Keep replies under 300 characters so they fit nicely in WhatsApp.
Be practical — give code snippets only if they're very short (1-2 lines). Be encouraging but direct."""

        try:
            msg = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                system=system,
                messages=[{"role": "user", "content": question}]
            )
            return msg.content[0].text.strip()
        except Exception as e:
            return f"⚠️ Couldn't process your question right now. Try again! ({str(e)[:50]})"

    def _send_reply(self, reply: str, original_question: str):
        """Send the answer back to the user via WhatsApp."""
        if not all([self.account_sid, self.auth_token, self.to_number]):
            print("   ⚠️ Twilio credentials not set.")
            return

        try:
            twilio_client = Client(self.account_sid, self.auth_token)
            full_message = f"🧠 *AXIOM answers:*\n\n_{original_question[:80]}..._\n\n{reply}"
            twilio_client.messages.create(
                from_=self.from_number,
                to=self.to_number,
                body=full_message
            )
            print(f"   ✅ Reply sent!")
        except Exception as e:
            print(f"   ❌ Reply failed: {e}")

    def run(self, mission_data: dict, github_data: dict) -> dict:
        """
        Poll for messages, answer any questions found, return summary.
        """
        print("   📥 Polling for incoming WhatsApp messages...")
        messages = self._get_incoming_messages()

        if not messages:
            print("   📭 No new messages found.")
            return {"questions_found": 0, "answered": 0}

        print(f"   📬 Found {len(messages)} message(s) from you!")
        answered = 0

        for msg in messages:
            question = msg.body.strip()
            if not question:
                continue

            print(f"   ❓ Question: {question[:60]}...")
            answer = self._answer_question(question, mission_data, github_data)
            self._send_reply(answer, question)
            answered += 1

        return {"questions_found": len(messages), "answered": answered}
