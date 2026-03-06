"""
AXIOM Agent 3 — Trend Spotter
Finds what's trending on GitHub in the student's tech stack.
Uses GitHub Search API to find repos that blew up recently.
Then uses Claude to explain why they matter for the student's career.
"""

import requests
import anthropic
import json
from datetime import datetime, timedelta


class TrendSpotter:
    def __init__(self, github_token: str, api_key: str):
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.client = anthropic.Anthropic(api_key=api_key)

    def _search_trending(self, language: str) -> list:
        """Search GitHub for repos in this language that got popular recently."""
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        query = f"language:{language} stars:>100 created:>{week_ago}"

        try:
            r = requests.get(
                "https://api.github.com/search/repositories",
                headers=self.headers,
                params={
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 5
                },
                timeout=10
            )
            r.raise_for_status()
            items = r.json().get("items", [])
            return [
                {
                    "name": item["full_name"],
                    "description": item.get("description", "No description"),
                    "stars": item["stargazers_count"],
                    "url": item["html_url"],
                    "language": item.get("language", language),
                    "topics": item.get("topics", [])
                }
                for item in items
            ]
        except Exception:
            return []

    def _search_student_trending(self) -> list:
        """Find trending repos specifically tagged for students/beginners."""
        try:
            r = requests.get(
                "https://api.github.com/search/repositories",
                headers=self.headers,
                params={
                    "q": "topic:student OR topic:beginner OR topic:portfolio stars:>200",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 3
                },
                timeout=10
            )
            r.raise_for_status()
            items = r.json().get("items", [])
            return [
                {
                    "name": item["full_name"],
                    "description": item.get("description", "No description"),
                    "stars": item["stargazers_count"],
                    "url": item["html_url"],
                }
                for item in items
            ]
        except Exception:
            return []

    def _analyze_relevance(self, languages: list, trending: list) -> str:
        """Use Claude to explain what skills the student is missing vs trending."""
        system = """You are a career advisor for student developers.
Analyze trending GitHub repos vs the student's current skills.
Identify exactly which skills/technologies they're missing that appear in trending repos.
Be specific and concise. 2-3 sentences max.
Return a JSON object: {missing_skills: [list of strings], market_insight: "1 sentence about what the market wants right now"}
Return ONLY the JSON."""

        user = f"""Student's current languages: {', '.join(languages)}

Trending repos this week:
{json.dumps([{'name': r['name'], 'description': r['description'], 'topics': r.get('topics', [])} for r in trending[:5]], indent=2)}

What key skills is the student missing based on what's trending?"""

        try:
            msg = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                system=system,
                messages=[{"role": "user", "content": user}]
            )
            raw = msg.content[0].text.strip().replace("```json", "").replace("```", "")
            return json.loads(raw)
        except Exception:
            return {
                "missing_skills": ["LangChain", "Docker", "FastAPI"],
                "market_insight": "AI/ML tooling and containerization are dominating entry-level job requirements right now."
            }

    def run(self, languages: list) -> dict:
        trending = []

        # Search trending for each of student's languages
        for lang in languages[:3]:
            results = self._search_trending(lang)
            trending.extend(results)

        # Also get general student trending
        student_trending = self._search_student_trending()

        # Deduplicate
        seen = set()
        unique_trending = []
        for r in trending:
            if r["name"] not in seen:
                seen.add(r["name"])
                unique_trending.append(r)

        # Analyze what skills are missing
        gap_analysis = self._analyze_relevance(languages, unique_trending)

        return {
            "trending": unique_trending[:5],
            "student_picks": student_trending,
            "missing_skills": gap_analysis.get("missing_skills", []),
            "market_insight": gap_analysis.get("market_insight", "")
        }
