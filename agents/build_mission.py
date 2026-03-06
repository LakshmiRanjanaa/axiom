"""
AXIOM Agent 4 — Build Mission Agent
Generates ONE specific, achievable build mission for today.
Based on skill gaps, trending tech, and profile weaknesses.
Also scores how this mission improves recruiter appeal.
"""

import anthropic
import json


class BuildMissionAgent:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def _call_claude(self, system: str, user: str) -> str:
        msg = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        return msg.content[0].text

    def _generate_mission(self, github_data: dict, trend_data: dict, roast_data: dict) -> dict:
        system = """You are a senior developer mentoring a CS student.
Generate ONE specific build mission they can complete in 4-6 hours today.
Return a JSON object with EXACTLY these fields:
{
  "mission_title": "short project name",
  "mission_description": "2 sentences: what to build and why it matters",
  "tech_stack": ["list", "of", "technologies"],
  "estimated_hours": 5,
  "github_boost": "1 sentence: how this improves their GitHub profile",
  "starter_steps": ["Step 1", "Step 2", "Step 3"],
  "why_hireable": "1 sentence: why recruiters will notice this",
  "difficulty": "beginner/intermediate"
}
Return ONLY the JSON object."""

        user = f"""Student GitHub profile:
- Current languages: {', '.join(github_data['languages'])}
- Profile score: {github_data['profile_score']}/100
- Total repos: {github_data['total_repos']}
- Weak spots: {json.dumps(github_data['weak_spots'][:2])}

Missing skills vs market: {json.dumps(trend_data['missing_skills'])}
Market insight: {trend_data['market_insight']}

Recruiter roast summary: {roast_data['roast'][:200]}

Generate the perfect build mission for today that:
1. Fills their biggest skill gap
2. Can be completed in 4-6 hours
3. Would genuinely impress a recruiter
4. Fits their current level"""

        raw = self._call_claude(system, user)
        try:
            return json.loads(raw.strip().replace("```json", "").replace("```", ""))
        except Exception:
            return {
                "mission_title": "Build a REST API with FastAPI",
                "mission_description": "Create a simple task management API with CRUD operations. This demonstrates backend skills that every company needs.",
                "tech_stack": ["Python", "FastAPI", "SQLite"],
                "estimated_hours": 5,
                "github_boost": "Shows you can build production-ready backends, not just scripts.",
                "starter_steps": [
                    "Install FastAPI: pip install fastapi uvicorn",
                    "Create main.py with 4 endpoints (GET, POST, PUT, DELETE)",
                    "Add a README explaining the API and how to run it"
                ],
                "why_hireable": "FastAPI is the #1 skill requested in Python backend job posts.",
                "difficulty": "beginner"
            }

    def _generate_30day_preview(self, github_data: dict, trend_data: dict) -> list:
        """Give a 5-step 30-day roadmap preview."""
        system = """Generate a concise 5-step 30-day learning roadmap for a student developer.
Return a JSON array of 5 objects: [{week, focus, outcome}]
Keep each outcome to 1 sentence. Be specific to their stack.
Return ONLY the JSON array."""

        user = f"""Student stack: {', '.join(github_data['languages'])}
Missing skills: {json.dumps(trend_data['missing_skills'])}
Current level: {github_data['profile_score']}/100

Create a 30-day roadmap that takes them from their current level to job-ready."""

        raw = self._call_claude(system, user)
        try:
            return json.loads(raw.strip().replace("```json", "").replace("```", ""))
        except Exception:
            return [
                {"week": "Week 1", "focus": "Strengthen fundamentals", "outcome": "Rebuild 2 existing projects with proper README and documentation."},
                {"week": "Week 2", "focus": "Learn a new framework", "outcome": "Build and deploy a simple REST API."},
                {"week": "Week 3", "focus": "Database integration", "outcome": "Add a real database to your API project."},
                {"week": "Week 4", "focus": "Portfolio polish", "outcome": "GitHub profile score above 80/100 and 1 standout project."}
            ]

    def run(self, github_data: dict, trend_data: dict, roast_data: dict) -> dict:
        mission = self._generate_mission(github_data, trend_data, roast_data)
        roadmap = self._generate_30day_preview(github_data, trend_data)

        return {
            "mission_title": mission.get("mission_title", "Build something today"),
            "mission_description": mission.get("mission_description", ""),
            "tech_stack": mission.get("tech_stack", []),
            "estimated_hours": mission.get("estimated_hours", 5),
            "github_boost": mission.get("github_boost", ""),
            "starter_steps": mission.get("starter_steps", []),
            "why_hireable": mission.get("why_hireable", ""),
            "difficulty": mission.get("difficulty", "beginner"),
            "roadmap_preview": roadmap
        }
