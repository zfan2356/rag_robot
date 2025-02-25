import json
from typing import Any, AsyncGenerator, Dict, Iterator

import aiohttp


async def process_stream_resp(
    model_name: str,
    payload: Dict[str, Any],
) -> AsyncGenerator[Dict[str, Any], None]:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/generate/{model_name}",
            json=payload,
        ) as resp:
            resp.raise_for_status()
            buffer = [""]
            all_chunk = b""
            async for chunk in resp.content.iter_chunked(4096):
                try:
                    all_chunk += chunk
                    buffer[0] += all_chunk.decode("utf-8")
                    all_chunk = b""
                except UnicodeDecodeError:
                    continue

                for json_str in get_json(buffer):
                    yield json_str


def get_json(buffer: list[str]) -> Iterator[Dict[str, Any]]:
    while "\n" in buffer[0]:
        line, buffer[0] = buffer[0].split("\n", 1)
        try:
            data = json.loads(line)
            yield data
        except json.decoder.JSONDecodeError as e:
            raise e
