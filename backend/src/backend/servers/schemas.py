from pydantic import BaseModel, ConfigDict


class ServerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game: str
    name: str


class ServerList(BaseModel):
    items: list[ServerOut]
