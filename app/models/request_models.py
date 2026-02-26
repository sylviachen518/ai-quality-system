from pydantic import BaseModel


class ArticleRequest(BaseModel):
    title: str
    content: str