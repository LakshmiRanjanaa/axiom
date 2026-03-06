"""
AXIOM Core Pipeline — 8 Agents

Flow:
1. GitHub Auditor       — score your profile
2. Roast & Fix          — brutal feedback
3. Trend Spotter        — what's hot in your stack
4. WhatsApp Receiver    — answer any questions you sent overnight  ← NEW
5. Progress Tracker     — check if you committed to current mission ← NEW
6. Build Mission        — generate mission (only if needed)
7. Mission Builder      — create repo + starter code (only if needed)
8. Dashboard            — update live dashboard
9. WhatsApp Sender      — send daily brief with links
"""

import os
import json
from dotenv import load_dotenv
from agents.github_auditor import GitHubAuditor
from agents.roast_fixer import RoastFixer
from agents.trend_spotter import TrendSpotter
from agents.build_mission import BuildMissionAgent
from agents.whatsapp_sender import WhatsAppSender
from agents.whatsapp_receiver import WhatsAppReceiver
from agents.mission_builder import MissionBuilder
from agents.dashboard_generator import DashboardGenerator
from agents.progress_tracker import ProgressTracker

load_dotenv()

# File to persist current mission state between daily runs
STATE_FILE = "axiom_state.json"


def load_state() -> dict:
    """Load persisted mission state from last run."""
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"current_mission": None, "current_repo_url": "", "run_count": 0}


def save_state(state: dict):
    """Save mission state for next run."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"   ⚠️ Could not save state: {e}")


async def run_axiom_pipeline():
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    github_token  = os.getenv("GITHUB_TOKEN")
    username      = os.getenv("GITHUB_USERNAME")

    if not all([username, github_token, anthropic_key]):
        print("❌ Missing environment variables. Check your .env file.")
        return

    print(f"\n{'='*50}")
    print(f"  AXIOM Pipeline — @{username}")
    print(f"{'='*50}\n")

    # Load last run's mission state
    state = load_state()
    state["run_count"] = state.get("run_count", 0) + 1

    # ── AGENT 1: GitHub Auditor ──────────────────────────
    print("🔍 Agent 1: GitHub Auditor running...")
    auditor = GitHubAuditor(username, github_token)
    github_data = auditor.run()
    print(f"   ✅ Fetched {github_data['total_repos']} repos | Score: {github_data['profile_score']}/100\n")

    # ── AGENT 2: Roast & Fix Agent ───────────────────────
    print("💀 Agent 2: Roast & Fix Agent running...")
    roaster = RoastFixer(anthropic_key)
    roast_data = roaster.run(github_data)
    print(f"   ✅ Roast generated | {len(roast_data['fixes'])} fixes suggested\n")

    # ── AGENT 3: Trend Spotter ───────────────────────────
    print("📈 Agent 3: Trend Spotter running...")
    spotter = TrendSpotter(github_token, anthropic_key)
    trend_data = spotter.run(github_data['languages'])
    print(f"   ✅ Found {len(trend_data['trending'])} trending repos in your stack\n")

    # ── AGENT 8: WhatsApp Receiver ───────────────────────
    # Answer any questions you sent since yesterday BEFORE sending today's brief
    print("📥 Agent 8: WhatsApp Receiver running...")
    current_mission = state.get("current_mission") or {}
    receiver = WhatsAppReceiver(anthropic_key)
    recv_result = receiver.run(current_mission, github_data)
    if recv_result["questions_found"] > 0:
        print(f"   ✅ Answered {recv_result['answered']} question(s)\n")
    else:
        print(f"   📭 No questions to answer\n")

    # ── AGENT 7: Progress Tracker ────────────────────────
    print("📊 Agent 7: Progress Tracker running...")
    current_repo_url = state.get("current_repo_url", "")
    tracker = ProgressTracker(anthropic_key, github_token, username)
    progress = tracker.run(current_mission, current_repo_url)
    print(f"   Status: {progress['status']} | Commits: {progress['commit_count']}")

    need_new_mission = progress["assign_new_mission"] or not current_mission

    if progress["status"] == "not_started" and current_repo_url:
        print(f"   💬 Nudge queued: {progress['nudge_message'][:60]}...\n")
    elif progress["status"] == "completed":
        print(f"   🎉 Mission complete! Assigning new mission.\n")
    elif progress["status"] == "in_progress":
        print(f"   🔨 Mission in progress — continuing same mission.\n")
    else:
        print()

    # ── AGENT 4: Build Mission Agent (only if needed) ────
    if need_new_mission:
        print("🎯 Agent 4: Build Mission Agent running...")
        mission_agent = BuildMissionAgent(anthropic_key)
        mission_data = mission_agent.run(github_data, trend_data, roast_data)
        print(f"   ✅ Mission: {mission_data['mission_title']}\n")
    else:
        mission_data = current_mission
        print(f"🎯 Agent 4: Skipped — continuing mission: {mission_data.get('mission_title', '')}\n")

    # ── AGENT 6: Mission Builder (only if new mission) ───
    if need_new_mission:
        print("🔨 Agent 6: Mission Builder running...")
        builder = MissionBuilder(anthropic_key, github_token, username)
        build_data = builder.run(github_data, roast_data, trend_data, mission_data)
        print(f"   ✅ {build_data['file_count']} files generated")
        repo_url = build_data['repo_info'].get('url', '')
        if repo_url:
            print(f"   ✅ Mission repo: {repo_url}\n")

        # Save new mission to state
        state["current_mission"] = mission_data
        state["current_repo_url"] = repo_url
    else:
        repo_url = current_repo_url
        build_data = {
            "file_count": 0,
            "repo_info": {"url": repo_url},
            "dashboard_data": _make_dashboard_data(
                github_data, roast_data, trend_data, mission_data,
                {"url": repo_url}, progress
            )
        }
        print(f"🔨 Agent 6: Skipped — repo already exists at {repo_url}\n")

    # ── DASHBOARD: Push live dashboard ───────────────────
    print("📊 Dashboard: Updating live dashboard...")
    dashboard = DashboardGenerator(github_token, username, "axiom")
    dashboard.enable_github_pages()
    dashboard_url = dashboard.push_dashboard(build_data['dashboard_data'])
    if dashboard_url:
        print(f"   ✅ Dashboard live at: {dashboard_url}\n")
    else:
        dashboard_url = f"https://{username}.github.io/axiom/"
        print(f"   ⚠️ Dashboard push failed — enable GitHub Pages manually\n")

    # ── AGENT 5: WhatsApp Sender ──────────────────────────
    print("📲 Agent 5: WhatsApp Sender running...")
    sender = WhatsAppSender()

    # Pass progress info into mission_data so sender can include it
    mission_data_with_progress = {
        **mission_data,
        "_progress_status": progress["status"],
        "_progress_commits": progress["commit_count"],
        "_nudge": progress.get("nudge_message", ""),
        "_is_new_mission": need_new_mission
    }

    sender.send(
        github_data,
        roast_data,
        trend_data,
        mission_data_with_progress,
        dashboard_url=dashboard_url,
        repo_url=repo_url
    )
    print(f"   ✅ WhatsApp report sent!\n")

    # Save state for next run
    save_state(state)

    print(f"{'='*50}")
    print(f"  ✅ AXIOM Pipeline Complete!")
    print(f"  🌐 Dashboard: {dashboard_url}")
    print(f"  📦 Mission Repo: {repo_url}")
    print(f"  📊 Mission Status: {progress['status']} ({progress['commit_count']} commits)")
    print(f"{'='*50}\n")


def _make_dashboard_data(github_data, roast_data, trend_data, mission_data, repo_info, progress):
    """Build dashboard data when mission builder is skipped."""
    from datetime import datetime
    return {
        "last_run": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "github": {
            "username": github_data["username"],
            "score": github_data["profile_score"],
            "repos": github_data["total_repos"],
            "stars": github_data["total_stars"],
            "streak": github_data["commit_streak_days"],
            "languages": github_data["languages"],
            "weak_spots": github_data["weak_spots"][:2]
        },
        "roast": roast_data.get("roast", "")[:300],
        "fixes": roast_data.get("fixes", [])[:3],
        "interview_questions": roast_data.get("interview_questions", []),
        "trending": trend_data.get("trending", [])[:3],
        "missing_skills": trend_data.get("missing_skills", []),
        "market_insight": trend_data.get("market_insight", ""),
        "mission": {
            "title": mission_data.get("mission_title", ""),
            "description": mission_data.get("mission_description", ""),
            "tech_stack": mission_data.get("tech_stack", []),
            "difficulty": mission_data.get("difficulty", "beginner"),
            "hours": mission_data.get("estimated_hours", 5),
            "why": mission_data.get("why_hireable", ""),
            "steps": mission_data.get("starter_steps", [])
        },
        "repo": repo_info,
        "progress": {
            "status": progress["status"],
            "commits": progress["commit_count"]
        }
    }
