from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_checker import check_text

router = APIRouter()

class Article(BaseModel):
    text: str

@router.post("/analyze")
def analyze_article(article: Article):
    result = check_text(article.text)
    return {"result": result}