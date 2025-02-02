from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from ui.routes.analysis_router import router as analysis_router
from ui.routes.conversions_router import router as conversions_router
from ui.routes.unificator_router import router as unificator_router
from ui.routes.calculator_router import router as calculator_router
from ui.routes.dynamic_router import router as dynamic_router
import os
from db.database import init_db

init_db()

app = FastAPI()

app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")



@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



app.include_router(analysis_router)
app.include_router(conversions_router)
app.include_router(unificator_router)
app.include_router(calculator_router)
app.include_router(dynamic_router)