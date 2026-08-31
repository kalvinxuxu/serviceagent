from typing import Protocol, TypeVar

from pydantic import BaseModel

from ..agent.state import Message

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMProvider(Protocol):
    async def structured_generate(
        self,
        *,
        messages: list[Message],
        output_schema: type[SchemaT],
        temperature: float = 0,
    ) -> SchemaT:
        ...
