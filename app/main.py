from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.analyze import router

app = FastAPI()

# ✅ 正確 CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://ai-test.local",
        "https://ai-test.local",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)