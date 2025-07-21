from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.routers import router as api_router


app = FastAPI()

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
)


@app.get("/")
async def hello(data: str):
    return {"data": "Hello World!", "data2": data}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
