# 🧠 AXIOM — Autonomous GitHub Intelligence & Career Acceleration Agent

> *Makes you findable, not just hireable.*

AXIOM is a fully autonomous multi-agent AI system that runs every morning, audits your real GitHub profile, detects your skill gaps vs the market, roasts what's weak, gives you a daily build mission, and sends a full career coaching report to your WhatsApp — automatically, every day, without you touching anything.

---

## 🤖 The 5 Agents

| Agent | What It Does |
|---|---|
| 🔍 GitHub Auditor | Fetches all your repos, scores your profile 0-100 like a recruiter |
| 💀 Roast & Fix Agent | Brutally critiques your profile + auto-generates a README for your worst repo |
| 📈 Trend Spotter | Finds trending GitHub repos in your stack + detects missing skills |
| 🎯 Build Mission Agent | Gives you 1 specific project to build today to fill your biggest gap |
| 📲 WhatsApp Sender | Sends your full daily brief to WhatsApp automatically |

---

## ⚡ Setup in 4 Steps (Total: ~45 minutes)

### Step 1 — Get Your API Keys (20 min)

You need 4 free accounts:

**A) Anthropic (Claude AI)**
1. Go to https://console.anthropic.com
2. Sign up → Click "API Keys" → "Create Key"
3. Copy the key starting with `sk-ant-...`

**B) GitHub Token**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name it "AXIOM", set expiry to 90 days
4. Check these scopes: `repo`, `read:user`
5. Click Generate → Copy the token

**C) Twilio WhatsApp (Free Sandbox)**
1. Go to https://www.twilio.com → Sign up free
2. Go to Messaging → Try it out → Send a WhatsApp message
3. Follow the sandbox setup (send a WhatsApp message to their number with a code)
4. Copy: Account SID, Auth Token (from Console Dashboard)
5. From number is always: `whatsapp:+14155238886`

**D) Your WhatsApp Number**
- Format: `whatsapp:+91XXXXXXXXXX` (with your country code)

---

### Step 2 — Set Up the Project (10 min)

```bash
# Clone or download this project
cd AXIOM

# Install dependencies
pip install -r requirements.txt

# Set up your environment file
cp .env.example .env
```

Now open `.env` in any text editor and fill in all 6 values:

```
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
GITHUB_USERNAME=yourusername
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
YOUR_WHATSAPP_NUMBER=whatsapp:+91XXXXXXXXXX
```

---

### Step 3 — Run It Manually (5 min)

```bash
python main.py
```

You'll see all 5 agents running in your terminal.
A WhatsApp message will arrive on your phone in ~60 seconds.

**If WhatsApp doesn't arrive:**
- Check your Twilio sandbox is active (you need to send the join message first)
- Check your phone number format (must include country code)
- Check terminal for error messages

---

### Step 4 — Make It Run Automatically Every Day (15 min)

AXIOM uses **GitHub Actions** (free) to run itself daily at 8AM.

1. Push this project to a new GitHub repo:
```bash
git init
git add .
git commit -m "AXIOM initial setup"
git remote add origin https://github.com/YOURUSERNAME/axiom.git
git push -u origin main
```

2. Add your secrets to GitHub:
   - Go to your repo → Settings → Secrets and variables → Actions
   - Click "New repository secret" for each of these:

| Secret Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic key |
| `AXIOM_GITHUB_TOKEN` | Your GitHub token |
| `GITHUB_USERNAME` | Your GitHub username |
| `TWILIO_ACCOUNT_SID` | Your Twilio SID |
| `TWILIO_AUTH_TOKEN` | Your Twilio token |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+14155238886` |
| `YOUR_WHATSAPP_NUMBER` | `whatsapp:+91XXXXXXXXXX` |

3. Go to Actions tab → Enable workflows

**That's it. AXIOM now runs every morning at 8AM IST automatically.**

To change the time, edit `.github/workflows/daily.yml` — change the cron value.
- `30 2 * * *` = 8:00 AM IST (2:30 AM UTC)
- `30 1 * * *` = 7:00 AM IST
- `0 4 * * *` = 9:30 AM IST

---

## 📁 Project Structure

```
AXIOM/
├── main.py                          ← Run this to start everything
├── requirements.txt                 ← Python dependencies
├── .env.example                     ← Copy to .env and fill in keys
├── .gitignore                       ← Keeps your .env safe
├── core/
│   └── pipeline.py                  ← Orchestrates all 5 agents
├── agents/
│   ├── github_auditor.py            ← Agent 1: GitHub profile fetcher & scorer
│   ├── roast_fixer.py               ← Agent 2: Roast + auto README generator
│   ├── trend_spotter.py             ← Agent 3: Trending repos + skill gap finder
│   ├── build_mission.py             ← Agent 4: Daily build mission generator
│   └── whatsapp_sender.py           ← Agent 5: WhatsApp report formatter & sender
└── .github/
    └── workflows/
        └── daily.yml                ← GitHub Actions: runs AXIOM daily at 8AM
```

---

## 🛠️ Tech Stack

| Tool | Purpose | Cost |
|---|---|---|
| Python 3.11 | Core language | Free |
| Anthropic Claude | AI brain of all agents | Pay per use (~₹2/run) |
| GitHub REST API | Fetch real profile data | Free |
| Twilio WhatsApp | Send daily messages | Free sandbox |
| GitHub Actions | Daily autonomous scheduling | Free (2000 min/month) |

**Total running cost: ~₹2 per day** (just the Claude API calls)

---

## 🔬 Research Use

AXIOM is built for students + researchers. To study its impact:

- Check terminal logs after each run — all agent outputs are printed
- Modify agent prompts in each `agents/*.py` file to change behavior
- Add a `results.json` export by modifying `core/pipeline.py`

**Research hypothesis:** Does daily autonomous skill-gap feedback improve GitHub profile quality and job placement rates vs. students without it?

---

Built with Claude AI by Anthropic 🧠
