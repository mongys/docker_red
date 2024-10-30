from fastapi import FastAPI
from src.interfaces.api import router as api_router
from config.config import settings

app = FastAPI()

app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
