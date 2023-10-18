from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from service.service import QuestionService
from questions.schemas import CreateQuestion
from fastapi import Depends


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/test", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("login/login.html", {"request": request})


@app.post("/api/v1/questions/delete")
async def get_questions(request: Request, question_id: int, service: QuestionService = Depends(QuestionService)):
    return await service.delete_questions(question_id)


@app.post("/api/v1/questions/create")
async def get_questions(request: Request,  question_data: CreateQuestion, service: QuestionService = Depends(QuestionService)):
    return await service.create_questions(question_data)


@app.get("/api/v1/questions")
async def get_questions(request: Request, service: QuestionService = Depends(QuestionService)):
    return await service.get_all_questions()


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
