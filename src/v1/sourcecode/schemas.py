from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class SourceCodeFile(BaseModel):
    name: str
    sourceCode: str
    fileUrl: HttpUrl = None

class SourceCodeResponse(BaseModel):
    files: Optional[List[SourceCodeFile]] = None
