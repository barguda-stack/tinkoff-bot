from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, FileResponse
from contextlib import asynccontextmanager
import os
from pydantic import BaseModel

from app.core.bot import bot_instance
from app.core.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    bot_instance.start()
    print("\n" + "="*50)
    print("🚀 WEB INTERFACE IS RUNNING AT: http://127.0.0.1:8000 🚀")
    print("="*50 + "\n")
    yield

app = FastAPI(title="Tinkoff Trading Bot", lifespan=lifespan)

os.makedirs("app/static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

class LoginRequest(BaseModel):
    password: str

WEB_PASSWORD = "admin"

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("app/static/favicon.ico")

@app.get("/")
async def root(request: Request):
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
    ticker = data.get("ticker")
    for asset in bot_instance.selected_assets:
        if asset["ticker"] == ticker:
            if "active" in data:
                if data["active"] and asset.get("status") != "READY":
                    raise HTTPException(status_code=400, detail="Cannot activate asset before backtesting is READY")
                asset["active"] = data["active"]
            if "max_lots" in data:
                asset["max_lots"] = data["max_lots"]
            if "max_trades" in data:
                asset["max_trades"] = data["max_trades"]
            return {"status": "updated", "asset": asset}
    raise HTTPException(status_code=404, detail="Asset not found")

@app.post("/api/toggle_bot")
async def toggle_bot():
    if bot_instance.is_running:
        bot_instance.stop()
    else:
        bot_instance.start()
    return {"is_running": bot_instance.is_running}

@app.post("/api/update")
async def update_bot():
    import subprocess
    import os
    try:
        if os.name == 'nt':
            # Run the update script in a new detached cmd window so the current process can be killed
            subprocess.Popen('start "" update.bat', shell=True)
            return {"status": "ok", "message": "Update started! The bot will now restart automatically. Please wait 10-15 seconds and refresh the page."}
        else:
            subprocess.check_call(["git", "fetch", "origin"])
            subprocess.check_call(["git", "reset", "--hard", "origin/master"])
            return {"status": "ok", "message": "Update downloaded successfully. Please restart manually."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
