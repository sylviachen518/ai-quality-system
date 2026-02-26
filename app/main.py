from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analyze   # 根據你的實際 import 路徑調整

app = FastAPI()

# ✅ 加在這裡（app 建立之後）

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 再 include router
app.include_router(analyze.router)