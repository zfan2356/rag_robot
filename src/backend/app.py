from fastapi import FastAPI

from src.backend.routers import models
from src.backend.setting import settings

app = FastAPI(title=settings.PROJECT_NAME)

# 注册路由
app.include_router(models.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
