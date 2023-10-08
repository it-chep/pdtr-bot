from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/test", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("login/login.html", {"request": request})


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
