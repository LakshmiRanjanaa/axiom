"""
AXIOM Agent 5 — WhatsApp Sender
Formats all agent outputs into a beautiful WhatsApp message.
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

    def _format_message(
        self,
        github_data: dict,
        roast_data: dict,
        trend_data: dict,
        mission_data: dict
    ) -> str:
        today = datetime.now().strftime("%d %b %Y")
        username = github_data["username"]
        score = github_data["profile_score"]
        langs = ", ".join(github_data["languages"][:3]) or "Not detected"
        stars = github_data["total_stars"]
        repos = github_data["total_repos"]
        streak = github_data["commit_streak_days"]

        # Score emoji
        if score >= 75:
            score_emoji = "🟢"
        elif score >= 50:
            score_emoji = "🟡"
        else:
            score_emoji = "🔴"

        # Trending repos (top 2)
        trending_lines = ""
        for t in trend_data["trending"][:2]:
            trending_lines += f"  → {t['name']} ⭐{t['stars']:,}\n"
        if not trending_lines:
            trending_lines = "  → No trending repos found today\n"

        # Missing skills (top 3)
        missing = trend_data.get("missing_skills", [])[:3]
        missing_str = ", ".join(missing) if missing else "Keep learning!"

        # Fixes (top 2)
        fixes_lines = ""
        for fix in roast_data.get("fixes", [])[:2]:
            fixes_lines += f"  ✏️ {fix['fix_title']}\n"

        # Mission steps (top 3)
        steps_lines = ""
        for i, step in enumerate(mission_data.get("starter_steps", [])[:3], 1):
            steps_lines += f"  {i}. {step}\n"

        # Interview questions
        questions = roast_data.get("interview_questions", [])
        q_lines = ""
        for i, q in enumerate(questions[:3], 1):
            q_lines += f"  {i}. {q}\n"

        # README fix
        readme_repo = roast_data.get("readme_fix", {}).get("repo_name", "N/A")
        readme_url = roast_data.get("readme_fix", {}).get("repo_url", "")

        message = f"""🧠 *AXIOM DAILY BRIEF*
📅 {today} | @{username}

━━━━━━━━━━━━━━━━━━━━━━
📊 *GITHUB PROFILE SCORE*
{score_emoji} *{score}/100*
Repos: {repos} | Stars: {stars} | Active days: {streak}
Stack: {langs}

━━━━━━━━━━━━━━━━━━━━━━
💀 *RECRUITER ROAST*
{roast_data.get('roast', 'No roast generated')}

🔧 *QUICK FIXES:*
{fixes_lines}
━━━━━━━━━━━━━━━━━━━━━━
📈 *TRENDING IN YOUR STACK*
{trending_lines}
⚠️ *Skills you're missing:* {missing_str}
💡 {trend_data.get('market_insight', '')}

━━━━━━━━━━━━━━━━━━━━━━
🎯 *TODAY'S BUILD MISSION*
*{mission_data['mission_title']}*
{mission_data['mission_description']}

Stack: {', '.join(mission_data['tech_stack'][:3])}
Time: ~{mission_data['estimated_hours']}hrs | Level: {mission_data['difficulty']}

*Start here:*
{steps_lines}
💼 Why it matters: {mission_data['why_hireable']}

━━━━━━━━━━━━━━━━━━━━━━
🎤 *INTERVIEW PREP (your stack)*
{q_lines}
━━━━━━━━━━━━━━━━━━━━━━
📝 *AUTO README GENERATED*
Repo: {readme_repo}
{readme_url}
(Copy the README from your AXIOM run logs)

━━━━━━━━━━━━━━━━━━━━━━
_AXIOM 🧠 | Making you findable, not just hireable_
_Runs daily 8AM automatically_"""

        return message

    def send(
        self,
        github_data: dict,
        roast_data: dict,
        trend_data: dict,
        mission_data: dict
    ):
        message = self._format_message(github_data, roast_data, trend_data, mission_data)

        # Print to console always (useful for logs)
        print("\n" + "="*50)
        print("📲 WHATSAPP MESSAGE PREVIEW:")
        print("="*50)
        print(message)
        print("="*50 + "\n")

        # Send via Twilio if credentials exist
        if not all([self.account_sid, self.auth_token, self.to_number]):
            print("⚠️  Twilio credentials not set — message printed above only.")
            print("    Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, YOUR_WHATSAPP_NUMBER in .env")
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
            print("   Check your Twilio credentials and sandbox setup.")
