"""
AXIOM Agent 7 — Progress Tracker
Checks if the user has committed to their current mission repo.
- If yes → marks mission complete, signals pipeline to assign a new one
- If no  → generates a helpful nudge with hints based on the mission
"""

import requests
import anthropic
from datetime import datetime, timezone


class ProgressTracker:
    def __init__(self, anthropic_key: str, github_token: str, github_username: str):
        self.client = anthropic.Anthropic(api_key=anthropic_key)
        self.github_username = github_username
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _get_user_commits(self, repo_name: str) -> list:
        """Get commits made by the user (not AXIOM bot) on the mission repo."""
        try:
            r = requests.get(
                f"https://api.github.com/repos/{self.github_username}/{repo_name}/commits",
                headers=self.headers,
                params={"author": self.github_username, "per_page": 10},
                timeout=10
            )
            if r.status_code == 200:
                commits = r.json()
                # Filter out auto-generated AXIOM commits
                user_commits = [
                    c for c in commits
                    if not c.get("commit", {}).get("message", "").startswith("🤖 AXIOM:")
                ]
                return user_commits
            return []
        except Exception as e:
            print(f"   ⚠️ Could not fetch commits: {e}")
            return []

    def _get_repo_name_from_url(self, repo_url: str) -> str:
        """Extract repo name from full GitHub URL."""
        return repo_url.rstrip("/").split("/")[-1]

    def _generate_nudge(self, mission_data: dict) -> str:
        """Generate a helpful hint message for a stuck user."""
        mission_title = mission_data.get("mission_title", "your mission")
        tech_stack = ", ".join(mission_data.get("tech_stack", []))
        steps = mission_data.get("starter_steps", [])
        first_step = steps[0] if steps else "Set up your project structure"

        prompt = f"""A student hasn't started working on their coding mission yet.
Mission: {mission_title}
Tech stack: {tech_stack}
First step they should take: {first_step}

Write a short, friendly WhatsApp message (max 200 chars) that:
1. Acknowledges they haven't started yet (no shame, just facts)
2. Gives ONE concrete action they can do in the next 30 minutes
3. Ends with encouragement

Be direct and casual. No emojis spam. Start with 💪"""

        try:
            msg = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return msg.content[0].text.strip()
        except Exception:
            return f"💪 Hey! Your mission '{mission_title}' is waiting. Start with: {first_step}. Even 30 mins counts!"

    def run(self, mission_data: dict, repo_url: str) -> dict:
        """
        Returns:
          status: 'completed' | 'in_progress' | 'not_started'
          nudge_message: str (shown in WhatsApp if not completed)
          assign_new_mission: bool
        """
        if not repo_url:
            return {
                "status": "not_started",
                "nudge_message": "",
                "assign_new_mission": True,
                "commit_count": 0
            }

        repo_name = self._get_repo_name_from_url(repo_url)
        print(f"   🔍 Checking commits on {repo_name}...")

        user_commits = self._get_user_commits(repo_name)
        commit_count = len(user_commits)

        if commit_count > 0:
            last_commit_msg = user_commits[0].get("commit", {}).get("message", "")
            print(f"   ✅ {commit_count} user commit(s) found — mission in progress!")
            return {
                "status": "completed" if commit_count >= 3 else "in_progress",
                "nudge_message": "",
                "assign_new_mission": commit_count >= 3,  # New mission after 3+ commits
                "commit_count": commit_count,
                "last_commit": last_commit_msg
            }
        else:
            print(f"   ⚠️ No user commits found — generating nudge...")
            nudge = self._generate_nudge(mission_data)
            return {
                "status": "not_started",
                "nudge_message": nudge,
                "assign_new_mission": False,
                "commit_count": 0
            }
