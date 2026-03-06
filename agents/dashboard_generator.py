"""
AXIOM Dashboard Generator
Creates a live HTML dashboard from today's run data.
Pushes to GitHub Pages so it's always live and accessible.
"""

import json
import requests
import base64


class DashboardGenerator:
    def __init__(self, github_token: str, github_username: str, repo_name: str = "axiom"):
        self.github_token = github_token
        self.github_username = github_username
        self.repo_name = repo_name
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }

    def _build_html(self, data: dict) -> str:
        gh = data["github"]
        mission = data["mission"]
        repo = data.get("repo", {})
        score = gh["score"]
        score_emoji = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
        score_color = "#6af7a0" if score >= 75 else "#f7c26a" if score >= 50 else "#f76a6a"
        circumference = 314
        offset = circumference - (score / 100) * circumference

        trending_html = ""
        for t in data.get("trending", [])[:3]:
            trending_html += f"""
            <div class="trend-item">
              <span class="trend-name">{t.get('name','')}</span>
              <span class="trend-stars">⭐ {t.get('stars',0):,}</span>
            </div>"""

        fixes_html = ""
        for f in data.get("fixes", [])[:3]:
            fixes_html += f'<div class="fix-item">✏️ {f.get("fix_title","")}</div>'

        questions_html = ""
        for i, q in enumerate(data.get("interview_questions", [])[:3], 1):
            questions_html += f'<div class="q-item"><span class="q-num">{i}.</span> {q}</div>'

        missing_html = " · ".join(data.get("missing_skills", [])[:4])

        steps_html = ""
        for i, s in enumerate(mission.get("steps", [])[:3], 1):
            steps_html += f'<div class="step-item"><span class="step-num">{i}</span>{s}</div>'

        repo_url = repo.get("url", "")
        repo_btn = f'<a href="{repo_url}" target="_blank" class="repo-btn">🔗 Open Mission Repo</a>' if repo_url else '<span class="repo-btn disabled">Repo pending...</span>'

        weak_html = ""
        for w in gh.get("weak_spots", [])[:2]:
            weak_html += f'<div class="weak-item">⚠️ {w[:80]}</div>'

        langs = ", ".join(gh.get("languages", [])[:3]) or "Not detected"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AXIOM Live Dashboard — @{gh['username']}</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#05070e;--card:#0f1220;--b:#1a1f35;--b2:#252b45;--a:#7c6af7;--a2:#f7c26a;--a3:#6af7c2;--text:#e8eaf8;--m:#6b7299;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--bg);color:var(--text);font-family:'JetBrains Mono',monospace;min-height:100vh;}}
body::before{{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(124,106,247,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(124,106,247,0.02) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;}}
.wrap{{max-width:1200px;margin:0 auto;padding:0 20px 60px;position:relative;z-index:1;}}
header{{display:flex;align-items:center;justify-content:space-between;padding:24px 0 20px;border-bottom:1px solid var(--b);margin-bottom:24px;flex-wrap:wrap;gap:12px;}}
.logo{{display:flex;align-items:center;gap:12px;}}
.lm{{width:38px;height:38px;background:linear-gradient(135deg,var(--a),var(--a3));border-radius:10px;display:grid;place-items:center;font-family:'Syne',sans-serif;font-weight:800;font-size:15px;color:#fff;box-shadow:0 0 16px rgba(124,106,247,0.4);}}
.lt{{font-family:'Syne',sans-serif;font-weight:800;font-size:17px;letter-spacing:3px;}}
.ls{{font-size:9px;letter-spacing:2px;color:var(--m);text-transform:uppercase;}}
.live{{display:flex;align-items:center;gap:6px;font-size:10px;letter-spacing:2px;color:var(--a3);}}
.dot{{width:6px;height:6px;border-radius:50%;background:var(--a3);animation:pulse 2s infinite;}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.2}}}}
.last-run{{font-size:10px;color:var(--m);}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:16px;}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;}}
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px;}}
@media(max-width:900px){{.grid3,.grid4{{grid-template-columns:1fr 1fr}}.grid2{{grid-template-columns:1fr}}}}
@media(max-width:500px){{.grid3,.grid4,.grid2{{grid-template-columns:1fr}}}}
.card{{background:var(--card);border:1px solid var(--b);border-radius:14px;padding:22px;}}
.card-title{{font-family:'Syne',sans-serif;font-size:11px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--m);margin-bottom:16px;display:flex;align-items:center;gap:8px;}}
.card-title::after{{content:'';flex:1;height:1px;background:var(--b);}}
.stat-val{{font-family:'Syne',sans-serif;font-size:32px;font-weight:800;line-height:1;}}
.stat-label{{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--m);margin-top:4px;}}
.stat-icon{{font-size:22px;margin-bottom:8px;}}
.score-wrap{{display:flex;align-items:center;gap:20px;}}
.score-ring{{position:relative;width:100px;height:100px;flex-shrink:0;}}
.score-ring svg{{transform:rotate(-90deg);}}
.score-center{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;}}
.score-num{{font-family:'Syne',sans-serif;font-size:24px;font-weight:800;}}
.score-denom{{font-size:10px;color:var(--m);}}
.score-info h3{{font-family:'Syne',sans-serif;font-size:16px;font-weight:700;margin-bottom:6px;}}
.score-info p{{font-size:11px;color:var(--m);line-height:1.6;}}
.roast-text{{font-size:12px;color:var(--m);line-height:1.8;font-style:italic;border-left:3px solid var(--a);padding-left:14px;}}
.fix-item{{font-size:11px;color:var(--m);padding:8px 0;border-bottom:1px solid var(--b);line-height:1.5;}}
.fix-item:last-child{{border-bottom:none;}}
.trend-item{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--b);}}
.trend-item:last-child{{border-bottom:none;}}
.trend-name{{font-size:11px;}}
.trend-stars{{font-size:10px;color:var(--a2);}}
.missing-box{{background:rgba(247,106,106,0.06);border:1px solid rgba(247,106,106,0.2);border-radius:8px;padding:10px 14px;font-size:11px;color:#f76a6a;margin-top:12px;}}
.q-item{{display:flex;gap:8px;font-size:11px;color:var(--m);padding:8px 0;border-bottom:1px solid var(--b);line-height:1.5;}}
.q-item:last-child{{border-bottom:none;}}
.q-num{{color:var(--a);font-weight:600;flex-shrink:0;}}
.mission-card{{background:linear-gradient(135deg,rgba(124,106,247,0.1),rgba(106,247,194,0.04));border:1px solid rgba(124,106,247,0.25);border-radius:14px;padding:22px;margin-bottom:16px;}}
.mission-title{{font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:var(--a);margin-bottom:6px;}}
.mission-desc{{font-size:12px;color:var(--m);line-height:1.7;margin-bottom:14px;}}
.tags{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;}}
.tag{{font-size:9px;letter-spacing:1px;padding:3px 10px;border-radius:20px;background:rgba(124,106,247,0.15);border:1px solid rgba(124,106,247,0.3);color:var(--a);}}
.step-item{{display:flex;gap:10px;font-size:11px;color:var(--m);padding:8px 0;border-bottom:1px solid var(--b);line-height:1.5;}}
.step-item:last-child{{border-bottom:none;}}
.step-num{{width:20px;height:20px;border-radius:50%;background:rgba(124,106,247,0.2);border:1px solid rgba(124,106,247,0.4);display:flex;align-items:center;justify-content:center;font-size:9px;color:var(--a);flex-shrink:0;font-weight:700;}}
.repo-btn{{display:inline-flex;align-items:center;gap:6px;padding:10px 18px;background:linear-gradient(135deg,var(--a),#9c8cf7);border-radius:8px;color:#fff;text-decoration:none;font-family:'Syne',sans-serif;font-weight:700;font-size:12px;letter-spacing:1px;margin-top:12px;transition:all 0.2s;}}
.repo-btn:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(124,106,247,0.4);}}
.repo-btn.disabled{{background:var(--b2);color:var(--m);pointer-events:none;}}
.weak-item{{font-size:10px;color:var(--m);padding:5px 0;border-bottom:1px solid var(--b);}}
.weak-item:last-child{{border-bottom:none;}}
footer{{text-align:center;padding:24px 0;font-size:10px;color:var(--m);letter-spacing:2px;border-top:1px solid var(--b);margin-top:8px;}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="logo">
    <div class="lm">A</div>
    <div><div class="lt">AXIOM</div><div class="ls">Live Intelligence Dashboard</div></div>
  </div>
  <div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap;">
    <div class="live"><div class="dot"></div>LIVE</div>
    <div class="last-run">Last run: {data['last_run']}</div>
  </div>
</header>

<!-- STATS ROW -->
<div class="grid4">
  <div class="card">
    <div class="stat-icon">📁</div>
    <div class="stat-val" style="color:var(--a)">{gh['repos']}</div>
    <div class="stat-label">Total Repos</div>
  </div>
  <div class="card">
    <div class="stat-icon">⭐</div>
    <div class="stat-val" style="color:var(--a2)">{gh['stars']}</div>
    <div class="stat-label">Stars Earned</div>
  </div>
  <div class="card">
    <div class="stat-icon">🔥</div>
    <div class="stat-val" style="color:var(--a3)">{gh['streak']}</div>
    <div class="stat-label">Active Days</div>
  </div>
  <div class="card">
    <div class="stat-icon">💻</div>
    <div class="stat-val" style="color:#6ab8f7;font-size:18px;margin-top:6px;">{langs}</div>
    <div class="stat-label">Stack</div>
  </div>
</div>

<!-- SCORE + ROAST -->
<div class="grid2">
  <div class="card">
    <div class="card-title">Profile Score</div>
    <div class="score-wrap">
      <div class="score-ring">
        <svg width="100" height="100" viewBox="0 0 100 100">
          <circle fill="none" stroke="var(--b2)" stroke-width="8" cx="50" cy="50" r="42"/>
          <circle fill="none" stroke="{score_color}" stroke-width="8" stroke-linecap="round"
            cx="50" cy="50" r="42"
            stroke-dasharray="{circumference:.0f}"
            stroke-dashoffset="{offset:.0f}"
            style="filter:drop-shadow(0 0 6px {score_color})"/>
        </svg>
        <div class="score-center">
          <div class="score-num" style="color:{score_color}">{score}</div>
          <div class="score-denom">/100</div>
        </div>
      </div>
      <div class="score-info">
        <h3>{score_emoji} @{gh['username']}</h3>
        <p>Profile analyzed by AXIOM Agent 1. Score based on README quality, language diversity, stars, and activity.</p>
        {weak_html}
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-title">Recruiter Roast 💀</div>
    <div class="roast-text">{data.get('roast','')[:280]}</div>
    <div style="margin-top:14px;">
      <div class="card-title">Quick Fixes</div>
      {fixes_html}
    </div>
  </div>
</div>

<!-- MISSION -->
<div class="mission-card">
  <div class="card-title">🎯 Today's Build Mission — Auto-Generated by AXIOM</div>
  <div class="mission-title">{mission['title']}</div>
  <div class="mission-desc">{mission['description']}</div>
  <div class="tags">
    {''.join(f'<span class="tag">{t}</span>' for t in mission.get('tech_stack',[])[:4])}
    <span class="tag">~{mission.get('hours',5)}hrs</span>
    <span class="tag">{mission.get('difficulty','beginner')}</span>
  </div>
  <div class="card-title">Starter Steps</div>
  {steps_html}
  <p style="font-size:11px;color:var(--a3);margin-top:12px;">💼 {mission.get('why','')}</p>
  {repo_btn}
</div>

<!-- TRENDING + INTERVIEW -->
<div class="grid3">
  <div class="card">
    <div class="card-title">📈 Trending in Stack</div>
    {trending_html}
    <div class="missing-box">⚠️ Missing: {missing_html}</div>
  </div>
  <div class="card" style="grid-column:span 2">
    <div class="card-title">🎤 Interview Prep</div>
    {questions_html}
  </div>
</div>

<footer>AXIOM 🧠 · Autonomous GitHub Intelligence · Runs daily 8AM · Made by @{gh['username']}</footer>
</div>
</body>
</html>"""

    def push_dashboard(self, data: dict) -> str:
        """Push the live dashboard HTML to GitHub repo."""
        html = self._build_html(data)
        encoded = base64.b64encode(html.encode("utf-8")).decode("utf-8")

        # Check if file exists (need SHA to update)
        sha = None
        try:
            r = requests.get(
                f"https://api.github.com/repos/{self.github_username}/{self.repo_name}/contents/docs/index.html",
                headers=self.headers,
                timeout=10
            )
            if r.status_code == 200:
                sha = r.json().get("sha")
        except Exception:
            pass

        payload = {
            "message": "🤖 AXIOM: Update live dashboard",
            "content": encoded,
        }
        if sha:
            payload["sha"] = sha

        try:
            r = requests.put(
                f"https://api.github.com/repos/{self.github_username}/{self.repo_name}/contents/docs/index.html",
                headers=self.headers,
                json=payload,
                timeout=15
            )
            if r.status_code in [200, 201]:
                dashboard_url = f"https://{self.github_username}.github.io/{self.repo_name}/"
                return dashboard_url
            else:
                print(f"   ⚠️ Dashboard push failed: {r.status_code}")
                return ""
        except Exception as e:
            print(f"   ⚠️ Dashboard push error: {e}")
            return ""

    def enable_github_pages(self) -> bool:
        """Enable GitHub Pages from the docs/ folder."""
        payload = {
            "source": {"branch": "master", "path": "/docs"}
        }
        try:
            r = requests.post(
                f"https://api.github.com/repos/{self.github_username}/{self.repo_name}/pages",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            return r.status_code in [200, 201, 409]
        except Exception:
            return False