from fastapi import FastAPI

from src.bot_app.routers import models, prompt
from src.bot_app.setting import settings

app = FastAPI(title=settings.PROJECT_NAME)

# 注册路由
app.include_router(models.router)
app.include_router(prompt.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
