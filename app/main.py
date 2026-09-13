from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
import os
from pydantic import BaseModel

from app.core.bot import bot_instance
from app.core.scheduler import start_scheduler

app = FastAPI(title="Tinkoff Trading Bot")

os.makedirs("app/static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Simple auth
class LoginRequest(BaseModel):
    password: str

WEB_PASSWORD = "admin"

@app.on_event("startup")
def startup_event():
    start_scheduler()
    bot_instance.start()

@app.get("/")
async def root(request: Request):
    # In a real app we'd use cookies/sessions, simplified for demo
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/api/login")
async def login(req: LoginRequest):
    if req.password == WEB_PASSWORD:
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail="Invalid password")

@app.get("/api/status")
async def get_status():
    return {
        "is_running": bot_instance.is_running,
        "last_scan_time": bot_instance.last_scan_time,
        "portfolio": bot_instance.portfolio_stats,
        "assets": bot_instance.selected_assets
    }

@app.post("/api/update_asset")
async def update_asset(data: dict):
    # data: {"ticker": "SBER", "active": true, "lot": 2}
    ticker = data.get("ticker")
    for asset in bot_instance.selected_assets:
        if asset["ticker"] == ticker:
            if "active" in data:
                asset["active"] = data["active"]
            if "lot" in data:
                asset["lot"] = data["lot"]
            return {"status": "updated", "asset": asset}
    raise HTTPException(status_code=404, detail="Asset not found")

@app.post("/api/toggle_bot")
async def toggle_bot():
    if bot_instance.is_running:
        bot_instance.stop()
    else:
        bot_instance.start()
    return {"is_running": bot_instance.is_running}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
