from pydantic import BaseModel
from typing import List

class AIComment(BaseModel):
    commentType: str = None
    title: str = None
    description: str = None
    code: str = None
