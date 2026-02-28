from fastapi import APIRouter
from pydantic import BaseModel
from app.services.model_router import ModelRouter

router = APIRouter()
model_router = ModelRouter()

class AnalyzeRequest(BaseModel):
    text: str

@router.post("/analyze")
def analyze(request: AnalyzeRequest):
    result = model_router.analyze(request.text)

    return {
        "success": True,
        "data": result
    }