from typing import Any, AsyncGenerator

data_access_factory: AsyncGenerator | None = None


async def get_data_access() -> Any:
    async for item in data_access_factory():
        yield item
