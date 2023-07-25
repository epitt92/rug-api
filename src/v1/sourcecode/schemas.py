from pydantic import BaseModel, HttpUrl
from typing import List

class SourceCodeFile(BaseModel):
    name: str
    sourceCode: str
    fileUrl: HttpUrl = None

class SourceCodeResponse(BaseModel):
    files: List[SourceCodeFile]
