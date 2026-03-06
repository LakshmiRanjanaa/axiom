"""
AXIOM Agent 5 — WhatsApp Sender
Sends daily brief + dashboard + mission repo links to WhatsApp.
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
        self.github_username = os.getenv("GITHUB_USERNAME", "")

    def _format_message(self, github_data, roast_data, trend_data, mission_data,
                         dashboard_url="", repo_url="") -> str:
        today = datetime.now().strftime("%d %b %Y")
        username = github_data["username"]
        score = github_data["profile_score"]
        langs = ", ".join(github_data["languages"][:2]) or "Not detected"
        stars = github_data["total_stars"]
        repos = github_data["total_repos"]
        streak = github_data["commit_streak_days"]

        score_emoji = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"

        roast_short = (roast_data.get('roast') or '')[:160]
        fixes = roast_data.get('fixes', [])
        fix1 = fixes[0].get('fix_title', '') if len(fixes) > 0 else ''
        questions = roast_data.get('interview_questions', [])
        q1 = (questions[0] or '')[:100] if questions else ''
        missing = ", ".join(trend_data.get("missing_skills", [])[:3]) or "Keep learning!"
        trending = trend_data.get("trending", [])
        trend1 = trending[0]["name"] if trending else "None today"
        mission_title = (mission_data.get('mission_title') or '')[:50]
        stack = ', '.join(mission_data.get('tech_stack', [])[:3])

        # Build links section — only shown if URLs exist
        links_section = ""
        if repo_url or dashboard_url:
            links_section = "\n🔗 *Links:*"
            if repo_url:
                links_section += f"\n📦 Repo: {repo_url}"
            if dashboard_url:
                links_section += f"\n🌐 Dashboard: {dashboard_url}"

        message = f"""🧠 *AXIOM | {today}*
@{username} | {score_emoji} *{score}/100*
Repos: {repos} | Stars: {stars} | Days: {streak}
Stack: {langs}

💀 *ROAST:*
{roast_short}

🔧 Fix: {fix1}

📈 Trending: {trend1}
⚠️ Missing: {missing}

🎯 *Mission:* {mission_title}
Stack: {stack}

🎤 *Q:* {q1}{links_section}

_AXIOM 🧠 | Daily 8AM_"""

        return message

    def send(self, github_data, roast_data, trend_data, mission_data,
             dashboard_url="", repo_url=""):
        message = self._format_message(
            github_data, roast_data, trend_data, mission_data,
            dashboard_url, repo_url
        )

        print("\n" + "="*50)
        print("📲 WHATSAPP MESSAGE PREVIEW:")
        print("="*50)
        print(message)
        print(f"\n[Message length: {len(message)} chars]")
        print("="*50 + "\n")

        if not all([self.account_sid, self.auth_token, self.to_number]):
            print("⚠️  Twilio credentials not set.")
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