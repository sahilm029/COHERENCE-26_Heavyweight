import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import database

import asyncio

scheduler = AsyncIOScheduler(timezone=os.getenv("TZ", "Asia/Kolkata"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB (creates WAL mode + tables)
    await database.init_db()
    # Start the scheduler
    scheduler.start()
    # Start Gmail inbox monitor (reply detection)
    from services.inbox_monitor import inbox_monitor_loop
    monitor_task = asyncio.create_task(inbox_monitor_loop())
    # Start WhatsApp reply poller (replaces webhook dependency)
    from services.whatsapp_poller import whatsapp_poller_loop
    wa_poller_task = asyncio.create_task(whatsapp_poller_loop())
    yield
    # Shutdown
    monitor_task.cancel()
    wa_poller_task.cancel()
    scheduler.shutdown()

app = FastAPI(title="ChronoReach API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import leads, workflows, campaigns, preflight, copilot, monitor, clawbot, cal, persona, autopsy, track, simulate, calls

app.include_router(leads.router)
app.include_router(workflows.router)
app.include_router(campaigns.router)
app.include_router(preflight.router)
app.include_router(copilot.router)
app.include_router(monitor.router)
app.include_router(clawbot.router)
app.include_router(cal.router)
app.include_router(persona.router)
app.include_router(autopsy.router)
app.include_router(track.router)
app.include_router(simulate.router)
app.include_router(calls.router)

@app.get("/")
def read_root():
    return {"status": "ChronoReach API is running"}
