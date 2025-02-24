from pydantic import BaseModel


class ModelResponse(BaseModel):
    name: str
    id: str
    size: str
