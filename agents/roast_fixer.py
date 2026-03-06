"""
AXIOM Agent 2 — Roast & Fix Agent
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
        system = "You are a brutally honest senior tech recruiter. Be direct, harsh but constructive. 3-4 sentences max."
        repos = [r['name'] + ': ' + (r['description'] or 'No description') for r in github_data['top_repos']]
        user = f"Username: {github_data['username']}, Score: {github_data['profile_score']}/100, Repos: {github_data['total_repos']}, Languages: {', '.join(github_data['languages'])}, Top repos: {json.dumps(repos)}. Give a brutal recruiter roast."
        return self._call_claude(system, user)

    def _generate_fixes(self, github_data: dict) -> list:
        system = "Return a JSON array of exactly 3 objects: [{fix_title, fix_description, priority}]. ONLY return JSON."
        user = f"Weaknesses: {json.dumps(github_data['weak_spots'])}. Give 3 fixes."
        raw = self._call_claude(system, user)
        try:
            return json.loads(raw.strip().replace("```json","").replace("```",""))
        except:
            return [{"fix_title": "Add README", "fix_description": "Add README to all repos.", "priority": "high"}]

    def _generate_readme(self, github_data: dict) -> dict:
        worst = next((r for r in github_data["top_repos"] if not r["description"]), None)
        if not worst:
            worst = github_data["top_repos"][0] if github_data["top_repos"] else None
        if not worst:
            return {"repo_name": "N/A", "repo_url": "", "readme": "No repos found."}
        system = "Generate a professional GitHub README in markdown. Under 25 lines."
        user = f"Repo: {worst['name']}, Language: {worst['language']}, URL: {worst['url']}"
        return {"repo_name": worst["name"], "repo_url": worst["url"], "readme": self._call_claude(system, user)}

    def _generate_interview_questions(self, github_data: dict) -> list:
        system = "Return a JSON array of exactly 3 interview question strings. ONLY return JSON."
        user = f"3 interview questions for student with stack: {', '.join(github_data['languages'])}"
        raw = self._call_claude(system, user)
        try:
            return json.loads(raw.strip().replace("```json","").replace("```",""))
        except:
            return ["Explain memory management in your language.", "REST vs GraphQL?", "Walk me through a project you built."]

    def run(self, github_data: dict) -> dict:
        return {
            "roast": self._generate_roast(github_data),
            "fixes": self._generate_fixes(github_data),
            "readme_fix": self._generate_readme(github_data),
            "interview_questions": self._generate_interview_questions(github_data)
