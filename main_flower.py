import asyncio
import uvicorn
from loguru import logger

from flowers.bot_app import app
from flowers.loader_flower import main


async def start_everything():
    asyncio.create_task(main())

    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    logger.info("Запуск бота")
    asyncio.run(start_everything())
