<p align="center">
  <img src="https://img.shields.io/badge/Track_3-Sales_%26_Outreach-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Coherence_7.0-Hackathon-purple?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Team-Heavyweight-orange?style=for-the-badge" />
</p>

# ⚡ Synaptiq — AI-Powered Outreach Workflow Engine

> **Ship personalized, multi-channel outreach campaigns at scale — with an AI agent that drafts, sends, monitors, calls, and handles objections autonomously.**

Synaptiq is a full-stack outreach automation platform where users build a personal AI agent, import leads, design workflow DAGs, and launch campaigns that send personalized emails, detect replies, handle objections, trigger WhatsApp alerts, and even make AI phone calls — all from a single dashboard.

---

## 🎯 What It Does — End to End

```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│ Agent Setup  │───▸│ Lead Import   │───▸│ Copilot (NL→  │───▸│  Preflight   │
│ Persona +    │    │ CSV/XLSX +    │    │  workflow DAG) │    │ Spam Scorer  │
│ Ghost Voice  │    │ Auto-enrich   │    │               │    │ + AI Fix It  │
└─────────────┘    └──────────────┘    └───────────────┘    └──────────────┘
                                                                    │
        ┌───────────────────────────────────────────────────────────┘
        ▼
┌──────────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│   Launch     │───▸│  Live        │───▸│   ClawBot      │───▸│  Campaign    │
│  DAG Engine  │    │  Monitoring  │    │  WhatsApp +    │    │  Autopsy     │
│  + Shield    │    │  SSE Stream  │    │  AI Calls      │    │  Report      │
└──────────────┘    └──────────────┘    └───────────────┘    └──────────────┘
```

### 1️⃣ Agent Setup
- DiceBear avatar generation from name  
- 3 personality sliders (Aggression, Empathy, CTA) → live preview  
- Ghost Voice: upload sample emails → Gemini extracts writing fingerprint  

### 2️⃣ Lead Import
- Upload CSV/XLSX → auto-detect email column  
- 10 Indian companies with hardcoded insights (Razorpay, Zepto, CRED, etc.)  
- Tavily API for real-time research on unknown companies  

### 3️⃣ Campaign Copilot
- Type a campaign description in natural language  
- Gemini 2.5 Flash converts it into a workflow DAG  
- Drag & tweak nodes on the canvas  

### 4️⃣ Workflow Canvas (7 Node Types)
| Node | What It Does |
|------|-------------|
| **Trigger** | Entry point — starts the pipeline per lead |
| **Blocklist** | Competitor Shield — blocks Salesforce, HubSpot, Zoho, etc. |
| **AI Message** | Gemini generates personalized email using lead insight + persona |
| **Delay** | Gaussian jitter ±30min, IST working hours snap, daily ramp-up |
| **Send Email** | Gmail SMTP with tracking pixel |
| **Condition** | Branch on reply_received / no_reply |
| **ClawBot** | Pause, send WhatsApp alert, wait for human decision |

### 5️⃣ Preflight Engine
- 21-phrase spam blacklist, ALL-CAPS detection, link count, cadence gap  
- Returns LOW / MEDIUM / HIGH risk score  
- "Fix It" button → Gemini Flash-Lite rewrites content  

### 6️⃣ DAG Executor
- APScheduler runs async DAG per lead  
- Kahn's topological sort for execution order  
- Safety rate limits: 3/min, 20/hr, 150/day (production mode)  
- Every action logged to events table + SSE streamed  

### 7️⃣ Competitor Shield
- Blocklist fires before any email send  
- Blocks competitor domains (zoho, salesforce, hubspot, freshworks, pipedrive)  
- Monitoring page flashes RED when shield activates  

### 8️⃣ Live Monitoring Dashboard
- SSE real-time event streaming  
- 4 stat cards: Sent, ClawBot Alerts, Reply Rate, Booked Calls  
- Per-lead horizontal milestone pipeline  
- Execution log terminal with timestamps  

### 9️⃣ ClawBot (WhatsApp Command Center)
- Hot lead detection (3+ email opens)  
- WhatsApp alerts via Twilio with YES / SKIP / PAUSE / custom reply  
- Objection classifier (6 types via Groq Llama-3.1-8B)  
- Specialized response playbooks via Gemini  

### 📞 Agentic AI Calls (Bland.ai)
- Click "Call" on any lead → Bland.ai AI agent makes the call  
- Agent introduces itself, qualifies the lead, books a meeting  
- Gemini analyzes transcript → WhatsApp alert if meeting booked  

### 🔬 Campaign Autopsy
- End-of-campaign report with 8 metrics  
- Human hours saved calculation (emails × 0.06 hrs)  

---

## 🛠 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 16, TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI, SQLAlchemy (async), SQLite (WAL mode), APScheduler |
| **LLMs** | Gemini 2.0 Flash, Gemini Flash-Lite, Groq Llama-3.3-70B, Groq Llama-3.1-8B |
| **Voice** | Sarvam Saarika V2 (transcription), Sarvam-M (Hindi emails) |
| **Search** | Tavily API (lead research) |
| **Messaging** | Twilio WhatsApp Sandbox |
| **Calls** | Bland.ai (agentic AI phone calls) |
| **Email** | Gmail SMTP + tracking pixel |
| **Scheduling** | Cal.com webhooks + email-based booking detection |
| **Avatars** | DiceBear API |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- API keys: Gemini, Groq, Twilio, (optional: Tavily, Bland.ai, Sarvam)

### 1. Clone & Install

```bash
git clone https://github.com/sahilm029/COHERENCE-26_Heavyweight.git
cd COHERENCE-26_Heavyweight

# Frontend
npm install

# Backend
cd chronoreach-backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key

# Email (Gmail App Password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=your_app_password

# Twilio WhatsApp
TWILIO_SID=your_sid
TWILIO_AUTH=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
USER_PHONE=whatsapp:+91XXXXXXXXXX

# Optional
SARVAM_API_KEY=your_sarvam_key
TAVILY_API_KEY=your_tavily_key
BLAND_API_KEY=your_bland_key
NGROK_DOMAIN=your-domain.ngrok-free.app
CAL_URL=app.cal.com/yourname

# Demo
DEMO_MODE=true
```

### 3. Run

```bash
# Terminal 1 — Backend
cd chronoreach-backend
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
npm run dev
```

Open **http://localhost:3000** 🎉

---

## 📁 Project Structure

```
COHERENCE-26_Heavyweight/
├── app/                          # Next.js pages
│   ├── page.tsx                  # Landing page
│   ├── main/page.tsx             # Agent setup + lead import
│   ├── dashboard/page.tsx        # Workflow canvas + copilot
│   ├── monitoring/page.tsx       # Live monitoring dashboard
│   └── autopsy/page.tsx          # Campaign autopsy report
├── components/
│   ├── AgentSidebar.tsx          # Agent panel + navigation
│   └── ui/                      # shadcn/ui components
├── chronoreach-backend/
│   ├── main.py                   # FastAPI app + scheduler
│   ├── models.py                 # SQLAlchemy models (8 tables)
│   ├── database.py               # Async SQLite + WAL mode
│   ├── engine/
│   │   ├── executor.py           # DAG executor + EventBus
│   │   ├── safety.py             # Rate limiting (3/min, 20/hr, 150/day)
│   │   ├── timing.py             # Gaussian jitter + IST snap
│   │   └── email_sender.py       # Gmail SMTP + tracking pixel
│   ├── routers/                  # 13 API routers
│   │   ├── leads.py              # CSV/XLSX upload + confirm
│   │   ├── workflows.py          # CRUD for DAGs
│   │   ├── campaigns.py          # Launch + status + heatmap
│   │   ├── preflight.py          # Spam scoring + AI fix
│   │   ├── copilot.py            # NL → workflow + transcribe
│   │   ├── monitor.py            # SSE streaming
│   │   ├── clawbot.py            # WhatsApp webhook
│   │   ├── calls.py              # Bland.ai phone calls
│   │   ├── cal.py                # Cal.com booking
│   │   ├── track.py              # Email open tracking
│   │   ├── simulate.py           # Demo simulation endpoints
│   │   ├── persona.py            # Agent persona + ghost voice
│   │   └── autopsy.py            # Campaign metrics
│   └── services/                 # Business logic
│       ├── llm_service.py        # Gemini + Groq + Sarvam
│       ├── call_service.py       # Bland.ai call trigger
│       ├── clawbot_service.py    # WhatsApp message builder
│       ├── ghost_voice.py        # Writing fingerprint extractor
│       ├── research_service.py   # Tavily + hardcoded insights
│       ├── voice_service.py      # Sarvam transcription
│       ├── preflight_ai.py       # Spam scorer + fixer
│       ├── copilot_service.py    # Workflow template generator
│       ├── objection_handler.py  # 6-type objection classifier
│       ├── inbox_monitor.py      # Gmail IMAP reply poller
│       ├── whatsapp_poller.py    # Twilio message poller
│       └── coach_service.py      # Campaign performance coach
└── Agentic Call Feature/         # Original Bland.ai scripts
```

---

## 👥 Team Heavyweight

| Name | Role |
|------|------|
| **Sahil** | Full Stack + Backend |
| **Lakshya** | Full Stack + AI Integration |
| **Vipul** | Frontend + Design |

Built for **Coherence 7.0 Hackathon — Track 3: Sales & Outreach Systems** 🏆
