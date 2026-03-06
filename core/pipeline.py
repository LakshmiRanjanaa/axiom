"""
AXIOM Core Pipeline
Orchestrates all 6 agents in sequence and sends WhatsApp report + updates live dashboard.
"""

import os
from dotenv import load_dotenv
from agents.github_auditor import GitHubAuditor
from agents.roast_fixer import RoastFixer
from agents.trend_spotter import TrendSpotter
from agents.build_mission import BuildMissionAgent
from agents.whatsapp_sender import WhatsAppSender
from agents.mission_builder import MissionBuilder
from agents.dashboard_generator import DashboardGenerator

load_dotenv()

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

    # ── AGENT 4: Build Mission Agent ─────────────────────
    print("🎯 Agent 4: Build Mission Agent running...")
    mission_agent = BuildMissionAgent(anthropic_key)
    mission_data = mission_agent.run(github_data, trend_data, roast_data)
    print(f"   ✅ Mission: {mission_data['mission_title']}\n")

    # ── AGENT 5: WhatsApp Sender ─────────────────────────
    print("📲 Agent 5: WhatsApp Sender running...")
    sender = WhatsAppSender()
    sender.send(github_data, roast_data, trend_data, mission_data)
    print(f"   ✅ WhatsApp report sent!\n")

    # ── AGENT 6: Mission Builder ─────────────────────────
    print("🔨 Agent 6: Mission Builder running...")
    builder = MissionBuilder(anthropic_key, github_token, username)
    build_data = builder.run(github_data, roast_data, trend_data, mission_data)
    print(f"   ✅ {build_data['file_count']} files generated")
    if build_data['repo_info'].get('url'):
        print(f"   ✅ Mission repo: {build_data['repo_info']['url']}\n")

    # ── DASHBOARD: Push live dashboard ───────────────────
    print("📊 Dashboard: Updating live dashboard...")
    dashboard = DashboardGenerator(github_token, username, "axiom")
    dashboard.enable_github_pages()
    dashboard_url = dashboard.push_dashboard(build_data['dashboard_data'])
    if dashboard_url:
        print(f"   ✅ Dashboard live at: {dashboard_url}\n")
    else:
        print(f"   ⚠️ Dashboard push failed — enable GitHub Pages manually\n")

    print(f"{'='*50}")
    print(f"  ✅ AXIOM Pipeline Complete!")
    if dashboard_url:
        print(f"  🌐 Dashboard: {dashboard_url}")
    if build_data['repo_info'].get('url'):
        print(f"  📦 Mission Repo: {build_data['repo_info']['url']}")
    print(f"{'='*50}\n")
