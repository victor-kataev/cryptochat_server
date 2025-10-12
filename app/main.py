from datetime import datetime

from fastapi import FastAPI

from app.api.v1.api import api_router
from app.schemas.auth import UserLogin


app = FastAPI()

app.include_router(api_router)




@app.get("/")
async def read_root():
    return {"Hello": "World"}

