"""
AXIOM Agent 2 — Roast & Fix Agent
Brutally critiques your GitHub profile like a senior recruiter.
Then generates a fix for your worst repo — auto README.
"""

import anthropic
import json


class RoastFixer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def _call_claude(self, system: str, user: str) -> str:
        msg = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        return msg.content[0].text

    def _generate_roast(self, github_data: dict) -> str:
        system = """You are a brutally honest senior tech recruiter reviewing a student's GitHub profile.
Be direct, specific, and a little harsh — but constructive. No fluff. 3-4 sentences max.
Point out exactly what would make you skip this profile in under 10 seconds.
Use simple language a beginner would understand."""

        user = f"""Review this GitHub profile:
Username: {github_data['username']}
Score: {github_data['profile_score']}/100
Total repos: {github_data['total_repos']}
Languages: {', '.join(github_data['languages'])}
Total stars: {github_data['total_stars']}
Weak spots found: {json.dumps(github_data['weak_spots'])}
Top repos: {json.dumps([r['name'] + ': ' + r['description'] for r in github_data['top_repos']])}

Give a brutally honest 3-4 sentence roast of this profile from a recruiter's perspective."""

        return self._call_claude(system, user)

    def _generate_fixes(self, github_data: dict) -> list:
        system = """You are a senior developer giving quick wins to a student.
Return a JSON array of exactly 3 objects: [{fix_title, fix_description, priority (high/medium/low)}]
Each fix should be specific and actionable — something they can do in under 1 hour.
Return ONLY the JSON array, no markdown."""

        user = f"""Based on these GitHub weaknesses: {json.dumps(github_data['weak_spots'])}
Languages: {', '.join(github_data['languages'])}
Score: {github_data['profile_score']}/100

Give 3 specific, actionable fixes to improve this GitHub profile fast."""

        raw = self._call_claude(system, user)
        try:
            return json.loads(raw.strip().replace("```json", "").replace("```", ""))
        except Exception:
            return [{"fix_title": "Add README to all repos", "fix_description": "Write a 5-line README for each repo explaining what it does and how to run it.", "priority": "high"}]

    def _generate_readme(self, github_data: dict) -> dict:
        """Auto-generate a README for the weakest top repo."""
        # Find worst repo (no description or fewest stars)
        worst = None
        for r in github_data["top_repos"]:
            if not r["description"] or r["description"] == "No description":
                worst = r
                break
        if not worst:
            worst = github_data["top_repos"][0] if github_data["top_repos"] else None

        if not worst:
            return {"repo_name": "N/A", "readme": "No repos found to fix."}

        system = """You are a technical writer. Generate a professional GitHub README.
Use markdown. Include: Project title, description, tech stack, how to run it, what problem it solves.
Keep it under 25 lines. Make it look impressive."""

        user = f"""Generate a README for this student project:
Repo name: {worst['name']}
Language: {worst['language']}
Current description: {worst['description']}
GitHub URL: {worst['url']}

Make it look like a professional project, not a homework assignment."""

        readme = self._call_claude(system, user)
        return {
            "repo_name": worst["name"],
            "repo_url": worst["url"],
            "readme": readme
        }

    def _generate_interview_questions(self, github_data: dict) -> list:
        """Generate 3 interview questions based on the student's actual tech stack."""
        system = """You are a technical interviewer. Generate exactly 3 interview questions.
Return a JSON array of 3 strings — just the questions themselves, no answers.
Make them realistic — the kind actually asked in entry-level dev interviews.
Return ONLY the JSON array."""

        user = f"""Generate 3 interview questions for a student whose tech stack is: {', '.join(github_data['languages'])}
Their GitHub score is {github_data['profile_score']}/100 so they are a beginner-intermediate level.
Focus on practical questions about the languages/concepts they actually use."""

        raw = self._call_claude(system, user)
        try:
            return json.loads(raw.strip().replace("```json", "").replace("```", ""))
        except Exception:
            return [
                f"Explain how {github_data['languages'][0] if github_data['languages'] else 'Python'} handles memory management.",
                "What is the difference between a REST API and a GraphQL API?",
                "Walk me through a project you built and the biggest challenge you faced."
            ]

    def run(self, github_data: dict) -> dict:
        roast = self._generate_roast(github_data)
        fixes = self._generate_fixes(github_data)
        readme_fix = self._generate_readme(github_data)
        interview_questions = self._generate_interview_questions(github_data)

        return {
            "roast": roast,
            "fixes": fixes,
            "readme_fix": readme_fix,
            "interview_questions": interview_questions
        }
