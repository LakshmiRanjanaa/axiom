"""
AXIOM — Autonomous GitHub Intelligence & Student Career Acceleration Agent
Run this file to trigger the full pipeline manually.
GitHub Actions runs it automatically every morning at 8AM.
"""

import asyncio
from core.pipeline import run_axiom_pipeline

if __name__ == "__main__":
    print("🧠 AXIOM Starting...")
    asyncio.run(run_axiom_pipeline())
