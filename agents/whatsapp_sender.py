"""
AXIOM Agent 5 — WhatsApp Sender
Formats all agent outputs into a WhatsApp message under 1600 chars.
Sends via Twilio WhatsApp API automatically.
"""

import os
from twilio.rest import Client
from datetime import datetime


class WhatsAppSender:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        self.to_number = os.getenv("YOUR_WHATSAPP_NUMBER")

    def _format_message(self, github_data, roast_data, trend_data, mission_data) -> str:
        today = datetime.now().strftime("%d %b %Y")
        username = github_data["username"]
        score = github_data["profile_score"]
        langs = ", ".join(github_data["languages"][:2]) or "Not detected"
        stars = github_data["total_stars"]
        repos = github_data["total_repos"]
        streak = github_data["commit_streak_days"]

        score_emoji = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"

        roast_short = (roast_data.get('roast') or '')[:180]
        fixes = roast_data.get('fixes', [])
        fix1 = fixes[0].get('fix_title', '') if len(fixes) > 0 else ''
        fix2 = fixes[1].get('fix_title', '') if len(fixes) > 1 else ''
        questions = roast_data.get('interview_questions', [])
        q1 = (questions[0] or '')[:120] if questions else ''
        missing = ", ".join(trend_data.get("missing_skills", [])[:3]) or "Keep learning!"
        trending = trend_data.get("trending", [])
        trend1 = trending[0]["name"] if trending else "None today"
        mission_title = (mission_data.get('mission_title') or '')[:50]
        mission_why = (mission_data.get('why_hireable') or '')[:100]
        stack = ', '.join(mission_data.get('tech_stack', [])[:3])

        message = f"""🧠 *AXIOM | {today}*
@{username} | {score_emoji} *{score}/100*
Repos: {repos} | Stars: {stars} | Days: {streak}
Stack: {langs}

💀 *ROAST:*
{roast_short}

🔧 *Fix these:*
• {fix1}
• {fix2}

📈 Trending: {trend1}
⚠️ Missing: {missing}

🎯 *Mission:* {mission_title}
Stack: {stack}
{mission_why}

🎤 *Interview Q:*
{q1}

_AXIOM 🧠 | Daily 8AM_"""

        return message

    def send(self, github_data, roast_data, trend_data, mission_data):
        message = self._format_message(github_data, roast_data, trend_data, mission_data)

        print("\n" + "="*50)
        print("📲 WHATSAPP MESSAGE PREVIEW:")
        print("="*50)
        print(message)
        print(f"\n[Message length: {len(message)} chars]")
        print("="*50 + "\n")

        if not all([self.account_sid, self.auth_token, self.to_number]):
            print("⚠️  Twilio credentials not set — message printed above only.")
            return

        try:
            client = Client(self.account_sid, self.auth_token)
            msg = client.messages.create(
                from_=self.from_number,
                to=self.to_number,
                body=message
            )
            print(f"✅ WhatsApp sent! Message SID: {msg.sid}")
        except Exception as e:
            print(f"❌ WhatsApp send failed: {e}")