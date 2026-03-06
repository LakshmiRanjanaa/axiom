"""
AXIOM Agent 1 — GitHub Auditor
Fetches your real GitHub profile and scores it like a recruiter would.
Uses GitHub REST API (no OAuth needed for public repos).
"""

import requests
from datetime import datetime, timezone


class GitHubAuditor:
    def __init__(self, username: str, token: str):
        self.username = username
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base = "https://api.github.com"

    def _get(self, path: str) -> dict | list:
        r = requests.get(f"{self.base}{path}", headers=self.headers, timeout=10)
        r.raise_for_status()
        return r.json()

    def _get_repos(self) -> list:
        repos = []
        page = 1
        while True:
            batch = self._get(f"/users/{self.username}/repos?per_page=100&page={page}&sort=updated")
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return repos

    def _get_commit_streak(self) -> int:
        """Estimate commit streak from recent events."""
        try:
            events = self._get(f"/users/{self.username}/events?per_page=100")
            push_days = set()
            for e in events:
                if e.get("type") == "PushEvent":
                    day = e["created_at"][:10]
                    push_days.add(day)
            return len(push_days)
        except Exception:
            return 0

    def _score_profile(self, repos: list, user: dict) -> int:
        """Score GitHub profile out of 100 like a recruiter would."""
        score = 0

        # Repos with README (20 pts)
        repos_with_readme = sum(1 for r in repos if not r.get("fork") and r.get("description"))
        readme_pct = repos_with_readme / max(len(repos), 1)
        score += int(readme_pct * 20)

        # Project variety / language diversity (20 pts)
        langs = set(r.get("language") for r in repos if r.get("language"))
        score += min(len(langs) * 4, 20)

        # Stars earned (15 pts)
        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        score += min(total_stars * 2, 15)

        # Profile completeness (15 pts)
        if user.get("bio"):
            score += 5
        if user.get("location"):
            score += 3
        if user.get("blog"):
            score += 4
        if user.get("email"):
            score += 3

        # Repo count (10 pts)
        score += min(len([r for r in repos if not r.get("fork")]) * 2, 10)

        # Recent activity (20 pts)
        recent = [r for r in repos if r.get("pushed_at", "") > "2024-01-01"]
        score += min(len(recent) * 4, 20)

        return min(score, 100)

    def _detect_weak_spots(self, repos: list) -> list:
        """Find specific weaknesses a recruiter would notice."""
        issues = []
        no_desc = [r for r in repos if not r.get("description") and not r.get("fork")]
        if len(no_desc) > 2:
            issues.append(f"{len(no_desc)} repos have no description — recruiters skip these instantly")

        names = [r["name"].lower() for r in repos if not r.get("fork")]
        beginner_names = [n for n in names if any(kw in n for kw in
            ["todo", "calculator", "hello", "test", "practice", "learning", "tutorial"])]
        if len(beginner_names) > 2:
            issues.append(f"{len(beginner_names)} beginner-level project names detected (todo apps, calculators) — shows no real-world problem solving")

        forked = [r for r in repos if r.get("fork")]
        if len(forked) > len(repos) * 0.5:
            issues.append(f"{len(forked)} of your repos are forks — this dilutes your profile")

        langs = set(r.get("language") for r in repos if r.get("language"))
        if len(langs) < 2:
            issues.append("Only 1 language detected — shows narrow skill set")

        if not issues:
            issues.append("Profile looks decent but lacks standout projects")

        return issues

    def run(self) -> dict:
        user = self._get(f"/users/{self.username}")
        repos = self._get_repos()
        own_repos = [r for r in repos if not r.get("fork")]

        # Languages breakdown
        lang_counts = {}
        for r in own_repos:
            lang = r.get("language")
            if lang:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
        top_langs = sorted(lang_counts, key=lang_counts.get, reverse=True)[:5]

        # Top repos by stars
        top_repos = sorted(own_repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:5]

        score = self._score_profile(repos, user)
        weak_spots = self._detect_weak_spots(own_repos)
        streak = self._get_commit_streak()

        return {
            "username": self.username,
            "name": user.get("name", self.username),
            "bio": user.get("bio", "No bio set"),
            "followers": user.get("followers", 0),
            "profile_score": score,
            "total_repos": len(own_repos),
            "total_stars": sum(r.get("stargazers_count", 0) for r in own_repos),
            "languages": top_langs,
            "lang_counts": lang_counts,
            "top_repos": [
                {
                    "name": r["name"],
                    "description": r.get("description", "No description"),
                    "stars": r.get("stargazers_count", 0),
                    "language": r.get("language", "Unknown"),
                    "url": r.get("html_url", ""),
                }
                for r in top_repos
            ],
            "weak_spots": weak_spots,
            "commit_streak_days": streak,
            "profile_url": f"https://github.com/{self.username}",
        }
